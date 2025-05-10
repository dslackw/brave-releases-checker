#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Union


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


@dataclass
class Config:  # pylint: disable=[R0902]
    """
    Represents the configuration settings for the Brave Release Checker.

    Attributes:
        package_path (Path): The default path to the directory containing installed package information.
        package_name_prefix (str): The prefix of the Brave Browser package name.
        github_token (str): The GitHub API token for authenticated requests (optional).
        download_folder (Path): The default path to download new releases.
        config_path (Union[str, None]): The path to the loaded configuration file, if found.
    """
    package_path: Path = Path('/var/log/packages/')
    package_name_prefix: str = 'brave-browser'
    github_token: str = ''
    download_folder: Path = Path(os.path.expanduser('~/Downloads/'))
    channel: str = 'stable'
    asset_suffix: str = '.deb'
    asset_arch: str = 'amd64'
    pages: str = '1'
    config_path: Union[str, None] = None


def load_config() -> Config:
    """
    Loads configuration settings from a config.ini file, if found.

    It searches for the config file in the following order:
    1. /etc/brave-releases-checker/config.ini
    2. ~/.config/brave-releases-checker/config.ini

    If no config file is found, default settings are used.

    Returns:
        Config: An instance of the Config dataclass containing the loaded or default settings.
    """
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
        return Config(config_path=found_config_path)

    download_path_from_config = config_parser.get('DEFAULT', 'download_path', fallback=None)
    return Config(
        package_path=Path(config_parser.get('PACKAGE', 'path', fallback='/var/log/packages/')),
        package_name_prefix=config_parser.get('PACKAGE', 'package_name', fallback='brave-browser'),
        github_token=config_parser.get('GITHUB', 'token', fallback=''),
        download_folder=Path(download_path_from_config) if download_path_from_config else Path(os.path.expanduser('~/Downloads/')),
        channel=config_parser.get('DEFAULT', 'channel', fallback='stable'),
        asset_suffix=config_parser.get('DEFAULT', 'suffix', fallback='.deb'),
        asset_arch=config_parser.get('DEFAULT', 'arch', fallback='amd64'),
        pages=config_parser.get('DEFAULT', 'pages', fallback='1'),
        config_path=found_config_path
    )
