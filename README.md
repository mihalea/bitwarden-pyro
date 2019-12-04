# bitwarden-pyro 
![travis-build](https://img.shields.io/travis/com/mihalea/bitwarden-pyro?style=flat-square)
![license](https://img.shields.io/github/license/mihalea/bitwarden-pyro?color=blue&style=flat-square)
![aur-version](https://img.shields.io/aur/version/bitwarden-pyro-git?style=flat-square)
![pypi-version](https://img.shields.io/pypi/v/bitwarden-pyro?style=flat-square)

`bwpyro` is a Bitwarden python interface built on Rofi, allowing for fast selection and insertion of passwords.

## Usage

```
usage: bwpyro [OPTIONS] -- [ROFI OPTIONS]

Rofi-based graphical interface for the official BitWarden CLI

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         increase verbosity level
  -l, --lock            lock vault and delete session key
  -s, --select-window   select and focus window before auto typing
  --hide-mesg           hide message explaining keybinds
  --version             show version information and exit
  --no-config           ignore config files and use default values
  --dump-config         dump the contents of the config data to stdout
  --no-logging          disable logging to file
  --config CONFIG       use a custom config file path
  --cache CACHE         set the time in days it takes for cache to become
                        invalid (default: 7)
  -c CLEAR, --clear CLEAR
                        clear the clipboard after CLEAR seconds (default: 5)
                        use -1 to disable
  -t TIMEOUT, --timeout TIMEOUT
                        automatically lock the vault after TIMEOUT seconds (default: 900)
                        use  0 to lock immediately
                        use -1 to disable
  -e {copy,password,all,totp}, --enter {copy,password,all,totp}
                        action triggered by pressing Enter (default: copy)
                        copy   - copy password to clipboard
                        all    - auto type username and password
                        passwd - auto type password
                        topt   - copy TOPT to clipboard
  -w {uris,logins,names,folders}, --window-mode {uris,logins,names,folders}
                        set the initial window mode (default: names)
```

### Security settings

#### Bitwarden session data
The master password is requested once, and the session key is stored on system using `keyctl`. On subsequent launches, the session key is requested from `keyctl` and the data is decrypted in memory without prompting the user for the password. 

By default, the session data is set to expire after 15 minutes unless refreshed. However it can be set to never expire by setting the timeout to `-1`.

By disabling this feature, the master password will be requested every time.

Usage:
```
// Enabling keyctl storage (default)
$ bwpyro --timeout 900

// Storage without expiration
$ bwpyro --timeout -1

// Disabling keyctl storage
$ bwpyro --timeout 0
```

#### Local item cache

A local item cache can be used to prevent the whole item collection from being decrypted every time. Items are decrypted, stripped of passwords and TOTP data, and stored on disk in a file with permissions set to `0600`. The cache will the used to display items, and only after a selection is made, an individual item will be decrypted using `bw`. 

An expiration interval can be set, which will force the application to sync the item data. By default it is set to 7 days.

The directory where the item cache is stored is `~/.cache/bwpyro/`.

Usage:
```
// Enabling item cache (default)
$ bwpyro --cache 1

// Disabling item cache
$ bwpyro --cache 0
```

#### Logging

The applications' logs can be found in `~/.cache/bwpyro`. They contain a verbose description of the runtime actions and should contain no sensitive information. If logging needs to be disabled, it can be done by launching the application with the `--no-logging` argument.

### Default keybinds
Window modes:
- <kbd>Alt</kbd> + <kbd>C</kbd>: Show folders
- <kbd>Alt</kbd> + <kbd>L</kbd>: Show item logins
- <kbd>Alt</kbd> + <kbd>N</kbd>: Show item names
- <kbd>Alt</kbd> + <kbd>U</kbd>: Show item URIs
- <kbd>Alt</kbd> + <kbd>R</kbd>: Sync Bitwarden

Clipboard:
- <kbd>Enter</kbd>: Copy password to clipbaord
- <kbd>Alt</kbd> + <kbd>T</kbd>: Copy TOPT to clipboard

Auto typing:
- <kbd>Alt</kbd> + <kbd>1</kbd>: Auto type password
- <kbd>Alt</kbd> + <kbd>2</kbd>: Auto type username and password
  
## Configuration

The program expects the configuration file to be present in `~/.config/bwpyro/config`, unless otherwise specified. When no config file can be found in the expected path, a new one will be created using the default values.

### Section: interface

- `interface.hide_mesg`: Hide keybind help message. Expected values: true, false.
- `interface.window_mode`: Default window mode. Expected values: Available options: uris, logins, names, folders.

### Section: security
- `security.cache`: Time in days after which the item cache is set to expire
- `security.clear`: Time in seconds after which the clipboard will be cleared
- `security.timeout`: Time in seconds after which the keyctl session data will be deleted

### Section: autotype
- `autotype.select_window`: Whether to show the window picker before the autotyping procedure
- `autotype.slop_args`: Arguments used to launch slop as window picker used to style the selection
- `autotype.start_delay`: Time delay in seconds before starting the autotype procedure, allowing the window manager to refocus the window
- `autotype.tab_delay`: Time delay in seconds before and after the Tab key, when auto typing both username and password
- `autotype.delay_notification`: Show notification letting the user know the value of autotype.start_delay, before starting the delay
  
### Section: keyboard
- `keyboard.{action}`: Keybind settings for all available actions and modes
  - `.hint`: Contents of the text parts of the help message
  - `.key`: Keybind triggering the action
  - `.show`: Whether to include it in the help message or not

## Installation
An Arch Linux package is available on the AUR: [bitwarden-pyro-git](https://aur.archlinux.org/packages/bitwarden-pyro-git)
```
yay -S bitwarden-pyro-git
```

The package is also available on PyPI: [bitwarden-pyro](https://pypi.org/project/bitwarden-pyro)
```
pip install bitwarden-pyro
```

### Dependencies:
- **rofi**: Display to user interface
- **bitwarden-cli**: Retrieve Bitwarden items
- **keyutils**: Provide `keyctl` caching
- **libnotify**: Show desktop notification

### Optional dependencies
- **xdotool**: Provide auto typing for X11
- **ydotool-git**: Provide auto typing for Wayland
- **xclip**: Provide clipboard interaction with X11
- **xset**: Alternative for clipoard interaction with X11
- **wl-clipboard**: Provide clipboard interaction with Wayland
- **slop**: Provide window selection for auto typing
- **wmctrl**: Provide window focusing for auto typing

### Wayland clipboard

Clipboard interaction requires root access for wayland users, as outlined by [ReimuNotMoe/ydotool](https://github.com/ReimuNotMoe/ydotool):

> This program requires access to /dev/uinput. This usually requires root permissions.

The easiest way of achieving this is by adding the following line to `visudo`:
```
your_username ALL=(ALL) NOPASSWD: /usr/bin/ydotool
```

## License

This software is available under the MIT License

## Credits

This software is based on the idea of Matthias De Bie and his [bitwarden-rofi](https://github.com/mattydebie/bitwarden-rofi), written in Bash.
