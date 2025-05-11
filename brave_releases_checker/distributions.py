#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
from pathlib import Path
from typing import Union

import distro
from packaging import version

from brave_releases_checker.config import Colors, load_config


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
    """

    def __init__(self) -> None:
        config = load_config()
        self.log_packages = Path(config.package_path)
        self.package_name_prefix = config.package_name_prefix
        self.color = Colors()

    def get_slackware(self) -> Union[version.Version, None]:
        """Gets installed version on Slackware."""
        brave_package = list(self.log_packages.glob(f'{self.package_name_prefix}*'))
        if brave_package:
            installed_info = str(brave_package[0]).rsplit('/', maxsplit=1)[-1]
            version_str = installed_info.split('-')[2]
            print(f'Installed Package (Slackware): {installed_info}')
            return version.parse(version_str)
        return None

    def get_debian_dpkg(self) -> Union[version.Version, None]:
        """Gets installed version on Debian-based systems, with fallback to snap on Ubuntu."""
        try:
            process = subprocess.run(['dpkg', '-s', self.package_name_prefix], capture_output=True, text=True, check=True)
            output = process.stdout
            for line in output.splitlines():
                if line.startswith('Version:'):
                    version_str = line.split(':')[-1].strip()
                    print(f'Installed Package (Debian): {self.package_name_prefix} - Version: {version_str}')
                    return version.parse(version_str)
            # If we reach here, dpkg didn't find the package or the Version line
            print(f'Package {self.package_name_prefix} not found or version info missing via dpkg.')
        except subprocess.CalledProcessError:
            print(f'Package {self.package_name_prefix} is not installed on this Debian-based system (via dpkg).')
        except FileNotFoundError:
            print(f'{self.color.bred}Error:{self.color.endc} dpkg command not found.')
            return None  # dpkg not available, cannot proceed with debian check

        # Fallback to snap if on Ubuntu
        if distro.id().lower() == 'ubuntu':
            try:
                subprocess.run(['which', 'snap'], check=True, capture_output=True)
                print('Attempting to get version via snap...')
                return self._get_debian_snap()
            except (subprocess.CalledProcessError, FileNotFoundError):
                print('snap command not found or not available.')
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
                    print(f'Installed Package (Snap): brave - Version: {version_str}')
                    return version.parse(version_str)
            if not version_str:
                print('Could not find installed version information in snap info output.')
                return None
        except subprocess.CalledProcessError as e:
            if "error: unknown snap \'brave\'" in e.stderr:
                print('Brave Browser is not installed as a snap.')
                return None
            print(f'{self.color.bred}Error:{self.color.endc} checking snap package: {e}')
            return None
        except FileNotFoundError:
            print(f'{self.color.bred}Error:{self.color.endc} snap command not found.')
            return None
        return None

    def get_rpm_dnf(self) -> Union[version.Version, None]:
        """Gets installed version on RPM-based systems."""
        process = subprocess.run(['dnf', 'list', self.package_name_prefix], capture_output=True, text=True, check=False)
        if process.returncode == 0:
            output = process.stdout
            for line in output.splitlines():
                if line.startswith(self.package_name_prefix):
                    version_str = line.split()[1].split('-')[0]
                    print(f'Installed Package (RPM): {self.package_name_prefix} - Version: {version_str}')
                    return version.parse(version_str)
        print(f'Package {self.package_name_prefix} not found or version info missing.')
        return None

    def get_arch(self) -> Union[version.Version, None]:
        """Gets installed version on Arch Linux."""
        process = subprocess.run(['pacman', '-Qi', self.package_name_prefix], capture_output=True, text=True, check=True)
        if process.returncode == 0:
            output = process.stdout
            for line in output.splitlines():
                if line.startswith('Version'):
                    version_str = line.split(':')[-1].strip()
                    print(f'Installed Package (Arch): {self.package_name_prefix} - Version: {version_str}')
                    return version.parse(version_str)
        print(f'Package {self.package_name_prefix} not found or version info missing.')
        return None

    def get_opensuse(self) -> Union[version.Version, None]:
        """Gets installed version on openSUSE."""
        process = subprocess.run(['zypper', 'info', self.package_name_prefix], capture_output=True, text=True, check=True)
        if process.returncode == 0:
            output = process.stdout
            for line in output.splitlines():
                if line.startswith('Version'):
                    version_str = line.split(':')[1].split('-')[0].strip()
                    print(f'Installed Package (openSUSE): {self.package_name_prefix} - Version: {version_str}')
                    return version.parse(version_str)
        print(f'Package {self.package_name_prefix} not found or version info missing.')
        return None
