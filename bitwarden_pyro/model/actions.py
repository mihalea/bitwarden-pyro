#!/usr/bin/env python

from enum import Enum


class BaseActions(Enum):
    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)


class ItemActions(BaseActions):
    COPY = 'copy'
    PASSWORD = 'passwd'
    ALL = 'all'
    TOTP = 'topt'


class WindowActions(BaseActions):
    SYNC = 'sync'
    SHOW_GROUP = 'group'
