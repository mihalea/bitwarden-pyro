from bitwarden_pyro.util.logger import ProjectLogger
from bitwarden_pyro.model.actions import ItemActions, WindowActions
from bitwarden_pyro.settings import NAME

import configparser
import os


class ConfigLoader:
    _default_values = {
        'security': {
            'timeout': 900,  # Session expiry in seconds
            'clear': 5      # Clipboard persistency in seconds
        },
        'keyboard': {
            'enter':                ItemActions.COPY,
            'typepassword_key':     'Alt+1',
            'typepassword_hint':    'Type password',
            'typeall_key':          'Alt+2',
            'typeall_hint':         'Type all',
            'showuris_key':         'Alt+u',
            'showuris_hint':        'Show URIs',
            'shownames_key':        'Alt+n',
            'shownames_hint':       'Show names',
            'showlogins_key':       'Alt+l',
            'showlogins_hint':      'Show logins',
            'showfolders_key':      'Alt+c',
            'showfolders_hint':     'Show folders',
            'totp_key':             'Alt+t',
            'totp_hint':            'totp',
            'sync_key':             'Alt+r',
            'sync_hint':            'sync'
        },
        'interface': {
            'hide_mesg': False,
            'default_mode': WindowActions.SHOW_NAMES
        }
    }

    _default_path = f'~/.config/{NAME}/config'

    def __init__(self):
        self._logger = ProjectLogger().get_logger()

    def get_config(self, args):
        parser = configparser.SafeConfigParser()

        # Read default values from dict
        parser.read_dict(self._default_values)

        # Command line arguments ovewrite default values and those
        # set by config file
        if not args.no_config:
            self.__from_file(parser, args.config)
        self.__from_args(parser, args)

        return parser

    def __from_args(self, parser, args):
        if args.timeout is not None:
            parser.set('security', 'timeout', args.timeout)
        if args.clear is not None:
            parser.set('security', 'clear', args.clear)
        if args.enter is not None:
            parser.set('keyboard', 'enter', str(args.enter))

    def __from_file(self, parser, config):
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
            self.__create_config(parser, config)
        else:
            parser.read(config)

    def __create_config(self, parser, config):
        self._logger.debug("Creating new config from defaults")

        dirname = os.path.dirname(config)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)

        with open(config, 'w') as f:
            parser.write(f)

    @staticmethod
    def get_default(section, option):
        return ConfigLoader._default_values.get(section).get(option)
