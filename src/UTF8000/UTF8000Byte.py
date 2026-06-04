from . import color

# size_t counting num of bytes; this is the only machine limitation
# little bittian ordered (1, 2, 4, 8, 16, 32, 64, 128)

ZERO               = 0b00000000

ASCII_PREFIX       = 0b00000000
ASCII_PREFIX_MASK  = 0b10000000
ASCII_CONTENT_MASK = 0b01111111

CONTINUATION_PREFIX       = 0b10000000
CONTINUATION_PREFIX_MASK  = 0b11000000
CONTINUATION_CONTENT_MASK = 0b00111111
CONTINUATION_FILLED       = 0b10111111

FIRST_BYTE_FULL = 0b11111111

OVERLONG_MASK_2_BYTE = 0b00011110

# These masks are ordered such that the i'th one corresponds with
# the final start byte containing i bits of content.
# We used to calculate these on-the-fly in the decoder, but it's much
# better to have them static like this. In particular if we were to implement
# this decoder in C, these would maybe be shoved inside the decoder function
# for even better performance.
OVERLONG_MASKS_N_BYTE = (
    (0b00000000, 0b00111110),
    (0b00000001, 0b00111100),
    (0b00000011, 0b00111000),
    (0b00000111, 0b00110000),
    (0b00001111, 0b00100000),
    (0b00011111, 0b00000000),
)

# How many bits in a first byte and continuation byte are
# programmable with either start sequence bits, or content bits.
N_BITS_FIRST_BYTE        = 8
N_BITS_CONTINUATION_BYTE = 6

# MIN = minimum
# SUP = supremum
UNICODE_MIN = 0x0
UNICODE_SUP = 0x11_0000

UTF_8_1_SUP = 0x00_0080 # 1 << 7
UTF_8_2_SUP = 0x00_0800 # 1 << 11
UTF_8_3_SUP = 0x01_0000 # 1 << 16
UTF_8_4_SUP = 0x11_0000 # (1 << 20) + (1 << 16) NB: not 1 << 21

UNICODE_SURROGATE_HIGH_MIN = 0xD800
UNICODE_SURROGATE_HIGH_SUP = 0xDC00
UNICODE_SURROGATE_LOW_MIN  = 0xDC00
UNICODE_SURROGATE_LOW_SUP  = 0xE000

