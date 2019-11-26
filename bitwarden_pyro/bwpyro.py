from bitwarden_pyro.util.logger import ProjectLogger
from bitwarden_pyro.util.arguments import parse_arguments
from bitwarden_pyro.settings import NAME, VERSION
from bitwarden_pyro.view.rofi import Rofi
from bitwarden_pyro.controller.session import Session, SessionException
from bitwarden_pyro.controller.autotype import AutoType, AutoTypeException
from bitwarden_pyro.controller.clipboard import Clipboard, ClipboardException
from bitwarden_pyro.controller.vault import Vault, VaultException
from bitwarden_pyro.model.actions import ItemActions, WindowActions
from bitwarden_pyro.util.formatter import ItemFormatter, ConverterFactory
from bitwarden_pyro.util.notify import Notify
from bitwarden_pyro.util.config import ConfigLoader

from enum import Enum, auto
from time import sleep
import re


class BwPyro:
    def __init__(self):
        self._rofi = None
        self._session = None
        self._vault = None
        self._clipboard = None
        self._autotype = None
        self._notify = None
        self._args = parse_arguments()
        self._logger = ProjectLogger(self._args.verbose).get_logger()

    def start(self):
        if self._args.version:
            print(f"{NAME} v{VERSION}")
            exit()
        elif self._args.lock:
            self.__lock()
        else:
            self.__launch_ui()

    def __lock(self):
        try:
            self._logger.info("Locking vault and deleting session")
            self._session = Session()
            self._session.lock()
        except SessionException:
            self._logger.error("Failed to lock session")
            self._rofi = Rofi(None, None, None)
            self._rofi.show_error("Failed to lock and delete session")

    def __unlock(self, force=False):
        self._logger.info("Unlocking bitwarden vault")
        if not self._session.has_key() or force:
            pwd = self._rofi.get_password()
            if pwd is not None:
                self._session.unlock(pwd)
            else:
                self._logger.info("Unlocking aborted")
                exit(0)

        k = self._session.get_key()
        self._vault.set_key(k)

    def __show_items(self, prompt):
        items = self._vault.get_items()
        # Convert items to \n separated strings
        formatted = ItemFormatter.unique_format(items)
        selected_name, event = self._rofi.show_items(formatted, prompt)
        self._logger.debug("User selected login: %s", selected_name)

        # Rofi dialog has been closed
        if selected_name is None:
            self._logger.debug("Item selection has been aborted")
            return (None, None)
        # Make sure that the group item isn't a single item where
        # the deduplication marker coincides
        elif selected_name.startswith(ItemFormatter.DEDUP_MARKER) and \
                len(self._vault.get_by_name(selected_name)) == 0:
            self._logger.debug("User selected item group")
            group_name = selected_name[len(ItemFormatter.DEDUP_MARKER):]
            selected_items = self._vault.get_by_name(group_name)

            if isinstance(event, ItemActions):
                event = WindowActions.SHOW_GROUP

            return (event, selected_items)
        # A single item has been selected
        else:
            self._logger.debug("User selected single item")
            selected_item = self._vault.get_by_name(selected_name)
            return (event, selected_item)

    def __show_group_items(self, prompt, items=None, fields=None,
                           ignore=None):
        if items is None:
            items = self._vault.get_items()

        converter = ConverterFactory.create(fields, ignore)
        indexed, formatted = ItemFormatter.group_format(items, converter)
        selected_name, event = self._rofi.show_items(formatted, prompt)

        # Rofi has been closed
        if selected_name is None:
            self._logger.debug("Group item selection has been aborted")
            return (None, None)
        # An item has been selected
        else:
            regex = r"^#([0-9]+): .*"
            match = re.search(regex, selected_name)
            selected_index = int(match.group(1)) - 1
            selected_item = indexed[selected_index]
            return (event, selected_item)

    def __show_folders(self, prompt):
        items = self._vault.get_folders()
        formatted = ItemFormatter.unique_format(items)
        selected_name, event = self._rofi.show_items(formatted, prompt)
        self._logger.info("User selected folder: %s", selected_name)

        if selected_name is None:
            self._logger.debug("Folder selection has been aborted")
            return (None, None)
        else:
            folder = [i for i in items if i['name'] == selected_name][0]

            if folder['name'] == 'No Folder':
                self._logger.debug("Clearing vault folder filter")
                self._vault.set_filter(None)
            else:
                self._vault.set_filter(folder)

            if isinstance(event, ItemActions):
                event = WindowActions.SHOW_NAMES

            return (event, None)

    def __load_items(self):
        try:
            # First attempt at loading items
            count = self._vault.load_items()

            # Second attempt, as key might get invalidated by running bw manually
            if count == 0:
                self._logger.warning(
                    "First attempt at loading vault items failed")
                self.__unlock(force=True)
                count = self._vault.load_items()

            # Last attempt failed, abort execution
            if count == 0:
                self._logger.error(
                    "Aborting execution, as second attempt at " +
                    "loading vault items failed"
                )

                self._rofi.show_error("Failed to load items")
                exit(0)

        except SessionException:
            self._logger.error("Failed to load items")

    def __set_keybinds(self):
        self._enter_action = self._args.enter

        keybinds = {
            'typepassword': ItemActions.PASSWORD,
            'typeall':      ItemActions.ALL,
            'totp':         ItemActions.TOTP,
            'showuris':     WindowActions.SHOW_URI,
            'shownames':    WindowActions.SHOW_NAMES,
            'showlogins':   WindowActions.SHOW_LOGIN,
            'showfolders':  WindowActions.SHOW_FOLDERS,
            'sync':         WindowActions.SYNC
        }

        for name, action in keybinds.items():
            self._rofi.add_keybind(
                self._config.get('keyboard', f'{name}_key'),
                action,
                self._config.get('keyboard', f'{name}_hint'),
            )

    def __launch_ui(self):
        self._logger.info("Application has been launched")
        try:
            self._config = ConfigLoader().get_config(self._args)
            self._session = Session(self._config.getint('security', 'timeout'))
            self._rofi = Rofi(self._args.rofi_args,
                              self._config.get('keyboard', 'enter'),
                              self._config.getboolean('interface', 'hide_mesg'))
            self._clipboard = Clipboard(
                self._config.getint('security', 'clear'))
            self._autotype = AutoType()
            self._vault = Vault()
            self._notify = Notify()

            self.__set_keybinds()
        except (ClipboardException, AutoTypeException,
                SessionException, VaultException):
            self._logger.exception(f"Failed to initialise application")
            exit(1)

        try:

            self.__unlock()
            self.__load_items()

            action = WindowActions.SHOW_NAMES
            while action is not None and isinstance(action, WindowActions):
                self._logger.info("Switch window mode to %s", action)

                prompt = 'Bitwarden'
                if self._vault.has_filter():
                    prompt = self._vault.get_filter()['name']
                    # A group of items has been selected
                if action == WindowActions.SHOW_NAMES:
                    action, item = self.__show_items(
                        prompt=prompt
                    )
                elif action == WindowActions.SHOW_GROUP:
                    action, item = self.__show_group_items(
                        prompt=item[0]['name'],
                        items=item,
                        fields=['login.username']
                    )
                elif action == WindowActions.SHOW_URI:
                    action, item = self.__show_group_items(
                        prompt=prompt,
                        fields=['login.uris.uri'],
                        ignore=['http://', 'https://', 'None']
                    )

                elif action == WindowActions.SHOW_LOGIN:
                    action, item = self.__show_group_items(
                        prompt=prompt,
                        fields=['name', 'login.username']
                    )
                elif action == WindowActions.SYNC:
                    self._vault.sync()
                    self.__load_items()
                    action, item = self.__show_items(
                        prompt=prompt
                    )
                elif action == WindowActions.SHOW_FOLDERS:
                    action, item = self.__show_folders(
                        prompt='Folders'
                    )

            # Selection has been aborted
            if action == None:
                self._logger.info("Exiting. Login selection has been aborted")
                exit(0)

            if action == ItemActions.COPY:
                self._logger.info("Copying password to clipboard")
                self._notify.send(
                    message="Login password copied to clipboard",
                    timeout=self._clipboard.clear * 1000  # convert to ms
                )
                self._clipboard.set(item['login']['password'])
            elif action == ItemActions.ALL:
                self._logger.info("Auto tying username and password")
                self._notify.send(
                    message="Auto typing username and password"
                )
                # Input delay allowing correct window to be focused
                sleep(1)
                self._autotype.string(item['login']['username'])
                sleep(0.2)
                self._autotype.key('Tab')
                sleep(0.2)
                self._autotype.string(item['login']['password'])
            elif action == ItemActions.PASSWORD:
                self._logger.info("Auto typing password")
                self._notify.send(
                    message="Auto typing password"
                )
                # Input delay allowing correct window to be focused
                sleep(1)
                self._autotype.string(item['login']['password'])
            elif action == ItemActions.TOTP:
                self._logger.info("Copying TOTP to clipboard")
                totp = self._vault.get_topt(item['id'])
                if totp is not None:
                    self._notify.send(
                        message="TOTP is copied to the clipboard",
                        timeout=self._clipboard.clear * 1000  # convert to ms
                    )
                    self._clipboard.set(totp)
                else:
                    self._logger.warning(
                        "Selected item does not provide TOTP"
                    )
                    self._rofi.show_error(
                        "Selected item does not provide TOTP"
                    )
            else:
                self._logger.error("Unknown action received: %s", action)
        except (AutoTypeException, ClipboardException,
                SessionException, VaultException):
            self._rofi.show_error("An unexpected error has occurred")
            self._logger.error("Application has received a critical error")


def run():
    bw_pyro = BwPyro()
    bw_pyro.start()
