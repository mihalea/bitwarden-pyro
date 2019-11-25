#!/usr/bin/env python

from enum import Enum


class KeybindActions(Enum):
    COPY = 'copy'
    PASSWORD = 'passwd'
    ALL = 'all'

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)
