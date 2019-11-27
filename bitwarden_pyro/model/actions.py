from enum import Enum


class BaseActions(Enum):
    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)


class ItemActions(BaseActions):
    COPY = 'copy'
    PASSWORD = 'password'
    ALL = 'all'
    TOTP = 'totp'


class WindowActions(BaseActions):
    SYNC = 'sync'
    GROUP = 'group'
    URIS = 'uris'
    NAMES = 'names'
    LOGINS = 'logins'
    FOLDERS = 'folders'
