#!/usr/bin/env python

from bitwarden_pyro.util.logger import ProjectLogger

from subprocess import CalledProcessError
from shutil import which
import subprocess as sp
import re


class Session:
    KEY_NAME = "bw_session"
    DEFAULT_TIMEOUT = 900

    def __init__(self, auto_lock=None):
        # Interval in seconds for locking the vault
        self.auto_lock = int(auto_lock) \
            if auto_lock is not None else self.DEFAULT_TIMEOUT
        self.key = None

        self._logger = ProjectLogger().get_logger()
        self.__has_executable()

    def __has_executable(self):
        """Check whether the 'keyctl' can be found on the system"""

        if which('keyctl') is None:
            self._logger.error("'keyctl' could not be found on the system")
            return None

    def has_key(self):
        """Return true if the key can be retrieved from system

            The key can be retrieved if auto locking is not zero 
            or keyctl has the session data registered
        """
        return self.auto_lock != 0 and self.__get_keyid() is not None

    def __get_keyid(self):
        """Retrieves key id of session data from keyctl"""
        try:
            self._logger.debug("Requesting key id from keyctl")
            request_cmd = f"keyctl request user {self.KEY_NAME}"
            proc = sp.run(request_cmd.split(), check=True, capture_output=True)
            keyid = proc.stdout.decode("utf-8").strip()
            return keyid
        except CalledProcessError:
            return None

    def lock(self):
        """Delete session data from keyctl

        Raises:
            LockException: Raised when the spawned process returns errors
        """
        try:
            self._logger.info("Deleting key from keyctl and locking bw")
            keyctl_cmd = f"keyctl purge user {self.KEY_NAME}"
            sp.run(keyctl_cmd.split(), check=True, capture_output=True)

            bw_cmd = "bw lock"
            sp.run(bw_cmd.split(), check=True, capture_output=True)
        except CalledProcessError as e:
            self._logger.exception("Failed to delete key from keyctl")
            raise LockException from e

    def unlock(self, password):
        """Unlock bw and store session data in keyctl"""

        try:
            self._logger.info("Unlocking bw using password")

            # Unlock bw vault and retrieve session key
            unlock_cmd = f"bw unlock {password}"
            proc = sp.run(unlock_cmd.split(), check=True, capture_output=True)

            # Extract session key from the process output
            output = proc.stdout.decode("utf-8").split("\n")[3]
            regex = r"BW_SESSION=\"(.*==)\""
            self.key = re.search(regex, output).group(1)

            # Save to keyctl if there is a non-zero lock timeout set
            if self.auto_lock != 0:
                self._logger.info("Saving key to keyctl")
                keyid = self.__get_keyid()
                if keyid is not None:
                    self._logger.info("Overwriting old key")
                send_cmd = f"echo {self.key}"
                padd_cmd = f"keyctl padd user {self.KEY_NAME} @u"
                proc = sp.Popen(send_cmd.split(), stdout=sp.PIPE)
                sp.check_output(padd_cmd.split(), stdin=proc.stdout)
        except CalledProcessError:
            self._logger.warning("Failed to unlock bitwarden")
            raise UnlockException

    def get_key(self):
        """Return the session key from memory or from keyctl"""

        try:
            self._logger.info("Started key retrieval sequence")
            if self.auto_lock == 0:
                self._logger.debug("Force locking vault")
                self.lock()

            if self.key is not None:
                self._logger.debug("Returning key already in memory")
                return self.key
            elif self.auto_lock != 0:
                keyid = self.__get_keyid()

                if keyid is not None:
                    self._logger.debug("Retrieving key from keyctl")
                    refresh_cmd = f"keyctl timeout {keyid} {self.auto_lock}"
                    sp.run(refresh_cmd.split(), check=True)

                    pipe_cmd = f"keyctl pipe {keyid}"
                    proc = sp.run(pipe_cmd.split(),
                                  check=True, capture_output=True)

                    self.key = proc.stdout.decode("utf-8").strip()
                    return self.key
                else:
                    self._logger.error("Key was not found in keyctl")
                    raise KeyReadException
            else:
                self._logger.critical(
                    "Program is in an unknown state. Exiting..."
                )
                raise KeyReadException
        except CalledProcessError as e:
            self._logger.error("Failed to retrieve key")
            raise KeyReadException from e


class SessionException(Exception):
    """Base exception for all errors raised by Session"""
    pass


class LockException(SessionException):
    """Raised when an issue occurs when trying to lock the vault"""
    pass


class UnlockException(SessionException):
    """Raised when an issue occurs when trying to unlock the vault"""
    pass


class KeyReadException(SessionException):
    """Raised when reading the key from keyctl fails"""
    pass
