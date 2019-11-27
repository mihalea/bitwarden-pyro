import logging

from bitwarden_pyro.settings import NAME


class SingletonType(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(
                SingletonType, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class ProjectLogger(object, metaclass=SingletonType):
    _logger = None

    def __init__(self, verbose=None):
        self._logger = logging.getLogger(NAME)
        self._logger.setLevel(logging.DEBUG)

        # create file handler which logs even debug messages
        file_handler = logging.FileHandler(f'{NAME}.log')
        file_handler.setLevel(logging.DEBUG)
        # create console handler with a higher log level
        console_handler = logging.StreamHandler()
        console_handler.setLevel(
            logging.INFO if not verbose else logging.DEBUG)

        # create formatter and add it to the handlers
        console_formatter = None
        file_formatter = logging.Formatter(
            '%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] - %(message)s'
        )

        if verbose:
            console_formatter = file_formatter
        else:
            console_formatter = logging.Formatter(
                '%(asctime)s %(levelname)-8s - %(message)s'
            )

        file_handler.setFormatter(file_formatter)
        console_handler.setFormatter(console_formatter)
        # add the handlers to the logger
        self._logger.addHandler(file_handler)
        self._logger.addHandler(console_handler)

    def get_logger(self):
        return self._logger
