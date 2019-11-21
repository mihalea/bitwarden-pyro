#!/usr/bin/env python

from shutil import which
from logger import BwLogger
import os


class Completion:
    _logger = None
    _default_tools = {
        'autotype': {
            'x11': ['xdotool'],
            'wayland': ['sudo ydotool']
        },
        'copy': {
            'wayland': ['wl-copy'],
            'x11': ['xclip', 'xsel']
        }
    }

    def __init__(self):
        self._type = None
        self._copy = None

        self._logger = BwLogger().get_logger()
        self._type = self.__init_executable('autotype')
        self._copy = self.__init_executable('copy')

    def __find_executable(self, tools):
        """Return a single executable installed on the system

        Arguments:
            tools {list of string} -- A list of possible executable names

        Raises:
            NoExecutableException: Raised when no suitable executable has been found

        Returns:
            string -- Name of valid executable
        """

        for t in tools:
            if which(t) is not None:
                self._logger.debug("Found valid executable '%s'", t)
                return t

        # If not valid executable has been found, log and exit
        self._logger.critical(
            "Could not find executable: '%s'", tools
        )
        raise NoExecutableException

    def __init_executable(self, tool_group):
        """Find the most appropriate executables based on session type

        Arguments:
            tool_group {string} -- Name of a valid tool group

        Returns:
            string -- Name of a valid executable
        """
        session_type = os.getenv('XDG_SESSION_TYPE')
        self._logger.debug("Initialising executable for %s", tool_group)
        if session_type is not None:
            self._logger.debug('Detected session type: %s', session_type)
            tools = self._default_tools.get(tool_group).get(session_type)
            if tools is not None:
                return self.__find_executable(tools)
            else:
                self._logger.critical(
                    "Desktop session not supported: %s", session_type
                )
                raise UnsupportedDesktopException
        else:
            self._logger.warning(
                "Could not read desktop session type from environment, " +
                "trying to guess based on detected executables"
            )

            detected = [
                (ds, tool)
                for ds, tool in self._default_tools.get(tool_group).items()
                if which(tool) is not None
            ]

            detected_sessions = set([d[0] for d in detected])

            if len(detected) == 0:
                self._logger.critical(
                    "No supported executables found for '%s'", tool_group
                )
                raise NoExecutableException(
                    f"Failed to find executable for {tool_group}"
                )
            elif len(detected_sessions) == 1:
                return self.__find_executable([d[1] for d in detected])
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
