#!/usr/bin/env python
from subprocess import CalledProcessError
from traceback import print_exc
from shutil import which
from logger import BwLogger
import subprocess as sp
import re


class Session:
    KEY_NAME = "bw_session"
    _logger = None

    def __init__(self, auto_lock):
        # Interval in seconds for locking the vault
        self.auto_lock = int(auto_lock) if auto_lock is not None else 900
        self.key = None

        self._logger = BwLogger().get_logger()
        self.__test_keyctl()

    def __test_keyctl(self):
        if which('keyctl') is None:
            self._logger.error("'keyctl' could not be found on the system")
            exit(0)

    def has_key(self):
        return self.auto_lock != 0 and self.__get_keyid() is not None

    def __get_keyid(self):
        try:
            self._logger.debug("Requesting key id from keyctl")
            request_cmd = f"keyctl request user {self.KEY_NAME}"
            proc = sp.run(request_cmd.split(), check=True, capture_output=True)
            keyid = proc.stdout.decode("utf-8").strip()
            return keyid
        except CalledProcessError:
            self._logger.debug("Key id was not found in keyctl")
            return None

    def lock(self):
        try:
            self._logger.info("Deleting key from keyctl")
            lock_cmd = f"keyctl purge user {self.KEY_NAME}"
            sp.run(lock_cmd.split(), check=True)
        except CalledProcessError:
            self._logger.exception("Failed to delete key from keyctl")
            exit(1)

    def unlock(self, password):
        try:
            self._logger.info("Unlocking bw using password")
            unlock_cmd = f"bw unlock {password}"
            proc = sp.run(unlock_cmd.split(), check=True, capture_output=True)
            output = proc.stdout.decode("utf-8").split("\n")[3]

            regex = r"BW_SESSION=\"(.*==)\""
            self.key = re.search(regex, output).group(1)

            if self.auto_lock != 0:
                self._logger.info("Saving key to keyctl")
                keyid = self.__get_keyid()
                if keyid is None:
                    send_cmd = f"echo {self.key}"
                    padd_cmd = f"keyctl padd user {self.KEY_NAME} @u"
                    proc = sp.Popen(send_cmd.split(), stdout=sp.PIPE)
                    sp.check_output(padd_cmd.split(), stdin=proc.stdout)

        except CalledProcessError:
            self._logger.warning("Failed to unlock bitwarden")

    def get_key(self):
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
                    exit(1)
            else:
                self._logger.critical(
                    "Program is in an unknown state. Exiting..."
                )
                exit(1)
        except CalledProcessError:
            self._logger.critical("Failed to retrieve key")
            exit(1)
