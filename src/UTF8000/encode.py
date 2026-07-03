from .UTF8000Byte import (
    MULTIBYTE_SELF_SYNC_BITS_FIRST,
    MULTIBYTE_SELF_SYNC_BITS_CONTINUATION,
    MULTIBYTE_PROGRAMMABLE_N_BITS,
    MULTIBYTE_PROGRAMMABLE_MASK,
    MULTIBYTE_SELF_PUNCTUATION_ONES_FULL,
    MULTIBYTE_SELF_PUNCTUATION_ONES_SOME,
    ceil_div
)

def encode(x: int) -> bytes:
    """
    Encode an integer `x` into UTF-8000 bytes.
    """

    if x < 0:
        raise ValueError("Cannot encode negative number")

    ret_ints: list[int] = []

    if x < 0x80:
        # Treat ASCII as a special case.
        # Its self-synchronization prefix of '0' in the highest bit
        # is already present, so nothing more needs to be done.
        ret_ints.insert(0, x)
    else:
        n_bits_content_occupied: int = 0
        y: int = x

        # Extract sextets from `x`, the 6 least-significant bits at a time,
        # until there's 1 to 6 bits left. We walk backwards through
        # `ret_ints`, building it up from right-to-left,
        # least-significant bits to most-significant bits.
        # These sextets will fit nicely into continuation bytes, and they
        # contribute 6 towards the content bit count `n_bits_content_occupied`.
        while y > MULTIBYTE_PROGRAMMABLE_MASK:
            final_6_bits = y & MULTIBYTE_PROGRAMMABLE_MASK
            ret_ints.insert(0, final_6_bits)
            n_bits_content_occupied += MULTIBYTE_PROGRAMMABLE_N_BITS
            y >>= MULTIBYTE_PROGRAMMABLE_N_BITS

        # Add the final bits, the most-significant bits, to `ret_ints`.
        # Count exactly how much they contribute towards the content bit count.
        final_6_bits = y
        ret_ints.insert(0, final_6_bits)
        while y > 0:
            n_bits_content_occupied += 1
            y >>= 1

        # Calculate how many bytes our UTF-8000 code unit requires.
        # An `n`-byte code unit has capacity for `5n+1` content bits.
        # Therefore `ceil((n_bits_content_occupied-1) / 5)` gives us `n`,
        # which is sufficient and minimal for our content bit count.
        # Any larger code unit size would lead to an overlong encoding!
        n_utf_8000_bytes_needed = ceil_div(n_bits_content_occupied - 1, 5)

        # Left pad the array of content hextets with empty bytes,
        # to the size `n_utf_8000_bytes_needed`.
        # This array is then ready for its bytes to be
        # empowered with start bits to provide self-punctuation, and
        # crowned with prefixes to provide self-synchronization,
        # which delivers us from content bit hextets to UTF-8000 octets.
        ret_ints = [0 for _ in range(n_utf_8000_bytes_needed - len(ret_ints))] + ret_ints

        ### Add the self-punctuation start bits:
        idx_self_punctuation = 0

        # Calculate how many full sextets of '1' start bits there are,
        # and how many '1' start bits there are in the final start byte.
        # The final start byte will contain 0 to 5 '1' bits,
        # meaning that the terminating '0' start bit will also fit inside.
        n_start_bytes_filled_with_ones, n_ones_in_final_start_byte = divmod(n_utf_8000_bytes_needed - 2, MULTIBYTE_PROGRAMMABLE_N_BITS)

        # Add the start byte sextets full of '1' bits.
        while idx_self_punctuation < n_start_bytes_filled_with_ones:
            ret_ints[idx_self_punctuation] |= MULTIBYTE_SELF_PUNCTUATION_ONES_FULL
            idx_self_punctuation += 1

        # Add the final start bits '[...111]0'.
        ret_ints[idx_self_punctuation] |= MULTIBYTE_SELF_PUNCTUATION_ONES_SOME[n_ones_in_final_start_byte]

        ### Add the self-synchronization prefixes:
        idx_self_sync = 0

        # The first byte has its prefix of '11',
        # letting us know where a code unit starts.
        ret_ints[idx_self_sync] |= MULTIBYTE_SELF_SYNC_BITS_FIRST
        idx_self_sync += 1

        # The continuation bytes have prefixes of '10'.
        while idx_self_sync < n_utf_8000_bytes_needed:
            ret_ints[idx_self_sync] |= MULTIBYTE_SELF_SYNC_BITS_CONTINUATION
            idx_self_sync += 1

    return bytes(ret_ints)
