import os
import yaml

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from bitwarden_pyro.util.logger import ProjectLogger
from bitwarden_pyro.model.actions import ItemActions, WindowActions
from bitwarden_pyro.settings import NAME


class ConfigLoader:
    _default_values = {
        'security': {
            'timeout': 900,  # Session expiry in seconds
            'clear': 5      # Clipboard persistency in seconds
        },
        'keyboard': {
            'enter': str(ItemActions.COPY),
            'typepassword': {
                'key': 'Alt+1',
                'hint': 'Type password'
            },
            'typeall': {
                'key': 'Alt+2',
                'hint': 'Type all'
            },
            'showuris': {
                'key': 'Alt+u',
                'hint': 'Show URIs'
            },
            'shownames': {
                'key': 'Alt+n',
                'hint': 'Show names'
            },
            'showlogins': {
                'key': 'Alt+l',
                'hint': 'Show logins'
            },
            'showfolders': {
                'key': 'Alt+c',
                'hint': 'Show folders'
            },
            'totp': {
                'key': 'Alt+t',
                'hint': 'totp'
            },
            'sync': {
                'key': 'Alt+r',
                'hint': 'sync'
            }
        },
        'interface': {
            'hide_mesg': False,
            'default_mode': str(WindowActions.SHOW_NAMES)
        }
    }

    _default_path = f'~/.config/{NAME}/config'

    def __init__(self, args):
        self._logger = ProjectLogger().get_logger()
        self._config = None

        self.__init_config(args)
        self.__default_converters()

    def __default_converters(self):
        self.add_converter('int', int)
        self.add_converter('boolean', bool)

    def __init_config(self, args):

        # Load default values from dict
        self._config = self._default_values

        # Command line arguments ovewrite default values and those
        # set by config file
        if not args.no_config:
            self.__from_file(args.config)

        self.__from_args(args)

    def __from_args(self, args):
        if args.timeout is not None:
            self.set('security', 'timeout', args.timeout)
        if args.clear is not None:
            self.set('security', 'clear', args.clear)
        if args.enter is not None:
            self.set('keyboard', 'enter', str(args.enter))

    def __from_file(self, config):
        self._logger.info("Loading config from %s", config)

        if config is None:
            config = self._default_path

        # Resolve to absolute path by either expanding '~' or
        # resolving the relative path
        if config[0] == '~':
            config = os.path.expanduser(config)
        else:
            config = os.path.abspath(config)

        # If theere is no config file at the location specified
        # create one with default values
        if not os.path.isfile(config):
            self.__create_config(config)
        else:
            with open(config, 'r') as f:
                self._config = yaml.load(f, Loader=Loader)

    def __create_config(self, config):
        self._logger.debug("Creating new config from defaults")

        dirname = os.path.dirname(config)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)

        with open(config, 'w') as f:
            yaml.dump(self._config, f, Dumper=Dumper)

    def get(self, section, option):
        options = self._config.get(section)
        if options is None:
            raise ConfigException(f"Section '{section}' could not be found")

        option = options.get(option)
        if option is None:
            raise ConfigException(
                f"Option '{option}' from section '{section}' could not be found"
            )

        return option

    def set(self, section, option, value):
        options = self._config.get(section)
        if options is None:
            raise ConfigException(f"Section '{section}' could not be found")

        options[option] = value

    def add_converter(self, name, converter):
        def getter(self, section, option):
            raw = self.get(section, option)
            return converter(raw)

        getter.__name__ = f"get_{name}"
        setattr(self.__class__, getter.__name__, getter)

    @staticmethod
    def get_default(section, option):
        return ConfigLoader._default_values.get(section).get(option)


class ConfigException(Exception):
    """Base class for exceptions thrown by ConfigLoader"""
