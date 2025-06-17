#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import logging
import subprocess
from pathlib import Path
from typing import Union

import distro
from packaging import version

from brave_releases_checker.config import Colors, load_config

logger = logging.getLogger('BraveCheckerDaemon')


class InstalledVersion:

    """
    A class responsible for detecting the installed Brave Browser version
    on various operating systems.

    Attributes:
        log_packages (Path): The path to the directory where package information
                             might be stored.
        package_name_prefix (str): The expected prefix of the Brave Browser
                                   package name (read from configuration).
        color (Colors): An instance of the Colors class for colored output.
        logger (logging.Logger): The logger instance for recording events.
    """

    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        config = load_config()
        self.log_packages = Path(config.package_path)
        self.package_name_prefix = config.package_name_prefix
        self.color = Colors()
        self.logger = logger

    def _output_message(self, message: str, level: str = 'info', color_code: str = '') -> None:
        """
        Handles printing to console or logging based on daemon mode and log level.

        Args:
            message (str): The message to output.
            level (str): The logging level ('info', 'warning', 'error').
            color_code (str): ANSI color code for console output.
        """
        if self.args.daemon:
            if level == 'info':
                self.logger.info(message)
            elif level == 'warning':
                self.logger.warning(message)
            elif level == 'error':
                self.logger.error(message)
            else:   # Fallback for unknown levels in daemon mode
                self.logger.debug("Unknown log level '%s' for message: %s", level, message)
        else:
            # Apply color only for console output
            print(f"{color_code}{message}{self.color.endc}" if color_code else message)

    def get_slackware(self) -> Union[version.Version, None]:
        """Gets installed version on Slackware."""
        brave_package = list(self.log_packages.glob(f'{self.package_name_prefix}*'))
        if brave_package:
            installed_info = str(brave_package[0]).rsplit('/', maxsplit=1)[-1]
            version_str = installed_info.split('-')[2]
            self._output_message(f'Installed Package (Slackware): {installed_info}')
            return version.parse(version_str)
        self._output_message("Brave Browser package not found for Slackware.", level='info')  # Use info for "not found" which isn't an error
        return None

    def get_debian_dpkg(self) -> Union[version.Version, None]:
        """Gets installed version on Debian-based systems, with fallback to snap on Ubuntu."""
        try:
            process = subprocess.run(['dpkg', '-s', self.package_name_prefix], capture_output=True, text=True, check=True)
            output = process.stdout
            for line in output.splitlines():
                if line.startswith('Version:'):
                    version_str = line.split(':')[-1].strip()
                    self._output_message(f'Installed Package (Debian): {self.package_name_prefix} - Version: {version_str}')
                    return version.parse(version_str)
            self._output_message(f'Package {self.package_name_prefix} not found or version info missing via dpkg.', level='warning')
        except subprocess.CalledProcessError:
            self._output_message(f'Package {self.package_name_prefix} is not installed on this Debian-based system (via dpkg).', level='info')
        except FileNotFoundError:
            self._output_message('dpkg command not found.', level='error', color_code=self.color.bred)
            return None

        if distro.id().lower() == 'ubuntu':
            try:
                subprocess.run(['which', 'snap'], check=True, capture_output=True)
                self._output_message('Attempting to get version via snap...')
                return self._get_debian_snap()
            except (subprocess.CalledProcessError, FileNotFoundError):
                self._output_message('snap command not found or not available.', level='warning')
                return None

        return None

    def _get_debian_snap(self) -> Union[version.Version, None]:
        """Gets installed version on systems with snapd where Brave is installed as a snap."""
        try:
            process = subprocess.run(['snap', 'info', 'brave'], capture_output=True, text=True, check=True)
            output = process.stdout
            version_str = None
            for line in output.splitlines():
                if line.startswith('installed:'):
                    version_str = line.split()[1]
                    self._output_message(f'Installed Package (Snap): brave - Version: {version_str}')
                    return version.parse(version_str)
            if not version_str:
                self._output_message('Could not find installed version information in snap info output.', level='warning')
                return None
        except subprocess.CalledProcessError as e:
            if "error: unknown snap 'brave'" in e.stderr:
                self._output_message('Brave Browser is not installed as a snap.', level='info')
                return None
            self._output_message(f'Error checking snap package: {e}', level='error', color_code=self.color.bred)
            return None
        except FileNotFoundError:
            self._output_message('snap command not found.', level='error', color_code=self.color.bred)
            return None
        return None

    def get_rpm_dnf(self) -> Union[version.Version, None]:
        """Gets installed version on RPM-based systems."""
        process = subprocess.run(['dnf', 'list', self.package_name_prefix], capture_output=True, text=True, check=False)
        if process.returncode == 0:
            output = process.stdout
            for line in output.splitlines():
                if line.startswith(self.package_name_prefix):
                    version_str = line.split()[1].split('-')[0].strip()
                    self._output_message(f'Installed Package (RPM): {self.package_name_prefix} - Version: {version_str}')
                    return version.parse(version_str)
        self._output_message(f'Package {self.package_name_prefix} not found or version info missing via dnf.', level='warning')
        return None

    def get_arch(self) -> Union[version.Version, None]:
        """Gets installed version on Arch Linux."""
        try:
            process = subprocess.run(['pacman', '-Qi', self.package_name_prefix], capture_output=True, text=True, check=True)
            if process.returncode == 0:
                output = process.stdout
                for line in output.splitlines():
                    if line.startswith('Version'):
                        version_str = line.split(':')[-1].strip()
                        self._output_message(f'Installed Package (Arch): {self.package_name_prefix} - Version: {version_str}')
                        return version.parse(version_str)
            self._output_message(f'Package {self.package_name_prefix} not found or version info missing via pacman.', level='warning')
        except subprocess.CalledProcessError:
            self._output_message(f"Package {self.package_name_prefix} not found via pacman.", level='info')
        except FileNotFoundError:
            self._output_message("pacman command not found.", level='error', color_code=self.color.bred)
        return None

    def get_opensuse(self) -> Union[version.Version, None]:
        """Gets installed version on openSUSE."""
        process = subprocess.run(['zypper', 'info', self.package_name_prefix], capture_output=True, text=True, check=False)
        if process.returncode == 0:
            output = process.stdout
            for line in output.splitlines():
                if line.startswith('Version'):
                    version_str = line.split(':')[1].split('-')[0].strip()
                    self._output_message(f'Installed Package (openSUSE): {self.package_name_prefix} - Version: {version_str}')
                    return version.parse(version_str)
        self._output_message(f'Package {self.package_name_prefix} not found or version info missing via zypper.', level='warning')
        return None
