from bitwarden_pyro.util.logger import ProjectLogger

from shutil import which

import os


class Executable:
    def __init__(self, tools):
        self._tools = tools
        self._logger = ProjectLogger().get_logger()

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

    def init_executable(self):
        """Find the most appropriate executables based on session type"""

        session_type = os.getenv('XDG_SESSION_TYPE')
        self._logger.debug("Initialising executable")

        # If session is a supported one
        if session_type is not None:
            self._logger.debug('Detected session type: %s', session_type)
            tools = self._tools.get(session_type)
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
                for ds, tool in self._tools.items()
                if which(tool) is not None
            ]

            if len(detected) == 0:
                self._logger.debug("No supported executables found")
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
                    "a guess: %s", detected
                )
                raise NotDecisiveException


class ExecutableException(Exception):
    """Base class for all exception originating from Completion"""
    pass


class NoExecutableException(ExecutableException):
    """Raised when no suitable executable can be found"""
    pass


class UnsupportedDesktopException(ExecutableException):
    """Raised when an unsupported desktop exception has been found"""
    pass


class NotDecisiveException(ExecutableException):
    """Raised when no decision upon which executable can be made"""
    pass
