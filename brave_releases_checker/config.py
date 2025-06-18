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
    bold: str = '\x1b[1m'
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
    for path in config_paths:
        if os.path.isfile(path):
            found_config_path = path
            config_parser.read(path)
            break

    # Define default log file directory here, as it's common for both cases
    default_log_dir = os.path.expanduser('~/.local/share/brave_checker/logs/')
    # Define default notification timeout here
    default_notification_timeout = 5000  # 5 seconds
    # Default Wget options
    default_wget_options = "-c -q --tries=3 --progress=bar:force:noscroll --show-progress"

    if not found_config_path:
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
            log_file_dir=default_log_dir,
            notification_timeout=5000,
            wget_options=default_wget_options,
            config_path=found_config_path,
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
            log_file_dir=config_parser.get('DAEMON', 'log_path', fallback=default_log_dir),
            notification_timeout=config_parser.getint('DAEMON', 'notification_timeout', fallback=default_notification_timeout),
            wget_options=config_parser.get('DOWNLOAD', 'wget_options', fallback=default_wget_options),
            config_path=found_config_path
        )
    return _CONFIG_INSTANCE
