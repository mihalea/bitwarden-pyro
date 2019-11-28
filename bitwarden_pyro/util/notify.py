from subprocess import CalledProcessError

import subprocess as sp
import os
import pkg_resources

from bitwarden_pyro.util.logger import ProjectLogger


class Notify:
    """Send desktop notifications using notify-send"""

    def __init__(self, icons=None):
        self._logger = ProjectLogger().get_logger()
        self._icon = self.__find_icon(icons)

    def __find_icon(self, icons):
        if icons is not None:
            for icon in icons:
                if os.path.isfile(icon):
                    self._logger.debug("Found a valid icon: %s", icon)
                    return icon

        # Use internal fallback icon
        path = pkg_resources.resource_filename(
            'bitwarden_pyro.resources', 'icon.svg'
        )
        self._logger.debug("Using fallback icon: %s", path)
        return path

    def send(self, message, title='Bitwarden Pyro', timeout=None):
        """Send a dekstop notification"""

        try:
            self._logger.debug("Sending desktop notification")
            cmd = ['notify-send', title, message]

            if timeout is not None:
                cmd.extend(['--expire-time', f"{timeout}"])

            if self._icon is not None:
                cmd.extend(['--icon', self._icon])

            sp.run(cmd, check=True, capture_output=True)
        except CalledProcessError:
            raise NotifyException("Failed to send notification message")


class NotifyException(Exception):
    """Base exception for errors raised by Notify"""
