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

    raise NotImplementedError

    return bytes(ret_ints)
