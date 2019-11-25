from bitwarden_pyro.util.logger import ProjectLogger
from bitwarden_pyro.util.executable import Executable

from shutil import which
from subprocess import CalledProcessError
from time import sleep

import subprocess as sp
import os


class AutoType:
    _tools = {
        'x11': ['xdotool'],
        'wayland': ['sudo ydotool']
    }

    def __init__(self):
        self._exec = Executable.init_executable(self._tools)
        self._logger = ProjectLogger().get_logger()

    def string(self, string):
        """Type a string emulating a keyboard"""

        self.__emulate_keyboard('type', string)

    def key(self, key):
        """Type a single key emulating a keyboard"""

        self.__emulate_keyboard('key', key)

    def __emulate_keyboard(self, action, value):
        """Emulate keyboard input"""

        try:
            self._logger.debug("Emulating keyboard input for %s", action)
            type_cmd = f"{self._exec} {action} {value}"
            sp.run(type_cmd.split(), check=True, capture_output=True)
        except CalledProcessError:
            self._logger.error("Failed to emulate keyboard input")
            raise AutoTypeException


class AutoTypeException(Exception):
    """Raised when emulating keyboard strings failed"""
    pass
