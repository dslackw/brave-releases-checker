#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import configparser
import os
import subprocess
import sys
from pathlib import Path
from typing import Union

import distro
import requests
from packaging import version

# COLORS
BOLD = '\033[1m'
GREEN = '\x1b[32m'
BGREEN = f'{BOLD}{GREEN}'
ENDC = '\x1b[0m'


class BraveReleaseChecker:  # pylint: disable=R0902,R0903
    """
    Checks for new Brave Browser releases on GitHub, compares with the installed version,
    and offers to download the latest release based on specified criteria.

    This class provides functionality to:
    - Parse command-line arguments for release channel, file suffix, architecture, and page number.
    - Read a GitHub token from a .env file for authenticated API requests.
    - Determine the locally installed Brave Browser version (currently assumes Linux packages in /var/log/packages).
    - Fetch the latest Brave Browser releases from the GitHub API, filtering by channel, suffix, and architecture.
    - Compare the latest available version with the installed version.
    - If a newer version is found, prompt the user to download it using wget.
    """

    def __init__(self):
        """
        Initializes the BraveReleaseChecker by reading configuration from config.ini,
        reading the GitHub token, defining URLs, and parsing command-line arguments.
        """
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_path = '/etc/brave-releases-checker/config.ini'
        self.config = configparser.ConfigParser()
        self.config.read(self.config_path)

        self.package_path_str = self.config['PACKAGE'].get('path', '/var/log/packages/')
        self.package_name_prefix = self.config['PACKAGE'].get('package_name', 'brave-browser')
        self.github_token = self.config['GITHUB'].get('token', '')

        self.log_packages = Path(self.package_path_str)

        self.download_url = "https://github.com/brave/brave-browser/releases/download/"
        self.repo = "brave/brave-browser"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"{self.github_token}"
        }
        download_path_from_config = self.config['DOWNLOAD'].get('path')

        if download_path_from_config:
            self.download_folder = download_path_from_config
        else:
            self.download_folder = os.path.expanduser('~/Downloads/')

        self.args = self._parse_arguments()

    def _parse_arguments(self) -> argparse.Namespace:
        """Parses command-line arguments."""
        parser = argparse.ArgumentParser(description="Check and download Brave Browser releases.")
        parser.add_argument('--channel', default='stable', choices=['stable', 'beta', 'nightly'], help="Release channel to check")
        parser.add_argument('--suffix', default='.deb', choices=['.deb', '.rpm', '.tar.gz', '.apk', '.zip', '.dmg', '.pkg'],
                            help="Asset file suffix to filter")
        parser.add_argument('--arch', default='amd64', choices=['amd64', 'arm64', 'universal'], help="Architecture to filter")
        parser.add_argument('--page', type=int, default=1, help="Page number of releases to fetch")
        args = parser.parse_args()
        if args.page < 1:
            print("Error: Page number must be a positive integer.")
            sys.exit(1)
        return args

    def _get_installed_version(self) -> Union[version.Version, None]:  # pylint: disable=R0912
        """Finds and returns the locally installed Brave Browser version."""
        distribution = distro.id().lower()
        version_info = None

        distribution_handlers = {
            'slackware': self._get_installed_version_slackware,
            'ubuntu': self._get_installed_version_debian,
            'debian': self._get_installed_version_debian,
            'fedora': self._get_installed_version_rpm,
            'centos': self._get_installed_version_rpm,
            'redhat': self._get_installed_version_rpm,
        }

        handler = distribution_handlers.get(distribution)
        if handler:
            version_info = handler()
        else:
            print(f"Unsupported distribution: {distribution}. Cannot determine installed version.")

        return version_info

    def _get_installed_version_slackware(self) -> Union[version.Version, None]:
        """Gets installed version on Slackware."""
        brave_package = list(self.log_packages.glob(f'{self.package_name_prefix}*'))
        if brave_package:
            installed_info = str(brave_package[0]).rsplit('/', maxsplit=1)[-1]
            version_str = installed_info.split('-')[2]
            print(f"Installed Package (Slackware): {installed_info}")
            return version.parse(version_str)
        print(f"No installed version of {self.package_name_prefix} found in {self.package_path_str}.")
        sys.exit(1)

    def _get_installed_version_debian(self) -> Union[version.Version, None]:
        """Gets installed version on Debian-based systems."""
        try:
            process = subprocess.run(['dpkg', '-s', self.package_name_prefix], capture_output=True, text=True, check=True)
            output = process.stdout
            for line in output.splitlines():
                if line.startswith('Version:'):
                    version_str = line.split(':')[-1].strip()
                    print(f"Installed Package (Debian): {self.package_name_prefix} - Version: {version_str}")
                    return version.parse(version_str)
        except subprocess.CalledProcessError:
            print(f"Package {self.package_name_prefix} is not installed on this Debian-based system.")
            sys.exit(1)
        except FileNotFoundError:
            print("Error: dpkg command not found.")
            sys.exit(1)
        return None

    def _get_installed_version_rpm(self) -> Union[version.Version, None]:
        """Gets installed version on RPM-based systems."""
        try:
            process = subprocess.run(['rpm', '-qi', self.package_name_prefix], capture_output=True, text=True, check=True)
            output = process.stdout
            for line in output.splitlines():
                if line.startswith('Version     :'):
                    version_str = line.split(':')[-1].strip()
                    print(f"Installed Package (RPM): {self.package_name_prefix} - Version: {version_str}")
                    return version.parse(version_str)
        except subprocess.CalledProcessError as e:
            if f"package {self.package_name_prefix} is not installed" in e.stderr:
                print(f"Package {self.package_name_prefix} is not installed on this RPM-based system.")
                sys.exit(1)
            else:
                print(f"Error checking package (RPM): {e}")
                sys.exit(1)
        except FileNotFoundError:
            print("Error: rpm command not found.")
            sys.exit(1)
        return None

    def _fetch_github_releases(self) -> list:
        """Fetches Brave Browser releases from GitHub API based on criteria."""
        api_url = f"https://api.github.com/repos/{self.repo}/releases?page={self.args.page}"
        response = requests.get(api_url, headers=self.headers, timeout=10)
        if response.status_code != 200:
            print(f"Error downloading releases: {response.status_code}, Message: {response.json().get('message')}")
            sys.exit(1)

        releases = response.json()
        assets = []
        build_release_lower = self.args.channel.lower()
        brave_asset_suffix = self.args.suffix
        arch = self.args.arch

        for rel in releases:
            release_version = rel['tag_name'].lstrip('v')
            for asset in rel['assets']:
                asset_name = asset['name']
                if asset_name.endswith(brave_asset_suffix) and arch in asset_name:
                    asset_lower = asset_name.lower()
                    if build_release_lower == 'stable' and 'nightly' not in asset_lower and 'beta' not in asset_lower:
                        assets.append({
                            'version': release_version,
                            'asset_name': asset_name,
                            'tag_name': rel['tag_name']
                        })
                    elif build_release_lower == 'beta' and 'beta' in asset_lower:
                        assets.append({
                            'version': release_version,
                            'asset_name': asset_name,
                            'tag_name': rel['tag_name']
                        })
                    elif build_release_lower == 'nightly' and 'nightly' in asset_lower:
                        assets.append({
                            'version': release_version,
                            'asset_name': asset_name,
                            'tag_name': rel['tag_name']
                        })
        return assets

    def _check_and_download(self, installed_version: version.Version, assets: list) -> None:
        """Checks for newer versions and offers to download."""
        if assets:
            assets.sort(key=lambda x: version.parse(x['version']), reverse=True)
            latest_asset = assets[0]
            asset_file = latest_asset['asset_name']
            tag_version = latest_asset['tag_name']
            latest_version = version.parse(latest_asset['version'])

            print("\n" + "=" * 50)
            print(f"{BOLD}Brave Releases Checker{ENDC}")
            print(f"{BOLD}Channel:{ENDC} {self.args.channel.capitalize()}")
            print(f"{BOLD}Architecture:{ENDC} {self.args.arch}")
            print(f"{BOLD}File Suffix:{ENDC} {self.args.suffix}")
            print(f"{BOLD}Checking Page:{ENDC} {self.args.page}")
            print("-" * 50)
            print(f"{BOLD}Installed Version:{ENDC} v{installed_version}")
            print(f"{BOLD}Latest Version Available:{ENDC} v{latest_version} ({latest_asset['asset_name']})")
            print("=" * 50)

            if latest_version > installed_version:
                print(f"\n{BGREEN}A newer version is available: v{latest_version}{ENDC}")
                try:
                    answer = input(f'\nDo you want to download it? [{BGREEN}y{ENDC}/{BOLD}N{ENDC}] ')
                except (KeyboardInterrupt, EOFError):
                    print("\nDownload cancelled.")
                    sys.exit(1)
                if answer.lower() == 'y':
                    download_url = f'{self.download_url}{tag_version}/{asset_file}'
                    print(f"\n{BOLD}Downloading:{ENDC} {asset_file} to {self.download_folder}")
                    subprocess.call(
                        f"wget -c -q --tries=3 --progress=bar:force:noscroll --show-progress "
                        f"--directory-prefix={self.download_folder} '{download_url}'", shell=True
                    )
                    print(f"\n{BGREEN}Download complete!{ENDC} File saved in: {self.download_folder}{asset_file}")
                else:
                    print("\nDownload skipped.")
            else:
                print(f"\n{GREEN}Your Brave Browser is up to date!{ENDC} (v{installed_version} is the latest {self.args.channel} version)")
            print("=" * 50 + "\n")
        else:
            print("\n" + "=" * 50)
            print(f"{BOLD}Brave Releases Checker{ENDC}")
            print(f"{BOLD}Channel:{ENDC} {self.args.channel.capitalize()}")
            print(f"{BOLD}Architecture:{ENDC} {self.args.arch}")
            print(f"{BOLD}File Suffix:{ENDC} {self.args.suffix}")
            print(f"{BOLD}Checking Page:{ENDC} {self.args.page}")
            print("-" * 50)
            print(f"{BOLD}No {self.args.channel.capitalize()} {self.args.suffix} files for {self.args.arch} were found on this page.{ENDC}\n")
            print("=" * 50 + "\n")

    def run(self) -> None:
        """Main method to check and download releases."""
        installed_version = self._get_installed_version()
        if installed_version is not None:
            latest_releases = self._fetch_github_releases()
            self._check_and_download(installed_version, latest_releases)
        else:
            print("Skipping version check and download.")


if __name__ == "__main__":
    checker = BraveReleaseChecker()
    checker.run()
