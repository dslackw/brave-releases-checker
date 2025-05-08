#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import subprocess
import sys
from typing import Union

import distro
import requests
from packaging import version

from brave_releases_checker.config import Colors, load_config
from brave_releases_checker.version import __version__


class BraveReleaseChecker:  # pylint: disable=R0902,R0903
    """
    Checks for new Brave Browser releases on GitHub, compares with the installed version,
    and offers to download the latest release based on specified criteria.
    """

    def __init__(self) -> None:
        """
        Initializes the BraveReleaseChecker by loading configuration, defining URLs,
        setting headers for GitHub API requests, and parsing command-line arguments.
        """
        config = load_config()
        self.config_path = config.config_path
        self.package_path_str = str(config.package_path)
        self.package_name_prefix = config.package_name_prefix
        self.github_token = config.github_token
        self.download_folder = str(config.download_folder)
        self.log_packages = config.package_path
        self.color = Colors()

        self.download_url = "https://github.com/brave/brave-browser/releases/download/"
        self.repo = "brave/brave-browser"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"{self.github_token}"
        }

        self.args = self._parse_arguments()

    def _parse_arguments(self) -> argparse.Namespace:
        """Parses command-line arguments."""
        parser = argparse.ArgumentParser(description="Check and download Brave Browser releases.")
        parser.add_argument('--channel', default='stable', choices=['stable', 'beta', 'nightly'], help="Release channel to check")
        parser.add_argument('--suffix', default='.deb', choices=['.deb', '.rpm', '.tar.gz', '.apk', '.zip', '.dmg', '.pkg'],
                            help="Asset file suffix to filter")
        parser.add_argument('--arch', default='amd64', choices=['amd64', 'arm64', 'aarch64', 'universal'], help="Architecture to filter")
        parser.add_argument('--download-path', default=self.download_folder, help="Path to download")
        parser.add_argument('--asset-version', help="Specify the asset version")
        parser.add_argument('--page', type=int, default=1, help="Page number of releases to fetch")
        parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
        args = parser.parse_args()
        if args.page < 1:
            print(f'{self.color.bred}Error{self.color.endc}: Page number must be a positive integer.')
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
            'arch': self._get_installed_version_arch,
            'opensuse': self._get_installed_version_opensuse,
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
        return None

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
            print('{BRED}Error:{ENDC} dpkg command not found.')
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
                print(f'{self.color.bred}Error:{self.color.endc} checking package (RPM): {e}')
                sys.exit(1)
        except FileNotFoundError:
            print('{BRED}Error:{ENDC} rpm command not found.')
            sys.exit(1)
        return None

    def _get_installed_version_arch(self) -> Union[version.Version, None]:
        """Gets installed version on Arch Linux."""
        try:
            process = subprocess.run(['pacman', '-Qi', self.package_name_prefix], capture_output=True, text=True, check=True)
            output = process.stdout
            for line in output.splitlines():
                if line.startswith('Version        :'):
                    version_str = line.split(':')[-1].strip()
                    print(f"Installed Package (Arch): {self.package_name_prefix} - Version: {version_str}")
                    return version.parse(version_str)
        except subprocess.CalledProcessError:
            print(f"Package {self.package_name_prefix} is not installed on this Arch-based system.")
            sys.exit(1)
        except FileNotFoundError:
            print(f"{self.color.bred}Error:{self.color.endc} pacman command not found.")
            sys.exit(1)
        return None

    def _get_installed_version_opensuse(self) -> Union[version.Version, None]:
        """Gets installed version on openSUSE."""
        try:
            process = subprocess.run(['zypper', 'info', self.package_name_prefix], capture_output=True, text=True, check=True)
            output = process.stdout
            for line in output.splitlines():
                if line.startswith('Version: '):
                    version_str = line.split(':')[-1].strip()
                    print(f"Installed Package (openSUSE): {self.package_name_prefix} - Version: {version_str}")
                    return version.parse(version_str)
        except subprocess.CalledProcessError as e:
            if f"Information for package '{self.package_name_prefix}' not found." in e.stderr:
                print(f"Package {self.package_name_prefix} is not installed on this openSUSE system.")
                sys.exit(1)
            else:
                print(f"{self.color.bred}Error:{self.color.endc} checking package (openSUSE): {e}")
                sys.exit(1)
        except FileNotFoundError:
            print(f"{self.color.bred}Error:{self.color.endc} zypper command not found.")
            sys.exit(1)
        return None

    def _fetch_github_releases(self) -> list:
        """Fetches Brave Browser releases from GitHub API based on criteria."""
        api_url = f"https://api.github.com/repos/{self.repo}/releases?page={self.args.page}"
        sys.stdout.write(f"{self.color.bold}Connecting to GitHub... {self.color.endc}")
        sys.stdout.flush()
        try:
            response = requests.get(api_url, headers=self.headers, timeout=10)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        except requests.exceptions.Timeout:
            print(f"{self.color.bred}Error:{self.color.endc} Connection to GitHub timed out.")
            sys.exit(1)
        except requests.exceptions.RequestException as e:
            print(f"{self.color.bred}Error:{self.color.endc} Failed to download releases from GitHub: {e}")
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
                    add_asset = False
                    if build_release_lower == 'stable':
                        if 'nightly' not in asset_lower and 'beta' not in asset_lower:
                            add_asset = True
                    elif build_release_lower == 'beta':
                        if 'beta' in asset_lower:
                            add_asset = True
                    elif build_release_lower == 'nightly':
                        if 'nightly' in asset_lower:
                            add_asset = True

                    if add_asset:
                        assets.append({
                            'version': release_version,
                            'asset_name': asset_name,
                            'tag_name': rel['tag_name']
                        })
        return assets

    def _check_and_download(self, installed_version: version.Version, all_found_assets: list) -> None:  # pylint: disable=[R0912,R0915]
        """Checks for newer versions and offers to download."""
        asset_version_arg = self.args.asset_version
        download_folder = self.args.download_path

        if download_folder:
            self.download_folder = download_folder

        print("\n" + "=" * 50)
        print(f"{self.color.bold}Brave Releases Checker{self.color.endc}")
        print(f"{self.color.bold}Channel:{self.color.endc} {self.args.channel.capitalize()}")
        print(f"{self.color.bold}Architecture:{self.color.endc} {self.args.arch}")
        print(f"{self.color.bold}File Suffix:{self.color.endc} {self.args.suffix}")
        print(f"{self.color.bold}Checking Page:{self.color.endc} {self.args.page}")
        print("-" * 50)
        print(f"{self.color.bold}Installed Version:{self.color.endc} v{installed_version}")
        print("=" * 50)

        filtered_assets = []
        if asset_version_arg:
            target_version = version.parse(asset_version_arg)
            for asset in all_found_assets:
                if version.parse(asset['version']) == target_version:
                    filtered_assets.append(asset)
            if filtered_assets:
                latest_asset = filtered_assets[0]
            else:
                print(f"\n{self.color.bred}Error:{self.color.endc} No asset found for version v{asset_version_arg} with the specified criteria.")
                print("=" * 50 + "\n")
                return
        elif all_found_assets:
            all_found_assets.sort(key=lambda x: version.parse(x['version']), reverse=True)
            latest_asset = all_found_assets[0]
        else:
            print(f"\n{self.color.bold}No {self.args.channel.capitalize()} {self.args.suffix} files for"
                  f" {self.args.arch} were found on page {self.args.page}.{self.color.endc}\n")
            print("=" * 50 + "\n")
            return

        latest_version = version.parse(latest_asset['version'])
        asset_file = latest_asset['asset_name']
        tag_version = latest_asset['tag_name']

        print(f"{self.color.bold}Latest Version Available:{self.color.endc} v{latest_version} ({latest_asset['asset_name']})")
        print("=" * 50)

        if latest_version > installed_version:
            print(f"\n{self.color.bgreen}A newer version is available: v{latest_version}{self.color.endc}")
            try:
                answer = input(f'\nDo you want to download it? [{self.color.bgreen}y{self.color.endc}/{self.color.bold}N{self.color.endc}] ')
            except (KeyboardInterrupt, EOFError):
                print("\nDownload cancelled.")
                sys.exit(1)
            if answer.lower() == 'y':
                download_url = f'{self.download_url}{tag_version}/{asset_file}'
                print(f"\n{self.color.bold}Downloading:{self.color.endc} {asset_file} to:\n"
                      f"  {self.download_folder}")
                subprocess.call(
                    f"wget -c -q --tries=3 --progress=bar:force:noscroll --show-progress "
                    f"--directory-prefix={self.download_folder} '{download_url}'", shell=True
                )
                print(f"\n{self.color.bgreen}Download complete!{self.color.endc} File saved in: \n"
                      f"  {self.download_folder}{asset_file}")
            else:
                print("\nDownload skipped.")
        elif asset_version_arg:
            print(f"\n{self.color.green}The specified version (v{latest_version}) matches the latest available.{self.color.endc}")
        else:
            print(f'\n{self.color.green}Your Brave Browser is up to date!{self.color.endc} '
                  f'(v{installed_version} is the latest {self.args.channel} version)')
        print("=" * 50 + "\n")

    def run(self) -> None:
        """Main method to check and download releases."""
        installed_version = self._get_installed_version()
        if installed_version is None:
            try:
                answer = input(f'{self.color.bred}Warning:{self.color.endc} Brave Browser is not installed or its version cannot be determined.\n'
                               f'\nDo you want to continue and download the latest release? '
                               f'[{self.color.bgreen}y{self.color.endc}/{self.color.bold}N{self.color.endc}] ')
                if answer.lower() != 'y':
                    print("Download cancelled by user.")
                    sys.exit(0)
                else:
                    latest_releases = self._fetch_github_releases()
                    self._check_and_download(version.Version('0.0.0'), latest_releases)  # Pass a dummy version
                    return
            except (KeyboardInterrupt, EOFError):
                print("\nOperation cancelled.")
                sys.exit(1)
        else:
            latest_releases = self._fetch_github_releases()
            self._check_and_download(installed_version, latest_releases)


def main() -> None:
    """
    The main entry point of the Brave Release Checker script.

    It creates an instance of the BraveReleaseChecker class and initiates the
    process of checking for and potentially downloading new Brave Browser releases.
    """
    checker = BraveReleaseChecker()
    checker.run()


if __name__ == "__main__":
    main()
