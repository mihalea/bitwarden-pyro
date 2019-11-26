from bitwarden_pyro.util.logger import ProjectLogger
from bitwarden_pyro.util.executable import Executable

import subprocess as sp

from enum import Enum, auto
from time import sleep
from subprocess import CalledProcessError


class ClipboardEvents(Enum):
    GET = auto()
    SET = auto()
    CLEAR = auto()


class Clipboard:
    _tools = {
        'wayland': {
            'wl-copy': {
                ClipboardEvents.GET: 'wl-paste',
                ClipboardEvents.SET: 'wl-copy',
                ClipboardEvents.CLEAR: 'wl-copy --clear'
            }
        },
        'x11': {
            'xclip': {
                ClipboardEvents.GET: 'xclip -selection clipboard -o',
                ClipboardEvents.SET: 'xclip -selection clipboard -r',
                ClipboardEvents.CLEAR: 'echo lul | xclip -selection clipboard -r'
            },
            'xsel': {
                ClipboardEvents.GET: 'xsel --clipboard',
                ClipboardEvents.SET: 'xsel --clipboard --input',
                ClipboardEvents.CLEAR: 'xsel --clipboard --delete'
            }}
    }

    def __init__(self, clear):
        self.clear = clear
        self._exec = Executable.init_executable(self._tools)
        self._logger = ProjectLogger().get_logger()

    def get(self):
        return self.__emulate_clipboard(ClipboardEvents.GET)

    def set(self, value):
        self.__emulate_clipboard(ClipboardEvents.SET, value)

        if self.clear >= 0:
            sleep(self.clear)
            self._logger.info("Clearing clipboard")
            self.__clear()

    def __clear(self):
        self.__emulate_clipboard(ClipboardEvents.CLEAR)

    def __emulate_clipboard(self, action, value=None):
        """Interact with the clipboard"""

        try:
            self._logger.debug("Interacting with clipboard: %s", action)
            command = self._exec.get(action)

            if command is not None:
                self._logger.debug("Executing command %s", command)

                input_cmd = None
                if "|" in command:
                    cmds = command.split("|")
                    input_cmd = cmds[0]
                    command = cmds[1]
                elif value is not None:
                    input_cmd = f"echo {value}"

                if input_cmd is not None:
                    input_cmd = input_cmd.split(" ", 2)
                    ep = sp.Popen(input_cmd, stdout=sp.PIPE)
                    output = sp.Popen(command.split(), stdin=ep.stdout)
                else:
                    output = sp.check_output(command.split())
                    return output

            else:
                self._logger.error(
                    "Action %s is not supported for clipboard", action
                )
                raise ClipboardException
        except CalledProcessError:
            self._logger.error("Failed to interact with clipboard")
            raise ClipboardException


class ClipboardException(Exception):
    """Raised when interacting with the clipboard failed"""
    pass
