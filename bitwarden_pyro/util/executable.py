from bitwarden_pyro.util.logger import ProjectLogger

from shutil import which

import os


class Executable:
    @staticmethod
    def __find_executable(tools):
        """Return a single executable installed on the system from the list"""
        logger = ProjectLogger().get_logger()

        for t in tools:
            if which(t) is not None:
                logger.debug("Found valid executable '%s'", t)

                if isinstance(tools, dict):
                    return tools.get(t)
                else:
                    return t

        # If no valid executable has been found, log and raise
        logger.critical(
            "Could not find executable: '%s'", tools
        )
        raise NoExecutableException

    @staticmethod
    def init_executable(tools):
        """Find the most appropriate executables based on session type"""

        logger = ProjectLogger().get_logger()

        session_type = os.getenv('XDG_SESSION_TYPE')
        logger.debug("Initialising executable")

        # If session is a supported one
        if session_type is not None:
            logger.debug('Detected session type: %s', session_type)
            desktop_tools = tools.get(session_type)
            # If there are tools defined for the current tool_group
            if desktop_tools is not None:
                return Executable.__find_executable(desktop_tools)
            else:
                logger.critical(
                    "Desktop session not supported: %s", session_type
                )
                raise UnsupportedDesktopException
        # If session is not supported, try and make the best
        # guess based on available executables
        else:
            logger.warning(
                "Could not read desktop session type from environment, " +
                "trying to guess based on detected executables"
            )

            # List of available executables
            detected = []
            for desktop, items in tools.items():
                for item in items:
                    if which(item) is not None:
                        detected.append((desktop, item))

            if len(detected) == 0:
                logger.debug("No supported executables found")
                return None

            # List of unique desktop sessions for which executables have
            # been found
            detected_sessions = set([d[0] for d in detected])

            # Available executables are all for the same desktop session
            if len(detected_sessions) == 1:
                return Executable.__find_executable([d[1] for d in detected])

            # If executables are from multiple desktop sessions, the best one
            # can't be picked automatically, as we can't assume the currently
            # running desktop session
            elif len(detected_sessions) > 1:
                logger.warning(
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
