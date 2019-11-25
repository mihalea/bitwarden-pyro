#!/usr/bin/env python

import logging
from bitwarden_pyro.settings import NAME


class SingletonType(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(
                SingletonType, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class BwLogger(object, metaclass=SingletonType):
    _logger = None

    def __init__(self, verbose=None):
        self._logger = logging.getLogger(NAME)
        self._logger.setLevel(logging.DEBUG)

        # create file handler which logs even debug messages
        fh = logging.FileHandler(f'{NAME}.log')
        fh.setLevel(logging.DEBUG)
        # create console handler with a higher log level
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO if not verbose else logging.DEBUG)

        # create formatter and add it to the handlers
        consoleFormatter = None
        fileFormatter = logging.Formatter(
            '%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] - %(message)s'
        )

        if verbose:
            consoleFormatter = fileFormatter
        else:
            consoleFormatter = logging.Formatter(
                '%(asctime)s %(levelname)-8s - %(message)s'
            )

        fh.setFormatter(fileFormatter)
        ch.setFormatter(consoleFormatter)
        # add the handlers to the logger
        self._logger.addHandler(fh)
        self._logger.addHandler(ch)

    def get_logger(self):
        return self._logger
