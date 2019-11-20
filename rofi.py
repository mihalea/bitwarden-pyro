#!/usr/bin/env python
import subprocess
from subprocess import CalledProcessError
from traceback import print_exc


class Rofi:
    def get_password(self):
        try:
            cmd = "rofi -dmenu -p 'Master Password' -password -lines 0"
            cp = subprocess.run(cmd.split(), check=True, capture_output=True)
            return cp.stdout.decode("utf-8").strip()
        except CalledProcessError:
            print("Rofi has been closed")
            return None
