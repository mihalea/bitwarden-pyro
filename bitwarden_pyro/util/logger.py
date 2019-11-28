import logging
import os

from logging.handlers import RotatingFileHandler

from bitwarden_pyro.settings import NAME


class SingletonType(type):
    """Prevent multiple instances from being created"""
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(
                SingletonType, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class NoTraceFormatter(logging.Formatter):
    """Logging formatter with custom error information and no trace stacks"""

    def format(self, record):
        record.message = record.getMessage()
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)
        string = self.formatMessage(record)
        if record.exc_info:
            record.exc_text = f"{record.exc_info[1]} [{record.exc_info[0].__name__}]"
        if record.exc_text:
            if record.exc_text[:2] != " - ":
                record.exc_text = " - " + record.exc_text
            string = string + record.exc_text
        if record.stack_info:
            print(record.stack_info)
        return string


class ProjectLogger(metaclass=SingletonType):
    """Single logger object handling printing for project"""

    _logger = None

    def __init__(self, verbose=None, file_logging=True):
        self._logger = logging.getLogger(NAME)
        self._logger.setLevel(logging.DEBUG)

        path = os.path.expanduser(f'~/.cache/{NAME}/{NAME}.log')
        dirname = os.path.dirname(path)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)

        if file_logging:
            # create file handler which logs even debug messages
            file_handler = RotatingFileHandler(
                path,
                maxBytes=1024000,  # 1 MB
                backupCount=3
            )
            file_handler.setLevel(logging.DEBUG)

            # create formatter and add it to the handlers
            file_formatter = NoTraceFormatter(
                '%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] - %(message)s'
            )

            file_handler.setFormatter(file_formatter)
            self._logger.addHandler(file_handler)

        # create console handler with a higher log level
        console_handler = logging.StreamHandler()
        console_handler.setLevel(
            logging.INFO if not verbose else logging.DEBUG
        )

        console_formatter = NoTraceFormatter(
            '%(asctime)s %(levelname)-8s - %(message)s'
        )

        console_handler.setFormatter(console_formatter)
        self._logger.addHandler(console_handler)

    def get_logger(self):
        """Return the Python logger object"""

        return self._logger
