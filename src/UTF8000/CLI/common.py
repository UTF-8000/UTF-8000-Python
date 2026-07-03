import os
import sys

U_PLUS_PREFIX = "U+"

def yes_no_is_fd_tty(s: str, fd: int) -> bool:
    if s == "yes":
        return True
    if s == "no":
        return False
    if s == "auto":
        return os.isatty(fd)
    raise ValueError(f"Got {s!r} when expecting 'yes', 'no', or 'auto'")

def yes_no_is_stdin_tty(s: str) -> bool:
    return yes_no_is_fd_tty(s, sys.stdin.fileno())

def yes_no_is_stdout_tty(s: str) -> bool:
    return yes_no_is_fd_tty(s, sys.stdout.fileno())

def parse_codepoint(s: str) -> int:
    """
    Parse a codepoint string.

    If it begins with U+ or u+ treat it as hex 'U+(...X)X'.
    Otherwise treat it as decimal.
    """
    s = s.strip()
    s = s.upper()

    if s.startswith(U_PLUS_PREFIX):
        s = s.removeprefix(U_PLUS_PREFIX)
        base = 16
    else:
        base = 0

    return int(s, base)

def format_codepoint(n: int) -> str:
    """
    Format an integer as a unicode codepoint string.

    Returns strings of the form 'U+(...X)XXXX'.
    """

    return f"{U_PLUS_PREFIX}{n:04X}"
