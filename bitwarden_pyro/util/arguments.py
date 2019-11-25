#!/usr/bin/env python
import argparse
from bitwarden_pyro.settings import NAME
from bitwarden_pyro.controller.session import Session
from bitwarden_pyro.model.actions import ItemActions
from enum import Enum


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
        "-l", "--lock",
        help="Lock vault and delete session key",
        action="store_true"
    )

    parser.add_argument(
        "-t", "--timeout",
        help=f"R|automatically lock the vault after TIMEOUT seconds (default: {Session.DEFAULT_TIMEOUT})\n" +
        "use  0 to lock immediately\n" +
        "use -1 to disable"
    )

    parser.add_argument(
        "-e", "--enter",
        help="R|action triggered by pressing Enter (default: %(default)s)\n" +
        "copy   - copy password to clipboard\n" +
        "all    - auto type username and password\n" +
        "passwd - auto type password\n" +
        "topt   - copy TOPT to clipboard",
        choices=list(ItemActions),
        type=ItemActions,
        default=ItemActions.COPY
    )

    parser.add_argument(
        "-c", "--clear",
        help="R|clear the clipboard after CLEAR seconds (default: %(default)s)\n" +
        "use -1 to disable",
        default=5
    )

    parser.add_argument(
        'rofi_args',
        help=argparse.SUPPRESS,
        nargs=argparse.REMAINDER
    )

    return parser.parse_args()


def usage(name=None):
    return f'''{NAME} [OPTIONS] -- [ROFI OPTIONS]'''
