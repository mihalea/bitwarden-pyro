#!/usr/bin/env python
import subprocess as sp
from subprocess import CalledProcessError
from logger import BwLogger


class Keybind:
    def __init__(self, key, event):
        self.key = key
        self.event = event


class Rofi:
    def __init__(self, args):
        self._logger = BwLogger().get_logger()
        self._keybinds = {}
        self._args = args[1:]

        if len(args) > 0:
            self._logger.debug("Setting rofi arguments: %s", self._args)

    def add_keybind(self, action, key, event):
        self._keybinds[action + 9] = Keybind(key, event)

    def get_password(self):
        try:
            self._logger.info("Launching rofi password prompt")
            cmd = [
                "rofi", "-dmenu", "-p", "Master Password",
                "-password", "-lines", "0"
            ]

            if len(self._args) > 0:
                cmd.extend(self._args)

            cp = sp.run(cmd, check=True, capture_output=True)
            return cp.stdout.decode("utf-8").strip()
        except CalledProcessError:
            self._logger.info("Password prompt has been closed")
            return None

    def show_items(self, items, prompt='Bitwarden'):
        try:
            self._logger.info("Launching rofi login select")
            echo_cmd = ["echo", items]
            rofi_cmd = [
                "rofi", "-dmenu", "-p", prompt, "-i", "-no-custom"
            ]

            if len(self._args) > 0:
                rofi_cmd.extend(self._args)

            echo_proc = sp.Popen(echo_cmd, stdout=sp.PIPE)
            rofi_proc = sp.run(
                rofi_cmd, stdin=echo_proc.stdout, stdout=sp.PIPE
            )

            rc = rofi_proc.returncode
            selected = rofi_proc.stdout.decode("utf-8").strip()
            # Clean exit
            if rc == 1:
                return None, None
            # Selected item by enter
            elif rc == 0:
                return selected, None
            # Selected item using custom keybind
            elif rc in self._keybinds:
                return selected, self._keybinds.get(rc).event
            else:
                self._logger.warning(
                    "Unknown return code has been received: %s", rc
                )
                return None, None

        except CalledProcessError:
            self._logger.info("Login select has been closed")
            return None
