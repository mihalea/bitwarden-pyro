import argparse

from bitwarden_pyro.settings import NAME
from bitwarden_pyro.model.actions import ItemActions
from bitwarden_pyro.util.config import ConfigLoader


class SmartFormatter(argparse.HelpFormatter):
    """Custom formatter breaking lines on \n"""

    def _split_lines(self, text, width):
        if text.startswith('R|'):
            return text[2:].splitlines()
        # this is the RawTextHelpFormatter._split_lines
        return argparse.HelpFormatter._split_lines(self, text, width)


def parse_arguments():
    """Parse command line arguments using argparse"""

    parser = argparse.ArgumentParser(
        description="Rofi-based graphical interface for the official "
        + "BitWarden CLI",
        usage=usage(),
        formatter_class=SmartFormatter
    )

    parser.add_argument(
        '-v', '--verbose',
        help="increase verbosity level",
        action='store_true',
    )

    parser.add_argument(
        "-l", "--lock",
        help="lock vault and delete session key",
        action="store_true"
    )

    parser.add_argument(
        "-s", "--select-window",
        help="select and focus window before auto typing",
        action="store_true"
    )

    parser.add_argument(
        "--hide-mesg",
        help="hide message explaining keybinds",
        action="store_true"
    )

    parser.add_argument(
        "--version",
        help="show version information and exit",
        action="store_true"
    )

    parser.add_argument(
        "--no-config",
        help="ignore config files and use default values",
        action="store_true"
    )

    parser.add_argument(
        "--dump-config",
        help="dump the contents of the config data to stdout",
        action="store_true"
    )

    parser.add_argument(
        '--no-logging',
        help="disable logging to file",
        action="store_true"
    )

    parser.add_argument(
        "--config",
        help="use a custom config file path"
    )

    parser.add_argument(
        '--cache',
        help="set the time in days it takes for cache to become invalid" +
        f" (default: {ConfigLoader.get_default('security', 'cache')})"
    )

    parser.add_argument(
        "-c", "--clear",
        help="R|clear the clipboard after CLEAR seconds" +
        f" (default: {ConfigLoader.get_default('security', 'clear')})\n" +
        "use -1 to disable"
    )

    parser.add_argument(
        "-t", "--timeout",
        help="R|automatically lock the vault after TIMEOUT seconds" +
        f" (default: {ConfigLoader.get_default('security', 'timeout')})\n" +
        "use  0 to lock immediately\n" +
        "use -1 to disable"
    )

    parser.add_argument(
        "-e", "--enter",
        help="R|action triggered by pressing Enter" +
        f" (default: {ConfigLoader.get_default('keyboard', 'enter')})\n" +
        "copy   - copy password to clipboard\n" +
        "all    - auto type username and password\n" +
        "passwd - auto type password\n" +
        "topt   - copy TOPT to clipboard",
        choices=list(ItemActions),
        type=ItemActions
    )

    parser.add_argument(
        "-w", "--window-mode",
        help="set the initial window mode" +
        f" (default: {ConfigLoader.get_default('interface', 'window_mode')})",
        choices=['uris', 'logins', 'names', 'folders']
    )

    parser.add_argument(
        'rofi_args',
        help=argparse.SUPPRESS,
        nargs=argparse.REMAINDER
    )

    return parser.parse_args()


def usage():
    """Custom usage text for help text"""

    return f'''{NAME} [OPTIONS] -- [ROFI OPTIONS]'''
