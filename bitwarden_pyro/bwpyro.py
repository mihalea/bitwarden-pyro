from time import sleep

import re
import sys
import logging

from bitwarden_pyro.util.logger import ProjectLogger
from bitwarden_pyro.util.arguments import parse_arguments
from bitwarden_pyro.settings import NAME, VERSION
from bitwarden_pyro.view.rofi import Rofi
from bitwarden_pyro.controller.session import Session, SessionException
from bitwarden_pyro.controller.autotype import AutoType, AutoTypeException
from bitwarden_pyro.controller.clipboard import Clipboard, ClipboardException
from bitwarden_pyro.controller.vault import Vault, VaultException
from bitwarden_pyro.model.actions import ItemActions, WindowActions
from bitwarden_pyro.util.formatter import ItemFormatter, create_converter
from bitwarden_pyro.util.notify import Notify
from bitwarden_pyro.util.config import ConfigLoader, ConfigException
from bitwarden_pyro.controller.cache import CacheException
from bitwarden_pyro.controller.focus import Focus, FocusException


class FlowException(Exception):
    """Exceptions raised during the main loop"""


class BwPyro:
    """
    Start and control the execution of the program
    """

    def __init__(self):
        self._rofi = None
        self._session = None
        self._vault = None
        self._clipboard = None
        self._autotype = None
        self._notify = None
        self._config = None
        self._focus = None
        self._args = parse_arguments()
        self._logger = ProjectLogger(
            self._args.verbose, not self._args.no_logging
        ).get_logger()

    def start(self):
        """Start the execution of the program"""

        if self._args.version:
            print(f"{NAME} v{VERSION}")
            sys.exit()
        elif self._args.lock:
            self.__lock()
        elif self._args.dump_config:
            self.__dump_config()
        else:
            self.__launch_ui()

    def __dump_config(self):
        try:
            self._logger.setLevel(logging.ERROR)
            self._config = ConfigLoader(self._args)
            dump = self._config.dump()
            print(dump)
        except ConfigException:
            self._logger.exception("Failed to dump config")

    def __lock(self):
        try:
            self._logger.info("Locking vault and deleting session")
            self._session = Session()
            self._session.lock()
        except SessionException:
            self._logger.exception("Failed to lock session")
            self._rofi = Rofi(None, None, None)
            self._rofi.show_error("Failed to lock and delete session")

    def __unlock(self, force=False):
        self._logger.info("Unlocking bitwarden vault")
        if force or not self._session.has_key():
            pwd = self._rofi.get_password()
            if pwd is not None:
                self._session.unlock(pwd)
            else:
                self._logger.info("Unlocking aborted")
                sys.exit(0)

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
        if selected_name.startswith(ItemFormatter.DEDUP_MARKER) and \
                len(self._vault.get_by_name(selected_name)) == 0:
            self._logger.debug("User selected item group")
            group_name = selected_name[len(ItemFormatter.DEDUP_MARKER):]
            selected_items = self._vault.get_by_name(group_name)

            if isinstance(event, ItemActions):
                event = WindowActions.GROUP

            return (event, selected_items)

        # A single item has been selected
        self._logger.debug("User selected single item")
        selected_item = self._vault.get_by_name(selected_name)
        return (event, selected_item)

    def __show_indexed_items(self, prompt, items=None, fields=None,
                             ignore=None):
        if items is None:
            items = self._vault.get_items()

        converter = create_converter(fields, ignore)
        indexed, formatted = ItemFormatter.group_format(items, converter)
        selected_name, event = self._rofi.show_items(formatted, prompt)

        # Rofi has been closed
        if selected_name is None:
            self._logger.debug("Group item selection has been aborted")
            return (None, None)

    # An item has been selected
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

        folder = [i for i in items if i['name'] == selected_name][0]

        if folder['name'] == 'No Folder':
            self._logger.debug("Clearing vault folder filter")
            self._vault.set_filter(None)
        else:
            self._vault.set_filter(folder)

        if isinstance(event, ItemActions):
            event = WindowActions.NAMES

        return (event, None)

    def __load_items(self, use_cache=True):
        try:
            # First attempt at loading items
            self._vault.load_items(use_cache)
        except VaultException:
            self._logger.warning(
                "First attempt at loading vault items failed"
            )

            self.__unlock(force=True)
            self._vault.load_items(use_cache)

    def __set_keybinds(self):
        keybinds = {
            'type_password': ItemActions.PASSWORD,
            'type_all':      ItemActions.ALL,
            'copy_totp':         ItemActions.TOTP,
            'mode_uris':     WindowActions.URIS,
            'mode_names':    WindowActions.NAMES,
            'mode_logins':   WindowActions.LOGINS,
            'mode_folders':  WindowActions.FOLDERS,
            'sync':         WindowActions.SYNC
        }

        for name, action in keybinds.items():
            self._rofi.add_keybind(
                self._config.get(f'keyboard.{name}.key'),
                action,
                self._config.get(f'keyboard.{name}.hint'),
                self._config.get(f'keyboard.{name}.show'),
            )

    def __init_ui(self):
        try:
            self._config = ConfigLoader(self._args)
            self._session = Session(
                self._config.get_int('security.timeout'))
            self._rofi = Rofi(self._args.rofi_args,
                              self._config.get_itemaction('keyboard.enter'),
                              self._config.get_boolean('interface.hide_mesg'))
            self._clipboard = Clipboard(
                self._config.get_int('security.clear'))
            self._autotype = AutoType()
            self._vault = Vault(self._config.get_int('security.cache'))
            self._notify = Notify()
            self._focus = Focus(
                self._config.get_boolean('autotype.select_window'),
                self._config.get('autotype.slop_args')
            )

            self.__set_keybinds()
        except (ClipboardException, AutoTypeException, CacheException,
                SessionException, VaultException, ConfigException):
            self._logger.exception("Failed to initialise application")
            sys.exit(1)

    def __display_windows(self):
        action = self._config.get_windowaction('interface.window_mode')
        while action is not None and isinstance(action, WindowActions):
            self._logger.info("Switch window mode to %s", action)

            prompt = 'Bitwarden'
            if self._vault.has_filter():
                prompt = self._vault.get_filter()['name']
                # A group of items has been selected
            if action == WindowActions.NAMES:
                action, item = self.__show_items(
                    prompt=prompt
                )
            elif action == WindowActions.GROUP:
                action, item = self.__show_indexed_items(
                    prompt=item[0]['name'],
                    items=item,
                    fields=['login.username']
                )
            elif action == WindowActions.URIS:
                action, item = self.__show_indexed_items(
                    prompt=prompt,
                    fields=['login.uris.uri'],
                    ignore=['http://', 'https://', 'None']
                )

            elif action == WindowActions.LOGINS:
                action, item = self.__show_indexed_items(
                    prompt=prompt,
                    fields=['name', 'login.username']
                )
            elif action == WindowActions.SYNC:
                self._vault.sync()
                self.__load_items(use_cache=False)
                action, item = self.__show_items(
                    prompt=prompt
                )
            elif action == WindowActions.FOLDERS:
                action, item = self.__show_folders(
                    prompt='Folders'
                )

        return action, item

    def __delay_type(self):
        # Delay typing, allowing correct window to be focused
        if self._focus.is_enabled():
            okay = self._focus.select_window()
            if not okay:
                self._logger.warning("Focus has been cancelled")
                sys.exit(0)
        else:
            start_delay = self._config.get_int('autotype.start_delay')
            focus_notification = self._config.get_boolean(
                'autotype.delay_notification'
            )

            if focus_notification:
                self._notify.send(
                    message=f"Waiting {start_delay} second(s) for window to refocus",
                    timeout=start_delay * 1000  # Convert to ms
                )
            sleep(start_delay)

    def __execute_action(self, action, item):
        if action == ItemActions.COPY:
            self._logger.info("Copying password to clipboard")
            # Get item with password
            item = self._vault.get_item_full(item)
            self._notify.send(
                message="Login password copied to clipboard",
                timeout=self._clipboard.clear * 1000  # convert to ms
            )
            self._clipboard.set(item['login']['password'])
        elif action == ItemActions.ALL:
            self._logger.info("Auto tying username and password")
            # Get item with password
            item = self._vault.get_item_full(item)

            self.__delay_type()

            self._notify.send(
                message="Auto typing username and password"
            )

            tab_delay = self._config.get_float('autotype.tab_delay')
            self._autotype.string(item['login']['username'])
            sleep(tab_delay)
            self._autotype.key('Tab')
            sleep(tab_delay)
            self._autotype.string(item['login']['password'])
        elif action == ItemActions.PASSWORD:
            self._logger.info("Auto typing password")
            # Get item with password
            item = self._vault.get_item_full(item)

            self.__delay_type()

            self._notify.send(
                message="Auto typing password"
            )

            self._autotype.string(item['login']['password'])
        elif action == ItemActions.TOTP:
            self._logger.info("Copying TOTP to clipboard")
            totp = self._vault.get_item_topt(item)
            self._notify.send(
                message="TOTP is copied to the clipboard",
                timeout=self._clipboard.clear * 1000  # convert to ms
            )
            self._clipboard.set(totp)
        else:
            self._logger.error("Unknown action received: %s", action)

    def __launch_ui(self):
        self._logger.info("Application has been launched")

        self.__init_ui()

        try:
            self.__unlock()
            self.__load_items()

            action, item = self.__display_windows()

            # Selection has been aborted
            if action is None:
                self._logger.info("Exiting. Login selection has been aborted")
                sys.exit(0)

            self.__execute_action(action, item)

        except (AutoTypeException, ClipboardException,
                SessionException, VaultException, FocusException) as exc:
            self._logger.exception("Application has received a critical error")
            self._rofi.show_error(f"An error has occurred. {exc}")


def run():
    """Initialise the program controller"""

    bw_pyro = BwPyro()
    bw_pyro.start()
