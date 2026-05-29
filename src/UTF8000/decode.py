from typing import Generator

from .UTF8000Byte import (
    UTF8000Byte,
    byte_is_continuation, idx_start_seq_0, n_start_seq_ones,
    N_BITS_FIRST_BYTE, N_BITS_CONTINUATION_BYTE,
    OVERLONG_MASK_2_BYTE, OVERLONG_MASKS_N_BYTE
)
from .UTF8000Int import UTF8000Int

class UTF8000IncrementalDecoder:
    def __init__(self) -> None:
        self._results:      list[UTF8000Int] = []
        self._bytes_buffer: bytes            = b""

        self._generator = self._utf_8000_parse_forever()
        self._wakeup()

    def __iter__(self) -> Generator[UTF8000Int, None, None]:
        # queue
        while self._results:
            yield self._results.pop(0)

    def feed(self, utf_8000_bytes: bytes) -> None:
        self._bytes_buffer += utf_8000_bytes
        self._wakeup()

    def close(self) -> None:
        """
        Close the parser.

        Raises EOFError if we are part way through parsing a UTF-8000 sequence.

        Otherwise returns `None`.
        """
        self._generator.close()

    def _wakeup(self) -> None:
        self._generator.send(None)

    def _await_should_parse_again(self) -> Generator[None, None, None]:
        while not self._bytes_buffer:
            yield

    def _await_bytes(self, n_bytes: int) -> Generator[None, None, bytes]:
        while len(self._bytes_buffer) < n_bytes:
            yield

        ret                = self._bytes_buffer[:n_bytes]
        self._bytes_buffer = self._bytes_buffer[n_bytes:]

        return ret

    def _await_byte(self) -> Generator[None, None, int]:
        return (yield from self._await_bytes(1))[0]

    def _await_continuation_byte(self) -> Generator[None, None, int]:
        ret = yield from self._await_byte()
        if not byte_is_continuation(ret):
            self._unpop_byte(ret)
            self._on_error_invalid_continuation_byte()
        return ret

    def _unpop_bytes(self, b: bytes) -> None:
        self._bytes_buffer = b + self._bytes_buffer

    def _unpop_byte(self, c: int) -> None:
        self._unpop_bytes(bytes((c,)))

    def _on_error(self, error_message: str) -> UTF8000Byte:
        raise ValueError(error_message)

    def _on_error_invalid_start_byte(self) -> None:
        # XXX TODO 101: read all following continuation bytes to skip them
        self._on_error("Invalid start byte: continuation byte detected")

    def _on_error_invalid_continuation_byte(self) -> None:
        # XXX TODO 101: should we create / raise a ReplacementCharacterException?
        #               thus should we be calling return on the `_on_error`
        #               functions instead of just calling them?
        self._on_error("Not a continuation byte prefix")

    def _on_error_overlong(self) -> None:
        # XXX TODO 101: read all following continuation bytes to skip them
        self._on_error("Overlong encoding")

    def _utf_8000_parse_single(self) -> Generator[None, None, UTF8000Int]:
        parsed_bytes: list[UTF8000Byte] = []

        start_byte = yield from self._await_byte()

        # Find the position of the highest 0 in the 8 bits of the byte.
        # This zero allows us to tell how many bytes of UTF-8(000) we
        # are expecting.
        idx_0 = idx_start_seq_0(start_byte, N_BITS_FIRST_BYTE)

        if idx_0 == 7:
            #
            # Treat ASCII as a special case.
            # This makes it easier for us to write the decoder, and allows a 'fast path'.
            # ASCII has no (need for) overlong checking, and by returning early
            # before the overlong checking code we skip code that checks for multiple
            # start bytes, and further continuation bytes.
            #
            parsed_bytes.append(UTF8000Byte.ASCII(start_byte))

            return UTF8000Int(parsed_bytes)

        if idx_0 == 6:
            #
            # We have received a continuation byte when we were expecting a start byte.
            # This is an error.
            #
            return self._on_error_invalid_start_byte()

        if idx_0 == 5:
            #
            # Treat two byte UTF-8 as a special case.
            #
            # Two byte UTF-8 has only 4 mandatory content bits to check
            # against overlong encoding, unlike all other UTF-8000 sequences that
            # have 5 to check. This is because the jump from ASCII to UTF-8 means
            # we jump from 7 bits of content to 11, a gain of 4 bits of content,
            # whereas with every next additional continuation byte jumping from
            # k-byte UTF-8(000) to k+1-byte UTF-8(000) we gain 5 bits
            # of content; +6 bits from the continuation byte, -1 from extending
            # the start sequence bits by 1.
            #
            # Two byte UTF-8 has all 4 mandatory content bits in one byte,
            # the start byte, unlike all other UTF-8000 sequences
            # which may have them straddled across two bytes.
            #
            # Fun fact: It is for this reason why you will never see the bytes
            #           0xC0 or 0xC1 in a valid UTF-8(000) stream, like anywhere!
            #
            if not start_byte & OVERLONG_MASK_2_BYTE:
                self._on_error_overlong()

            parsed_bytes.append(UTF8000Byte.TwoByteStartByte(start_byte))

            first_non_start_byte = yield from self._await_continuation_byte()

            # No overlong checking needed for the second byte of two byte UTF-8.
            # We choose to fetch the continuation byte here instead of dropping
            # through to the end of the function for two reasons:
            #
            # Firstly this is a `ContinuationNonStartByteFirst`
            # not a `ContinuationNonStartByteNotFirst`
            #
            # Secondly by returning earlier we remove a layer of indentation
            # for the 'main' UTF-8000 case, making it more readable.
            #
            parsed_bytes.append(UTF8000Byte.ContinuationNonStartByteFirst(
                first_non_start_byte,
                n_bits_content_mandatory = 0
            ))

            return UTF8000Int(parsed_bytes)

        # The number of 1 bits in the start sequence is the number
        # (at least so far) of UTF-8000 bytes that we are expecting.
        n_bytes_expected = n_start_seq_ones(idx_0, N_BITS_FIRST_BYTE)

        if idx_0 != -1:
            #
            # The terminating 0 bit of the start sequence bits
            # was found in the first byte.
            # Thus this is the first and final start byte.
            #
            is_final_start_byte_a_continuation_byte = False
        else:
            #
            # The terminating 0 bit of the start sequence bits
            # !was not! found in the first byte.
            # This means that the byte is 0b11111111.
            # This means that we are expecting *at least* 8 bytes of UTF-8000.
            # We continue reading into the continuation bytes to find the
            # terminating 0 bit.
            # Thus this is the first but not the final start byte.
            #
            is_final_start_byte_a_continuation_byte = True

            parsed_bytes.append(UTF8000Byte.OnesFilledFirstStartByte())

            # Multiple start bytes: the power of UTF-8000!
            while True:
                start_byte = yield from self._await_continuation_byte()

                # Find the position of the highest 0 in the lowest 6 bits of the byte, aka
                # find the position of the highest 0 in the 6 bits that a
                # continuation byte contains. This zero allows us to tell
                # how many further continuation start bytes of UTF-8000
                # we are expecting.
                idx_0 = idx_start_seq_0(start_byte, N_BITS_CONTINUATION_BYTE)

                # The number of 1 bits in the start sequence is the number
                # of additional UTF-8000 bytes that we are expecting.
                n_bytes_expected += n_start_seq_ones(idx_0, N_BITS_CONTINUATION_BYTE)

                if idx_0 != -1:
                    #
                    # The terminating 0 bit of the start sequence bits
                    # was found in the continuation byte.
                    # Thus this is the final start byte.
                    #
                    break
                else:
                    #
                    # The terminating 0 bit of the start sequence bits
                    # !was not! found in the continuation byte.
                    # This means that the byte is 0b10111111.
                    # We continue reading into the continuation bytes
                    # to find the terminating 0 bit.
                    #
                    # XXX We may wish to set a reasonable limit, say 256
                    # bits in practice to prevent DOS attacks, even though
                    # UTF-8000 is unlimited.
                    #
                    parsed_bytes.append(UTF8000Byte.OnesFilledContinuationStartByte())

        final_start_byte_n_bits_content = idx_0
        first_non_start_byte_n_bits_content_mandatory = 5 - final_start_byte_n_bits_content

        # Perform checking against overlong encoding.
        # We forbid overlong encoding for two main reasons in my opinion:
        #
        # 1: Security.
        #    To make sure 0b11100000 0b10000000 0b10000000 0b10000000
        #    can't be decoded as codepoint 0, the null 'byte', which speciously
        #    may lead to people carelessly passing such bytes to `strcpy(3)`
        #    and friends, which at best leads to segfaults...
        #
        # 2: Uniqueness of encoding.
        #    Every codepoint has one unique valid representation as UTF-8000 bytes.
        #
        # At this point `start_byte` is the final start byte.
        #
        mask_start, mask_non_start = OVERLONG_MASKS_N_BYTE[final_start_byte_n_bits_content]

        if idx_0 == 5:
            # All of the mandatory content bits are
            # contained together in the <<final start byte<<.
            #
            # We check for overlong encoding in only the final start byte immediately.
            # We do not need to check the first non-start byte,
            # nor do we wait for it before performing overlong checking.
            #
            # It seems better computationally streamlined / CPU predictable /
            # deterministic to check `if idx_0 == 5`
            # than to check `if not mask_non_start`,
            # albeit the latter is more idiomatic.
            #
            # Examples:
            # UTF-8           Only possible for 2 byte UTF-8
            # UTF-8000    ... 0b100IIIII (0b10yyyyyy ...)
            #
            if not start_byte & mask_start:
                self._on_error_overlong()

            # Now we can wait for the first non-start byte,
            # and we do not need to check it.
            first_non_start_byte = yield from self._await_continuation_byte()
        else:
            # We wait for the first non-start byte, with which we
            # check for overlong encoding.
            first_non_start_byte = yield from self._await_continuation_byte()

            if idx_0 == 0:
                # All of the mandatory content bits are
                # contained together in the >>first non-start byte>>.
                #
                # We do not need to check the final start byte.
                # We check for overlong encoding in only the first non-start byte.
                #
                # It seems better computationally streamlined / CPU predictable /
                # deterministic to check `if idx_0 == 0`
                # than to check `if not mask_start`,
                # albeit the latter is more idiomatic.
                #
                # Examples:
                #
                # UTF-8           Not possible for UTF-8
                # UTF-8000        0b11111110 (0b10IIIIIy 0b10yyyyyy ...)
                # UTF-8000    ... 0b10111110 (0b10IIIIIy 0b10yyyyyy ...)
                #
                if not first_non_start_byte & mask_non_start:
                    self._on_error_overlong()
            else:
                # The mandatory content bits are
                # straddled across two bytes,
                # starting in the final start byte and continuing into
                # the first non-start byte.
                #
                # We employ both masks.
                #
                # Examples:
                #
                # UTF-8           0b11110QII (0b10IIyyyy 0b10yyyyyy 0b10yyyyyy)
                # UTF-8000    ... 0b10110III (0b10IIyyyy 0b10yyyyyy ...)
                # UTF-8000    ... 0b10110III (0b10QQyyyy 0b10yyyyyy ...)
                # UTF-8000    ... 0b10110QQQ (0b10IIyyyy 0b10yyyyyy ...)
                #
                if not (start_byte & mask_start | first_non_start_byte & mask_non_start):
                    self._on_error_overlong()

        parsed_bytes.append(UTF8000Byte(
            start_byte,
            is_continuation_byte     = is_final_start_byte_a_continuation_byte,
            is_start_byte            = True,
            n_bits_content_total     = final_start_byte_n_bits_content,
            n_bits_content_mandatory = final_start_byte_n_bits_content
        ))

        parsed_bytes.append(UTF8000Byte.ContinuationNonStartByteFirst(
            first_non_start_byte,
            n_bits_content_mandatory = first_non_start_byte_n_bits_content_mandatory
        ))

        while len(parsed_bytes) < n_bytes_expected:
            # Add the rest of the purely-content continuation bytes,
            # which have no mandatory content.
            continuation_byte = yield from self._await_continuation_byte()
            parsed_bytes.append(UTF8000Byte.ContinuationNonStartByteNotFirst(
                continuation_byte
            ))

        return UTF8000Int(parsed_bytes)

    def _utf_8000_parse_forever(self) -> Generator[None, None, None]:
        while True:
            try:
                yield from self._await_should_parse_again()
                # Park the generator in this 'parking lot' so that
                # if `close()` is called on the generator at this point
                # it's not an error, whereas if we are in the middle of
                # parsing a UTF-8000 sequence below that *should* be an
                # EOFError if `close()` is called early.
            except GeneratorExit:
                return
            try:
                x = yield from self._utf_8000_parse_single()
            except GeneratorExit as e:
                raise EOFError("Partially decoded UTF-8000 sequence didn't finish") from e
            else:
                self._results.append(x)
