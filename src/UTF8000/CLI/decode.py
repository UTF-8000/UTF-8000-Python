import sys
import argparse

from UTF8000.decode import UTF8000IncrementalDecoder
from UTF8000.UTF8000Byte import UNICODE_SUP
from UTF8000.UTF8000Int import UTF8000Int

from .common import (
    yes_no_is_stdout_tty,
    format_codepoint
)

_MAX_LEN_CODEPOINT = len(r"U+10FFFF")
_MAX_LEN_CHR_REPR  = len(r"'\U0010fffd'")
_MAX_LEN_HEX_BYTES = len(r"f4 8f bf bf")

def format_code_unit(code_unit: UTF8000Int, *, do_color: bool) -> str:
    n = int(code_unit)

    ## Codepoint
    part_codepoint = f"{format_codepoint(n):{_MAX_LEN_CODEPOINT}}"

    ## Character repr
    if n < UNICODE_SUP:
        chr_repr = f"{chr(n)!r}"
    else:
        chr_repr = ""
    part_chr_repr = f"{chr_repr:{_MAX_LEN_CHR_REPR}}"

    ## Hex bytes
    hex_bytes = " ".join(f"{int(b):02x}" for b in code_unit.utf_8000_bytes)
    part_hex_bytes = f"{hex_bytes:{_MAX_LEN_HEX_BYTES}}"

    ## Bin bytes
    fmt_parts = []
    if do_color:
        fmt_parts.append("color")
    fmt = ",".join(fmt_parts)
    bin_bytes = " ".join(f"{b:{fmt}}" for b in code_unit.utf_8000_bytes)
    part_bin_bytes = f"{bin_bytes}"

    ret_parts = (part_codepoint, part_chr_repr, part_hex_bytes, part_bin_bytes)

    return " | ".join(ret_parts)

def main_decode(args: argparse.Namespace) -> None:
    do_color = yes_no_is_stdout_tty(args.color)

    decoder = UTF8000IncrementalDecoder()

    while chunk := sys.stdin.buffer.raw.read(4096):
        decoder.feed(chunk)

        for code_unit in decoder:
            print(format_code_unit(code_unit, do_color = do_color))

    decoder.close()
