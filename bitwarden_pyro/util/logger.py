import logging

from bitwarden_pyro.settings import NAME


class SingletonType(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(
                SingletonType, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class NoTraceFormatter(logging.Formatter):
    def format(self, record):
        record.message = record.getMessage()
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)
        s = self.formatMessage(record)
        if record.exc_info:
            record.exc_text = f"{record.exc_info[1]} [{record.exc_info[0].__name__}]"
        if record.exc_text:
            if record.exc_text[:2] != " - ":
                record.exc_text = " - " + record.exc_text
            s = s + record.exc_text
        if record.stack_info:
            print(record.stack_info)
        return s


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
        file_formatter = NoTraceFormatter(
            '%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] - %(message)s'
        )

        console_formatter = NoTraceFormatter(
            '%(asctime)s %(levelname)-8s - %(message)s'
        )

        file_handler.setFormatter(file_formatter)
        console_handler.setFormatter(console_formatter)
        # add the handlers to the logger
        self._logger.addHandler(file_handler)
        self._logger.addHandler(console_handler)

    def get_logger(self):
        return self._logger
