from .UTF8000Byte import (
    MULTIBYTE_SELF_SYNC_BITS_FIRST,
    MULTIBYTE_SELF_SYNC_BITS_CONTINUATION,
    MULTIBYTE_PROGRAMMABLE_N_BITS,
    MULTIBYTE_PROGRAMMABLE_MASK,
    MULTIBYTE_SELF_PUNCTUATION_ONES_FULL,
    MULTIBYTE_SELF_PUNCTUATION_ONES_SOME,
    ceil_div
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
        ret_ints.insert(0, x)

        return bytes(ret_ints)

    n_bits_content_total: int = 0
    y: int = x

    while y > MULTIBYTE_PROGRAMMABLE_MASK:
        final_6_bits = y & MULTIBYTE_PROGRAMMABLE_MASK
        ret_ints.insert(0, final_6_bits)
        n_bits_content_total += MULTIBYTE_PROGRAMMABLE_N_BITS
        y >>= MULTIBYTE_PROGRAMMABLE_N_BITS

    final_6_bits = y
    ret_ints.insert(0, final_6_bits)
    while y > 0:
        n_bits_content_total += 1
        y >>= 1

    n_utf_8000_bytes_needed = ceil_div(n_bits_content_total - 1, 5)

    ret_ints = [0 for _ in range(n_utf_8000_bytes_needed - len(ret_ints))] + ret_ints

    idx_self_punctuation = 0

    n_start_bytes_filled_with_ones, n_ones_in_final_start_byte = divmod(n_utf_8000_bytes_needed - 2, MULTIBYTE_PROGRAMMABLE_N_BITS)

    while idx_self_punctuation < n_start_bytes_filled_with_ones:
        ret_ints[idx_self_punctuation] |= MULTIBYTE_SELF_PUNCTUATION_ONES_FULL
        idx_self_punctuation += 1

    ret_ints[idx_self_punctuation] |= MULTIBYTE_SELF_PUNCTUATION_ONES_SOME[n_ones_in_final_start_byte]

    idx_self_sync = 0

    ret_ints[idx_self_sync] |= MULTIBYTE_SELF_SYNC_BITS_FIRST
    idx_self_sync += 1

    while idx_self_sync < n_utf_8000_bytes_needed:
        ret_ints[idx_self_sync] |= MULTIBYTE_SELF_SYNC_BITS_CONTINUATION
        idx_self_sync += 1

    return bytes(ret_ints)
