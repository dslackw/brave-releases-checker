#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
import os
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace


@dataclass
class Colors:
    """Represents ANSI escape codes for terminal colors and styles."""
    bold: str = '\033[1m'
    green: str = '\x1b[32m'
    red: str = '\x1b[91m'
    bgreen: str = f'{bold}{green}'
    bred: str = f'{bold}{red}'
    yellow = '\x1b[93m'
    byellow = f'{bold}{yellow}'
    endc: str = '\x1b[0m'


# We use a SimpleNamespace to store the configuration instance.
_CONFIG_INSTANCE = None


def load_config() -> SimpleNamespace:
    """
    Loads configuration settings from a config.ini file, if found.

    It searches for the config file in the following order:
    1. /etc/brave-releases-checker/config.ini
    2. ~/.config/brave-releases-checker/config.ini

    If no config file is found, default settings are used.

    Returns:
        SimpleNamespace: An instance containing the loaded or default settings.
    """
    # We need global to modify the global variable
    global _CONFIG_INSTANCE  # pylint: disable=W0603
    if _CONFIG_INSTANCE:
        return _CONFIG_INSTANCE

    color = Colors()
    config_parser = configparser.ConfigParser()
    config_paths = [
        '/etc/brave-releases-checker/config.ini',
        os.path.expanduser('~/.config/brave-releases-checker/config.ini')
    ]
    found_config_path = None
    config_found = False
    for path in config_paths:
        if os.path.isfile(path):
            found_config_path = path
            config_parser.read(path)
            config_found = True
            break

    if not config_found:
        print(f'{color.bred}Warning:{color.endc} The config file not found. Default settings will be used.')
        _CONFIG_INSTANCE = SimpleNamespace(
            package_path=str(Path('/var/log/packages/')),
            package_name_prefix='brave-browser',
            github_token='',
            download_folder=str(Path(os.path.expanduser('~/Downloads/'))),
            channel='stable',
            asset_suffix='.deb',
            asset_arch='amd64',
            pages='1',
            config_path=found_config_path
        )
    else:
        _CONFIG_INSTANCE = SimpleNamespace(
            package_path=config_parser.get('PACKAGE', 'path', fallback='/var/log/packages/'),
            package_name_prefix=config_parser.get('PACKAGE', 'package_name', fallback='brave-browser'),
            github_token=config_parser.get('GITHUB', 'token', fallback=''),
            download_folder=config_parser.get('DEFAULT', 'download_path', fallback=str(Path(os.path.expanduser('~/Downloads/')))),
            channel=config_parser.get('DEFAULT', 'channel', fallback='stable'),
            asset_suffix=config_parser.get('DEFAULT', 'suffix', fallback='.deb'),
            asset_arch=config_parser.get('DEFAULT', 'arch', fallback='amd64'),
            pages=config_parser.get('DEFAULT', 'pages', fallback='1'),
            config_path=found_config_path
        )
    return _CONFIG_INSTANCE
