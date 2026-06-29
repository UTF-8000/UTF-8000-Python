from .UTF8000Byte import (
    MULTIBYTE_SELF_SYNC_BITS_CONTINUATION,
    MULTIBYTE_PROGRAMMABLE_MASK,
    MULTIBYTE_PROGRAMMABLE_N_BITS,
    MULTIBYTE_FILLED_FIRST,
    MULTIBYTE_FILLED_CONTINUATION,
    ceil_div, fill_n_bits_shifted_by_m
)

def encode(x: int, signed: bool = False) -> bytes:
    """
    Encode an integer `x` into UTF-8000 bytes.
    """

    if signed:
        raise NotImplementedError

    if x < 0:
        raise ValueError("Cannot encode negative number in unsigned mode")

    ret_ints: list[int] = []

    if x < 0x80:
        ret_ints.append(x)

        return bytes(ret_ints)

    contents: list[int] = []
    n_bits_content_total: int = 0
    y: int = x

    while y > MULTIBYTE_PROGRAMMABLE_MASK:
        final_6_bits = y & MULTIBYTE_PROGRAMMABLE_MASK
        contents.insert(0, final_6_bits)
        n_bits_content_total += MULTIBYTE_PROGRAMMABLE_N_BITS
        y >>= MULTIBYTE_PROGRAMMABLE_N_BITS

    final_6_bits = y
    contents.insert(0, final_6_bits)
    while y > 0:
        n_bits_content_total += 1
        y >>= 1

    n_utf_8000_bytes_needed = ceil_div(n_bits_content_total - 1, 5)

    if n_utf_8000_bytes_needed < 8:
        final_start_byte = fill_n_bits_shifted_by_m(n_utf_8000_bytes_needed, 8 - n_utf_8000_bytes_needed)

        n_bytes_pure_content_and_final_start = n_utf_8000_bytes_needed
    else:
        first_byte = MULTIBYTE_FILLED_FIRST

        ret_ints.append(first_byte)

        n_remaining_start_ones = n_utf_8000_bytes_needed - 8

        n_filled_continuation_start_bytes, n_ones_in_final_start_byte = divmod(n_remaining_start_ones, MULTIBYTE_PROGRAMMABLE_N_BITS)

        for _ in range(n_filled_continuation_start_bytes):
            ret_ints.append(MULTIBYTE_FILLED_CONTINUATION)

        final_start_byte_start_bits = fill_n_bits_shifted_by_m(n_ones_in_final_start_byte, MULTIBYTE_PROGRAMMABLE_N_BITS - n_ones_in_final_start_byte)
        final_start_byte = MULTIBYTE_SELF_SYNC_BITS_CONTINUATION | final_start_byte_start_bits

        n_full_start_bytes = 1 + n_filled_continuation_start_bytes
        n_bytes_pure_content_and_final_start = n_utf_8000_bytes_needed - n_full_start_bytes

    if len(contents) == n_bytes_pure_content_and_final_start:
        final_start_byte_contents = contents.pop(0)
        final_start_byte |= final_start_byte_contents

    ret_ints.append(final_start_byte)

    for non_start_byte_contents in contents:
        non_start_byte = MULTIBYTE_SELF_SYNC_BITS_CONTINUATION | non_start_byte_contents
        ret_ints.append(non_start_byte)

    return bytes(ret_ints)
