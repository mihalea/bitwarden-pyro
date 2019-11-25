#!/usr/bin/env python

from logger import BwLogger
from arguments import parse_arguments, EnterAction
from settings import NAME, VERSION
from session import Session, SessionException
from rofi import Rofi
from completion import Completion, CompletionException
from vault import Vault, VaultFormatter, VaultException
from enum import Enum, auto
from time import sleep
import re


class ControllerAction(Enum):
    DEFAULT = auto()
    COPY = auto()


class Controller:
    def __init__(self):
        self._rofi = None
        self._completion = None
        self._session = None
        self._vault = None
        self._enter_action = EnterAction.COPY
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

    def __show_items(self):
        items = self._vault.get_items()
        # Convert items to \n separated strings
        formatted = VaultFormatter.unique_format(items)
        selected_name = self._rofi.show_items(formatted)
        self._logger.debug("User selected login: %s", selected_name)

        # Rofi dialog has been closed
        if selected_name is None:
            self._logger.debug("Item selection has been aborted")
            return (None, None)
        # Make sure that the group item isn't a single item where
        # the deduplication marker coincides
        elif selected_name.startswith(VaultFormatter.DEDUP_MARKER) and \
                len(self._vault.get_by_name(selected_name)) == 0:
            self._logger.debug("User selected item group")
            group_name = selected_name[len(VaultFormatter.DEDUP_MARKER):]
            selected_items = self._vault.get_by_name(group_name)
            return (ControllerAction.DEFAULT, selected_items)
        # A single item has been selected
        else:
            self._logger.debug("User selected single item")
            selected_item = self._vault.get_by_name(selected_name)
            return (ControllerAction.DEFAULT, selected_item)

    def __show_group_items(self, items):
        name = items[0]['name']
        formatted = VaultFormatter.group_format(items)
        rofi_selected = self._rofi.show_items(formatted, name)

        # Rofi has been closed
        if rofi_selected is None:
            self._logger.debug("Group item selection has been aborted")
            return (None, None)
        # An item has been selected
        else:
            regex = r"^#([0-9]+): .*"
            match = re.search(regex, rofi_selected)
            selected_index = int(match.group(1)) - 1
            selected_item = items[selected_index]
            return (ControllerAction.DEFAULT, selected_item)

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

        try:
            if not self._session.has_key():
                self.__unlock()

            self.__load_items()

            action, item = self.__show_items()
            # A group of items has been selected
            if action is not None:
                if len(item) == 1:
                    item = item[0]
                elif len(item) > 1:
                    action, item = self.__show_group_items(item)

            # Selection has been aborted
            if action == None:
                self._logger.info("Exiting. Login selection has been aborted")
                exit(0)
            elif action == ControllerAction.DEFAULT:
                action = self._args.enter

            if action == EnterAction.COPY:
                self._logger.info("Copying password to clipboard")
                self._completion.clipboard_set(item['login']['password'])
                if self._args.clear >= 0:
                    self._logger.info("Clearing clipboard")
                    sleep(self._args.clear)
                    self._completion.clipboard_clear()
            elif action == EnterAction.ALL:
                # TODO: Implemention type all action
                pass
            elif action == EnterAction.PASSWORD:
                # TODO: Implement type password action
                pass
            else:
                # TODO: Implement catch all
                pass
        except (CompletionException, SessionException, VaultException):
            self._logger.error("Application has received a critical error")


def main():
    controller = Controller()
    controller.start()


if __name__ == "__main__":
    main()
