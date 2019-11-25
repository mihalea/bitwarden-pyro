#!/usr/bin/env python

from bitwarden_pyro.util.logger import ProjectLogger

import subprocess as sp
from subprocess import CalledProcessError


class Keybind:
    def __init__(self, key, event):
        self.key = key
        self.event = event


class Rofi:
    def __init__(self, args):
        self._logger = ProjectLogger().get_logger()
        self._keybinds = {}
        self._args = args[1:]
        self._keybinds_code = 10

        if len(args) > 0:
            self._logger.debug("Setting rofi arguments: %s", self._args)

    def __extend_command(self, command):
        if len(self._args) > 0:
            command.extend(self._args)

        for code, keybind in self._keybinds.items():
            command.extend([
                f"-kb-custom-{code - 9}",
                keybind.key
            ])

        return command

    def add_keybind(self, key, event):
        if self._keybinds_code == 28:
            self._logger.warning(
                "The maximum number of keybinds has been reached"
            )
            raise KeybindException

        self._keybinds[self._keybinds_code] = Keybind(key, event)
        self._keybinds_code += 1

    def get_password(self):
        try:
            self._logger.info("Launching rofi password prompt")
            cmd = self.__extend_command([
                "rofi", "-dmenu", "-p", "Master Password",
                "-password", "-lines", "0"
            ])

            self._logger.debug("Running command: %s", cmd)
            cp = sp.run(cmd, check=True, capture_output=True)
            return cp.stdout.decode("utf-8").strip()
        except CalledProcessError:
            self._logger.info("Password prompt has been closed")
            return None

    def show_items(self, items, prompt='Bitwarden'):
        try:
            self._logger.info("Launching rofi login select")
            echo_cmd = ["echo", items]
            rofi_cmd = self.__extend_command([
                "rofi", "-dmenu", "-p", prompt, "-i", "-no-custom"
            ])

            self._logger.debug("Running command: %s", rofi_cmd)
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


class RofiException(Exception):
    """Base class for exceptions thrown by Rofi"""
    pass


class KeybindException(Exception):
    """Raised when no more arguments can be added"""
    pass
