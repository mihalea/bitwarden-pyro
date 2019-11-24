#!/usr/bin/env python
import subprocess as sp
from subprocess import CalledProcessError
from logger import BwLogger


class Rofi:
    def __init__(self):
        self._logger = BwLogger().get_logger()

    def get_password(self):
        try:
            self._logger.info("Launching rofi password prompt")
            cmd = [
                "rofi", "-dmenu", "-p", "Master Password",
                "-password", "-lines", "0"
            ]
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
            echo_proc = sp.Popen(echo_cmd, stdout=sp.PIPE)
            rofi_proc = sp.check_output(rofi_cmd, stdin=echo_proc.stdout)

            return rofi_proc.decode("utf-8").strip()
        except CalledProcessError:
            self._logger.info("Login select has been closed")
            return None
