import subprocess as sp

from subprocess import CalledProcessError
from shutil import which

from bitwarden_pyro.util.logger import ProjectLogger


class Focus:
    """Select and focus specific windows"""

    def __init__(self, enabled, arguments):
        self._logger = ProjectLogger().get_logger()
        self._enabled = enabled
        self._arguments = arguments

        self.__check_execs()

        if self._enabled:
            self._logger.info("Focus has been enabled")

    def __check_execs(self):
        execs = ('slop', 'wmctrl')
        for exec_name in execs:
            if which(exec_name) is None:
                self._logger.warning(
                    "Disabling Focus, '%s' is not installed",
                    exec_name
                )
                self.enabled = False

    def __select_window(self):
        self._logger.debug("Selecting window")
        cmd = "slop -f %i -t 999999"
        if self._arguments is not None:
            cmd += f" {self._arguments}"

        proc = sp.run(cmd.split(), check=False, capture_output=True)

        if proc.returncode != 0:
            return None

        return proc.stdout.decode("utf-8")

    def __focus_window(self, window_id):
        try:
            self._logger.debug("Focusing window: %s", window_id)
            cmd = f"wmctrl -i -a {window_id}"
            sp.run(cmd.split(), check=True, capture_output=True)
        except CalledProcessError:
            raise FocusException("Failed to focus window")

    def select_window(self):
        """Select and focus a window with slop and wmctrl"""

        if not self._enabled:
            self._logger.debug("Select window functionality is not enabled")
            return

        window_id = self.__select_window()

        if window_id is None:
            self._logger.info("Window selection has been aborted")
            return False

        self.__focus_window(window_id)
        return True

    def is_enabled(self):
        """Return True if feature is enabled"""

        return self._enabled


class FocusException(Exception):
    """Base exception raised by Focus class"""
