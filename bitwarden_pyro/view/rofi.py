import subprocess as sp
from subprocess import CalledProcessError
from collections import namedtuple

from bitwarden_pyro.util.logger import ProjectLogger


Keybind = namedtuple("Kebind", "key event message show")


class Rofi:
    """Start and retrieve results from Rofi windows"""

    def __init__(self, args, enter_event, hide_mesg):
        self._logger = ProjectLogger().get_logger()
        self._keybinds = {}
        self._args = args[1:]
        self._enter_event = enter_event
        self._hide_mesg = hide_mesg
        self._keybinds_code = 10

        if len(args) > 0:
            self._logger.debug("Setting rofi arguments: %s", self._args)

    def __extend_command(self, command):
        if len(self._args) > 0:
            command.extend(self._args)

        if not self._hide_mesg:
            mesg = []
            for keybind in self._keybinds.values():
                if keybind.message is not None and keybind.show:
                    mesg.append(f"<b>{keybind.key}</b>: {keybind.message}")

            if len(mesg) > 0:
                command.extend([
                    "-mesg", ", ".join(mesg)
                ])

        for code, keybind in self._keybinds.items():
            command.extend([
                f"-kb-custom-{code - 9}",
                keybind.key
            ])

        return command

    def add_keybind(self, key, event, message, show):
        """Create a keybind object and add store it in memory"""

        if self._keybinds_code == 28:
            raise KeybindException(
                "The maximum number of keybinds has been reached"
            )

        self._keybinds[self._keybinds_code] = Keybind(
            key, event, message, show
        )
        self._keybinds_code += 1

    def get_password(self):
        """Launch a window requesting a password"""

        try:
            self._logger.info("Launching rofi password prompt")
            cmd = [
                "rofi", "-dmenu", "-p", "Master Password",
                "-password", "-lines", "0"
            ]

            if len(self._args) > 0:
                cmd.extend(self._args)

            proc = sp.run(cmd, check=True, capture_output=True)
            return proc.stdout.decode("utf-8").strip()
        except CalledProcessError:
            self._logger.info("Password prompt has been closed")
            return None

    def show_error(self, message):
        """Launch a window showing an error message"""

        try:
            self._logger.info("Showing Rofi error")
            cmd = ["rofi", "-e", f"ERROR! {message}"]

            if len(self._args) > 0:
                cmd.extend(self._args)

            sp.run(cmd, capture_output=True, check=True)
        except CalledProcessError:
            raise RofiException("Rofi failed to display error message")

    def show_items(self, items, prompt='Bitwarden'):
        """Show a list of items and return the selectem item and action"""

        try:
            self._logger.info("Launching rofi login select")
            echo_cmd = ["echo", items]
            rofi_cmd = self.__extend_command([
                "rofi", "-dmenu", "-p", prompt, "-i", "-no-custom"
            ])

            echo_proc = sp.Popen(echo_cmd, stdout=sp.PIPE)
            rofi_proc = sp.run(
                rofi_cmd, stdin=echo_proc.stdout, stdout=sp.PIPE, check=False
            )

            return_code = rofi_proc.returncode
            selected = rofi_proc.stdout.decode("utf-8").strip()
            # Clean exit
            if return_code == 1:
                return None, None
            # Selected item by enter
            if return_code == 0:
                return selected, self._enter_event
            # Selected item using custom keybind
            if return_code in self._keybinds:
                return selected, self._keybinds.get(return_code).event

            self._logger.warning(
                "Unknown return code has been received: %s", return_code
            )
            return None, None

        except CalledProcessError:
            self._logger.info("Login select has been closed")
            return None


class RofiException(Exception):
    """Base class for exceptions thrown by Rofi"""


class KeybindException(Exception):
    """Raised when no more arguments can be added"""
