import argparse

from UTF8000.encode import encode
from UTF8000.decode import UTF8000IncrementalDecoder
from UTF8000.UTF8000Byte import (
    UNICODE_SUP, UTF_8_1_SUP,
    UNICODE_SURROGATE_HIGH_MIN, UNICODE_SURROGATE_HIGH_SUP,
    UNICODE_SURROGATE_LOW_MIN, UNICODE_SURROGATE_LOW_SUP
)

from .common import (
    yes_no_is_stdout_tty,
    parse_codepoint, format_codepoint
)

def main_info(args: argparse.Namespace) -> None:
    # Initialise from args
    do_color: bool = yes_no_is_stdout_tty(args.color)
    n_str:    str  = args.n_str

    n = parse_codepoint(n_str)

    # Encode integer `n` in UTF-8000
    encoded = encode(n)
    decoder = UTF8000IncrementalDecoder()
    decoder.feed(encoded)
    code_unit = next(iter(decoder))

    # Print some info about the bytes / codepoint
    info_lines = []

    ## Unicode info
    line_parts = []
    if n < UNICODE_SUP:
        line_parts.append("In the Unicode range")
        if n in range(UNICODE_SURROGATE_HIGH_MIN, UNICODE_SURROGATE_HIGH_SUP):
            line_parts.append("(high surrogate)")
        elif n in range(UNICODE_SURROGATE_LOW_MIN, UNICODE_SURROGATE_LOW_SUP):
            line_parts.append("(low surrogate)")
        else:
            pass
        line_parts.append(format_codepoint(n))
        line_parts.append(f"{chr(n)!r}")
    else:
        line_parts.append("Beyond the Unicode range")
        line_parts.append("(adventurous)")
        line_parts.append(format_codepoint(n))
    info_lines.append(" ".join(line_parts))

    ## ASCII / UTF-8 / UTF-8000 length
    line_parts = []
    if n < UTF_8_1_SUP:
        codepoint_family = "ASCII"
    elif n < UNICODE_SUP:
        codepoint_family = "UTF-8"
    else:
        codepoint_family = "UTF-8000"
    line_parts.append(f"{code_unit.n_bytes} byte {codepoint_family}")
    line_parts.append(f"{code_unit.n_bits_content_total} bits")
    line_parts.append(f"{code_unit.n_bits_content_mandatory} mandatory bits")
    info_lines.append(" | ".join(line_parts))

    ## Hex bytes
    hex_bytes = " ".join(f"{int(b):02x}" for b in code_unit.utf_8000_bytes)
    info_lines.append(f"Hex: {hex_bytes}")

    ## Bin bytes
    fmt_parts = []
    if do_color:
        fmt_parts.append("color")
    fmt = ",".join(fmt_parts)
    # If there's a "," in a fmt_part then there's problems,
    # but our script won't do that.
    # Remember GitHub not sanitizing their input:
    # https://www.youtube.com/watch?v=m5t08CREHcE

    bin_bytes = " ".join(f"{b:{fmt}}" for b in code_unit.utf_8000_bytes)
    info_lines.append(f"Bin: {bin_bytes}")

    print("\n\n".join(info_lines))
