#!/usr/bin/env python
from subprocess import CalledProcessError
from traceback import print_exc
import subprocess as sp
import re


class Session:
    KEY_NAME = "bw_session"

    def __init__(self, auto_lock):
        # Interval in seconds for locking the vault
        self.auto_lock = int(auto_lock) if auto_lock is not None else 900
        self.key = None

    def has_key(self):
        return self.auto_lock != 0 and self.__get_keyid() is not None

    def __get_keyid(self):
        try:
            request_cmd = f"keyctl request user {Session.KEY_NAME}"
            proc = sp.run(request_cmd.split(), check=True, capture_output=True)
            keyid = proc.stdout.decode("utf-8").strip()
            return keyid
        except CalledProcessError:
            return None

    def lock(self):
        try:
            lock_cmd = f"keyctl purge user {Session.KEY_NAME}"
            sp.run(lock_cmd.split(), check=True)
        except CalledProcessError:
            print_exc()
            exit("Failed to delete key from kernel")

    def unlock(self, password):
        try:
            unlock_cmd = f"bw unlock {password}"
            proc = sp.run(unlock_cmd.split(), check=True, capture_output=True)
            output = proc.stdout.decode("utf-8").split("\n")[3]

            regex = r"BW_SESSION=\"(.*==)\""
            self.key = re.search(regex, output).group(1)

            if self.auto_lock != 0:
                keyid = self.__get_keyid()
                if keyid is None:
                    send_cmd = f"echo {self.key}"
                    padd_cmd = f"keyctl padd user {Session.KEY_NAME} @u"
                    proc = sp.Popen(send_cmd.split(), stdout=sp.PIPE)
                    sp.check_output(padd_cmd.split(), stdin=proc.stdout)

        except CalledProcessError:
            print_exc()
            exit("Failed to unlock bitwarden")

    def get_key(self):
        try:
            if self.auto_lock == 0:
                self.lock()

            if self.key is not None:
                return self.key
            elif self.auto_lock != 0:
                keyid = self.__get_keyid()

                refresh_cmd = f"keyctl timeout {keyid} {self.auto_lock}"
                sp.run(refresh_cmd.split(), check=True)

                pipe_cmd = f"keyctl pipe {keyid}"
                proc = sp.run(pipe_cmd.split(),
                              check=True, capture_output=True)

                self.key = proc.stdout.decode("utf-8").strip()
                return self.key
            else:
                exit("Program is in unknown state.")
        except CalledProcessError:
            print_exc()
            exit("Failed to retrieve key")
