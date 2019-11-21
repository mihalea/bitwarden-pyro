#!/usr/bin/env python
import argparse
from settings import NAME


class SmartFormatter(argparse.HelpFormatter):
    def _split_lines(self, text, width):
        if text.startswith('R|'):
            return text[2:].splitlines()
        # this is the RawTextHelpFormatter._split_lines
        return argparse.HelpFormatter._split_lines(self, text, width)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Rofi-based graphical interface for the official "
        + "BitWarden CLI",
        usage=usage(),
        formatter_class=SmartFormatter
    )

    parser.add_argument(
        "--version",
        help="show version information and exit",
        action="store_true"
    )

    parser.add_argument(
        '-v', '--verbose',
        help="increase verbosity level",
        action='store_true',
    )

    parser.add_argument(
        "-t", "--timeout",
        help="R|automatically lock the vault in TIMEOUT seconds\n" +
        "use 0 to lock immediately\n" +
        "use -1 to disable\n"
    )

    parser.add_argument(
        'rofi_args',
        help=argparse.SUPPRESS,
        nargs=argparse.REMAINDER
    )

    return parser.parse_args()


def usage(name=None):
    return f'''{NAME} [OPTIONS] -- [ROFI OPTIONS]'''
