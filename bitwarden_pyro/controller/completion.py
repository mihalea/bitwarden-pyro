from bitwarden_pyro.util.logger import ProjectLogger

from shutil import which
from subprocess import CalledProcessError
from enum import Enum, auto
from time import sleep
import subprocess as sp
import os


class Clipboard(Enum):
    GET = auto()
    SET = auto()
    CLEAR = auto()


class Completion:
    _default_tools = {
        'autotype': {
            'x11': ['xdotool'],
            'wayland': ['sudo ydotool']
        },
        'copy': {
            'wayland': {
                'wl-copy': {
                    Clipboard.GET: 'wl-paste',
                    Clipboard.SET: 'wl-copy',
                    Clipboard.CLEAR: 'wl-copy --clear'
                }
            },
            'x11': {
                'xclip': {
                    Clipboard.GET: 'xclip -selection clipboard -o',
                    Clipboard.SET: 'xclip -selection clipboard -r',
                    Clipboard.CLEAR: 'echo lul | xclip -selection clipboard -r'
                },
                'xsel': {
                    Clipboard.GET: 'xsel --clipboard',
                    Clipboard.SET: 'xsel --clipboard --input',
                    Clipboard.CLEAR: 'xsel --clipboard --delete'
                }}
        }
    }

    def __init__(self, clear):
        self._type = None
        self._copy = None
        self._tools = None
        self._clear = clear

        self._logger = ProjectLogger().get_logger()

        self._type = self.__init_executable('autotype')
        self._copy = self.__init_executable('copy')

    def clipboard_get(self):
        return self.__emulate_clipboard(Clipboard.GET)

    def clipboard_set(self, value):
        self.__emulate_clipboard(Clipboard.SET, value)

        if self._clear >= 0:
            sleep(self._clear)
            self._logger.info("Clearing clipboard")
            self.__clipboard_clear()

    def __clipboard_clear(self):
        self.__emulate_clipboard(Clipboard.CLEAR)

    def __emulate_clipboard(self, action, value=None):
        """Interact with the clipboard"""

        try:
            self._logger.debug("Interacting with clipboard: %s", action)
            command = self._copy.get(action)

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
                raise CopyingException
        except CalledProcessError as e:
            self._logger.error("Failed to interact with clipboard")
            raise CopyingException from e

    def type_string(self, string):
        """Type a string emulating a keyboard"""

        self.__emulate_keyboard('type', string)

    def type_key(self, key):
        """Type a single key emulating a keyboard"""

        self.__emulate_keyboard('key', key)

    def __emulate_keyboard(self, action, value):
        """Emulate keyboard input"""

        try:
            self._logger.debug("Emulating keyboard input for %s", action)
            type_cmd = f"{self._type} {action} {value}"
            sp.run(type_cmd.split(), check=True, capture_output=True)
        except CalledProcessError as e:
            self._logger.error("Failed to emulate keyboard input")
            raise TypingException from e

    def __find_executable(self, tools):
        """Return a single executable installed on the system from the list"""

        for t in tools:
            if which(t) is not None:
                self._logger.debug("Found valid executable '%s'", t)

                if isinstance(tools, dict):
                    return tools.get(t)
                else:
                    return t

        # If no valid executable has been found, log and raise
        self._logger.critical(
            "Could not find executable: '%s'", tools
        )
        raise NoExecutableException

    def __init_executable(self, tool_group):
        """Find the most appropriate executables based on session type"""

        session_type = os.getenv('XDG_SESSION_TYPE')
        self._logger.debug("Initialising executable for %s", tool_group)

        # If session is a supported one
        if session_type is not None:
            self._logger.debug('Detected session type: %s', session_type)
            tools = self._default_tools.get(tool_group).get(session_type)
            # If there are tools defined for the current tool_group
            if tools is not None:
                return self.__find_executable(tools)
            else:
                self._logger.critical(
                    "Desktop session not supported: %s", session_type
                )
                raise UnsupportedDesktopException
        # If session is not supported, try and make the best
        # guess based on available executables
        else:
            self._logger.warning(
                "Could not read desktop session type from environment, " +
                "trying to guess based on detected executables"
            )

            # List of available executables
            detected = [
                (ds, tool)
                for ds, tool in self._default_tools.get(tool_group).items()
                if which(tool) is not None
            ]

            if len(detected) == 0:
                self._logger.critical(
                    "No supported executables found for '%s'", tool_group
                )
                return None

            # List of unique desktop sessions for which executables have
            # been found
            detected_sessions = set([d[0] for d in detected])

            # Available executables are all for the same desktop session
            if len(detected_sessions) == 1:
                return self.__find_executable([d[1] for d in detected])

            # If executables are from multiple desktop sessions, the best one
            # can't be picked automatically, as we can't assume the currently
            # running desktop session
            elif len(detected_sessions) > 1:
                self._logger.warning(
                    "Found too many supported executable to be able to make " +
                    "a guess for '%s': %s", tool_group, detected
                )
                raise NotDecisiveException


class CompletionException(Exception):
    """Base class for all exception originating from Completion"""
    pass


class NoExecutableException(CompletionException):
    """Raised when no suitable executable can be found"""
    pass


class UnsupportedDesktopException(CompletionException):
    """Raised when an unsupported desktop exception has been found"""
    pass


class NotDecisiveException(CompletionException):
    """Raised when no decision upon which executable can be made"""
    pass


class TypingException(CompletionException):
    """Raised when emulating keyboard strings failed"""
    pass


class CopyingException(CompletionException):
    """Raised when interacting with the clipboard failed"""
    pass
