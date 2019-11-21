#!/usr/bin/env python

from logger import BwLogger
from arguments import parse_arguments
from settings import NAME, VERSION
from session import Session, SessionException
from rofi import Rofi
from completion import Completion, CompletionException
from vault import Vault, VaultException


class Controller:
    def __init__(self):
        self._rofi = None
        self._completion = None
        self._session = None
        self._vault = None
        self._args = parse_arguments()
        self._logger = BwLogger(self._args.verbose).get_logger()

    def start(self):
        if self._args.version:
            print(f"{NAME} v{VERSION}")
            exit()
        else:
            self.__launch_ui()

    def __unlock(self):
        pwd = self._rofi.get_password()
        if pwd is not None:
            self._session.unlock(pwd)
        else:
            self._logger.info("Unlocking aborted")
            exit(0)

    def __load_items(self):
        try:
            k = self._session.get_key()

            # First attempt at loading items
            count = self._vault.load_items(k)

            # Second attempt, as key might get invalidated by running bw manually
            if count == 0:
                self._logger.warning(
                    "First attempt at loading vault items failed")
                self.__unlock()
                k = self._session.get_key()
                count = self._vault.load_items(k)

            # Last attempt failed, abort execution
            if count == 0:
                self._logger.error(
                    "Aborting execution, as second attempt at " +
                    "loading vault items failed"
                )
                exit(0)
        except SessionException:
            self._logger.error("Failed to load items")

    def __launch_ui(self):
        self._logger.info("Application has been launched")
        try:
            self._session = Session(self._args.timeout)
            self._rofi = Rofi()
            self._completion = Completion()
            self._vault = Vault()
        except (CompletionException, SessionException, VaultException):
            self._logger.exception(f"Failed to initialise application")
            exit(1)

        if not self._session.has_key():
            self.__unlock()

        self.__load_items()


def main():
    controller = Controller()
    controller.start()


if __name__ == "__main__":
    main()
