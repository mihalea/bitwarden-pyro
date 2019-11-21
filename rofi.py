#!/usr/bin/env python
import subprocess
from subprocess import CalledProcessError
from logger import BwLogger


class Rofi:
    def __init__(self):
        self._logger = BwLogger().get_logger()

    def get_password(self):
        try:
            self._logger.info("Launching rofi password prompt")
            cmd = "rofi -dmenu -p MasterPassword -password -lines 0"
            cp = subprocess.run(cmd.split(), check=True, capture_output=True)
            return cp.stdout.decode("utf-8").strip()
        except CalledProcessError:
            self._logger.info("Password prompt has been closed")
            return None
