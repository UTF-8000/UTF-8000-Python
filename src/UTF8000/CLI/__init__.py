"""
UTF-8000 CLI
"""

import argparse

def get_cli_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description = __doc__)
    action = parser.add_subparsers(title = "action", dest = "action", required = True)

    args = parser.parse_args()

    return args

def main() -> None:
    args = get_cli_args()

    {
    }[args.action](args)
