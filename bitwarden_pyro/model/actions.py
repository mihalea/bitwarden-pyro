from enum import Enum


class BaseActions(Enum):
    """Base enum for actions"""

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)


class ItemActions(BaseActions):
    """Enum for actions that apply to items"""

    COPY = 'copy'
    PASSWORD = 'password'
    ALL = 'all'
    TOTP = 'totp'


class WindowActions(BaseActions):
    """Enum for actions that apply to windows"""

    SYNC = 'sync'
    GROUP = 'group'
    URIS = 'uris'
    NAMES = 'names'
    LOGINS = 'logins'
    FOLDERS = 'folders'
