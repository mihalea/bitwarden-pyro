from enum import Enum


class BaseActions(Enum):
    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        if isinstance(other, str):
            string = str(self)
            return string == other
        else:
            return super(BaseActions, self).__eq__(other)


class ItemActions(BaseActions):
    COPY = 'copy'
    PASSWORD = 'passwd'
    ALL = 'all'
    TOTP = 'totp'


class WindowActions(BaseActions):
    SYNC = 'sync'
    SHOW_GROUP = 'group'
    SHOW_URI = 'show_uri'
    SHOW_NAMES = 'show_names'
    SHOW_LOGIN = 'show_login'
    SHOW_FOLDERS = 'show_folders'
