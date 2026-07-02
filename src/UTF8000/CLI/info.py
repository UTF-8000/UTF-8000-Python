import argparse

from UTF8000.encode import encode
from UTF8000.decode import UTF8000IncrementalDecoder
from UTF8000.UTF8000Byte import (
    UNICODE_SUP, UTF_8_1_SUP, UTF_8_2_SUP,
    UNICODE_SURROGATE_HIGH_MIN, UNICODE_SURROGATE_HIGH_SUP,
    UNICODE_SURROGATE_LOW_MIN, UNICODE_SURROGATE_LOW_SUP
)

from .common import (
    yes_no_is_stdout_tty,
    parse_codepoint, format_codepoint
)

def main_info(args: argparse.Namespace) -> None:
    # Initialise from args
    do_base_prefix: bool = getattr(args, "#")
    do_color:  bool = yes_no_is_stdout_tty(args.color)
    n_str:     str  = args.n_str

    n = parse_codepoint(n_str)

    # Encode integer `n` in UTF-8000
    encoded = encode(n)
    decoder = UTF8000IncrementalDecoder()
    decoder.feed(encoded)
    fancy_encoded = next(iter(decoder)).utf_8000_bytes

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
    line_parts.append(f"{len(fancy_encoded)}")
    line_parts.append("byte")
    if n < UNICODE_SUP:
        line_parts.append("UTF-8")
        if n < UTF_8_1_SUP:
            line_parts.append("(ASCII)")
    else:
        line_parts.append("UTF-8000")
    if n < UTF_8_1_SUP:
        n_bits = 7
        n_bits_mandatory = 0
    else:
        n_bits = 5 * len(fancy_encoded) + 1
        if n < UTF_8_2_SUP:
            n_bits_mandatory = 4
        else:
            n_bits_mandatory = 5
    line_parts.append(f"|")
    line_parts.append(f"{n_bits}")
    line_parts.append("bits")
    line_parts.append(f"|")
    line_parts.append(f"{n_bits_mandatory}")
    line_parts.append("mandatory bits")
    info_lines.append(" ".join(line_parts))

    ## Hex bytes
    line_parts = []
    line_parts.append("Hex:")
    if do_base_prefix:
        fmt = "#04x"
    else:
        fmt = "02x"
    line_parts.extend(f"{int(b):{fmt}}" for b in fancy_encoded)
    info_lines.append(" ".join(line_parts))

    fmt_parts = []
    if do_base_prefix:
        fmt_parts.append("#")
    if do_color:
        fmt_parts.append("color")
    fmt = ",".join(fmt_parts)
    # If there's a "," in a fmt_part then there's problems,
    # but our script won't do that.
    # Remember GitHub not sanitizing their input:
    # https://www.youtube.com/watch?v=m5t08CREHcE

    ## Bin bytes
    line_parts = []
    line_parts.append("Bin:")
    line_parts.extend(f"{b:{fmt}}" for b in fancy_encoded)
    info_lines.append(" ".join(line_parts))

    print("\n\n".join(info_lines))