def ceil_div(x: int, y: int) -> int:
    return -(x // -y)

def fill_n_bits_shifted_by_m(n: int, m: int) -> int:
    pass         # example with n == 3, m == 4
    ret = 1      # 0b00000001
    ret <<= n    # 0b00001000
    ret -= 1     # 0b00000111
    ret <<= m    # 0b01110000
    return ret

def extract_n_bits_at_m(x: int, n: int, m: int, downshift: bool = True):
    pass                                  # example with n == 3, m == 4, downshift == True
    ret = x                               # 0bABCDEFGH
    mask = fill_n_bits_shifted_by_m(n, m) # 0b01110000
    ret &= mask                           # 0b0BCD0000
    if downshift:                         #
        ret >>= m                         # 0b00000BCD
    return ret

def byte_is_ascii(c: int) -> bool:
    return c & ASCII_PREFIX_MASK == ASCII_PREFIX

def byte_is_continuation(c: int) -> bool:
    return c & CONTINUATION_PREFIX_MASK == CONTINUATION_PREFIX

def int_find_highest_zero(c: int, n_bits: int) -> int:
    """
    Return the index of the highest 0 bit in the lowest `n_bits` of `c`.

    Returns -1 if a 0 bit is not found.
    """
    ret = n_bits - 1
    mask = 1 << ret
    for _ in range(n_bits):
        if not mask & c:
            break
        mask >>= 1
        ret -= 1
    return ret

def int_find_highest_one(c: int, n_bits: int) -> int:
    """
    Find the highest 1 in the lowest `n_bits` of `c`.

    Returns -1 if a 1 bit is not found.
    """
    ret = n_bits - 1
    mask = 1 << ret
    for _ in range(n_bits):
        if mask & c:
            break
        mask >>= 1
        ret -= 1
    return ret

def idx_highest_zero(c: int, n_bits: int) -> int:
    """
    Return the index of the highest 0 bit in the lowest `n_bits` of `c`.

    Returns -1 if a 0 bit is not found.
    """

    return int_find_highest_zero(c, n_bits)

def n_start_bits_ones(idx_0: int, n_bits: int) -> int:
    """
    Pass in `idx_0`, the result of calling `idx_highest_zero` with `n_bits`.

    Returns the number of extra bytes we expect in a code unit
    having read a 0 bit at `idx_0`, ie how many 1 bits there are
    above `idx_0` in the window of `n_bits`.
    """

    return (n_bits - 1) - idx_0

class UTF8000Byte:
    def __init__(self, c: int, *,
        is_continuation_byte:     bool,
        is_start_byte:            bool,
        n_bits_content_total:     int,
        n_bits_content_mandatory: int,
    ) -> None:
        self.c = c
        self.is_continuation_byte     = is_continuation_byte
        self.is_start_byte            = is_start_byte
        self.n_bits_content_total     = n_bits_content_total
        self.n_bits_content_mandatory = n_bits_content_mandatory

    def __int__(self) -> int:
        return self.c

    def __str__(self) -> str:
        return f"0b{self.c:08b}"

    def __format__(self, format_spec: str) -> str:
        """
        Format the byte to be human readable.

        Format specifiers are comma-separated.

        if 'x' or 'X' is passed then:
            Format in hex.

        elif 'b' or no presentation type is passed then:
            Format in binary.

            if 'color' is passed then:
                Format in color

        if '#' is passed then:
            Prefix the string with the presentation type's prefix
            ('0x', '0X', '0b', '0B')
        """

        format_spec_args = format_spec.split(",")
        # primitive but enough

        do_base_prefix = "#"     in format_spec_args
        do_color       = "color" in format_spec_args

        if 'x' in format_spec_args:
            # Return hex digits.
            base_prefix = "0x" if do_base_prefix else ""
            return f"{base_prefix}{self.c:02x}"
        elif 'X' in format_spec_args:
            # Return HEX digits.
            base_prefix = "0X" if do_base_prefix else ""
            return f"{base_prefix}{self.c:02X}"

        if 'B' in format_spec_args:
            base_prefix = "0B" if do_base_prefix else ""
        else:
            base_prefix = "0b" if do_base_prefix else ""

        # Calculate the number of self-synchronization prefix bits.
        if self.is_ascii:
            # '0' for ASCII, a special case.
            n_bits_continuation_prefix = 1
        elif not self.is_continuation_byte:
            # '11' for the first byte of a UTF-8000 code unit.
            n_bits_continuation_prefix = 2
        else:
            # '10' for a continuation byte of a UTF-8000 code unit.
            n_bits_continuation_prefix = 2

        n_bits_content_total     = self.n_bits_content_total
        n_bits_content_mandatory = self.n_bits_content_mandatory
        n_bits_content_optional  = n_bits_content_total - n_bits_content_mandatory
        n_bits_start_sequence    = 8 - n_bits_continuation_prefix - n_bits_content_total

        str_continuation_prefix = self._format_bit_field(
            n_bits_continuation_prefix, 8 - n_bits_continuation_prefix,
            color = color.CSI_BOLD + color.CSI_FG_CYAN, do_color = do_color
        )
        str_start_sequence_bits = self._format_bit_field(
            n_bits_start_sequence, n_bits_content_total,
            color = color.CSI_BOLD + color.CSI_FG_MAGENTA, do_color = do_color
        )
        str_content_mandatory = self._format_bit_field(
            n_bits_content_mandatory, n_bits_content_optional,
            color = color.CSI_BOLD + color.CSI_FG_GREEN, do_color = do_color
        )
        str_content_optional = self._format_bit_field(
            n_bits_content_optional, 0,
            color = color.CSI_FG_GREEN, do_color = do_color
        )

        return f"{base_prefix}{str_continuation_prefix}{str_start_sequence_bits}{str_content_mandatory}{str_content_optional}"

    def _format_bit_field(
        self, width: int, offset: int,
        *,
        color: str = None, do_color: bool = False
    ) -> str:
        if width == 0:
            # Normal string formatting of zero returns "0" but we want "".
            return ""

        data = extract_n_bits_at_m(self.c, width, offset)

        ret = f"{data:0{width}b}"

        if do_color:
            CSI_RESET = "\x1b[0m"
            ret = f"{color}{ret}{CSI_RESET}"

        return ret

    @property
    def is_ascii(self) -> bool:
        return self.n_bits_content_total == 7

    @property
    def is_content_byte(self) -> bool:
        return self.n_bits_content_total > 0

    @property
    def content(self) -> int:
        content_mask = fill_n_bits_shifted_by_m(self.n_bits_content_total, 0)

        return self.c & content_mask

    @classmethod
    def ASCII(cls, c: int):
        """
        Return an ASCII byte '0b0xxxxxxx'.
        """
        return cls(
            c,
            is_continuation_byte = False,
            is_start_byte = True,
            n_bits_content_total = 7,
            n_bits_content_mandatory = 0
        )

    @classmethod
    def TwoByteStartByte(cls, c: int):
        """
        Return a '0b110XXXXx' start byte for a two byte UTF-8 sequence.

        `c` is the whole octet, including the upper '110' bits,
        not just the quintet of content.
        """
        return cls(
            c,
            is_continuation_byte = False,
            is_start_byte = True,
            n_bits_content_total = 5,
            n_bits_content_mandatory = 4
        )

    @classmethod
    def OnesFilledFirstStartByte(cls):
        """
        Return a '0b11111111' filled up first start byte.
        """
        return cls(
            FIRST_BYTE_FULL,
            is_continuation_byte = False,
            is_start_byte = True,
            n_bits_content_total = 0,
            n_bits_content_mandatory = 0
        )

    @classmethod
    def OnesFilledContinuationStartByte(cls):
        """
        Return a '0b10111111' filled up continuation start byte.
        """
        return cls(
            CONTINUATION_FILLED,
            is_continuation_byte = True,
            is_start_byte = True,
            n_bits_content_total = 0,
            n_bits_content_mandatory = 0
        )

    @classmethod
    def ContinuationNonStartByteFirst(cls, c: int, *, n_bits_content_mandatory: int):
        """
        Return a '0b10yyyyyy' continuation byte that is the first byte that
        is not a start byte, and has the specified number of
        mandatory content bits >= 0.

        `c` is the whole octet, including the upper '10' bits,
        not just the hextet of content.
        """

        return cls(
            c,
            is_continuation_byte = True,
            is_start_byte = False,
            n_bits_content_total = 6,
            n_bits_content_mandatory = n_bits_content_mandatory
        )

    @classmethod
    def ContinuationNonStartByteNotFirst(cls, c: int):
        """
        Return a '0b10yyyyyy' continuation byte that is not a start byte,
        and is not the first non-start byte, ie this byte has
        no mandatory content bits.

        `c` is the whole octet, including the upper '10' bits,
        not just the hextet of content.
        """

        return cls(
            c,
            is_continuation_byte = True,
            is_start_byte = False,
            n_bits_content_total = 6,
            n_bits_content_mandatory = 0
        )
