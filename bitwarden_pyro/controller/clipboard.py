import subprocess as sp

from enum import Enum, auto
from time import sleep
from subprocess import CalledProcessError

from bitwarden_pyro.util.logger import ProjectLogger
from bitwarden_pyro.util.executable import init_executable


class ClipboardEvents(Enum):
    """Events that are supported by the clipboard emulator"""

    GET = auto()
    SET = auto()
    CLEAR = auto()


class Clipboard:
    """Interface with the clipboard to get, set and clear"""

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
        self._exec = init_executable(self._tools)
        self._logger = ProjectLogger().get_logger()

    def get(self):
        """Get the contents of the clipboard"""

        return self.__emulate_clipboard(ClipboardEvents.GET)

    def set(self, value):
        """Set the contents of the clipboard"""

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

            if command is None:
                raise ClipboardException(
                    f"Action '{action}' not supported by clipboard"
                )

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
                echo_proc = sp.Popen(input_cmd, stdout=sp.PIPE)
                output = sp.Popen(command.split(), stdin=echo_proc.stdout)
                return None

            output = sp.check_output(command.split())
            return output

        except CalledProcessError:
            raise ClipboardException("Failed to execute clipboard executable")


class ClipboardException(Exception):
    """Raised when interacting with the clipboard failed"""
