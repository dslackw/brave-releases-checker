#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Union

import distro
import notify2
import requests
from packaging import version

from brave_releases_checker.config import Colors, load_config
from brave_releases_checker.distributions import InstalledVersion
from brave_releases_checker.version import __version__

# Load config early to get log path
config = load_config()

# Define log file directory from config
log_dir = Path(os.path.expanduser(config.log_file_dir))  # Expanduser is important here

# Ensure the log directory exists
log_dir.mkdir(parents=True, exist_ok=True)

# Set up logging for daemon mode
log_file_path = log_dir / "brave_checker.log"

logger = logging.getLogger('BraveCheckerDaemon')
logger.setLevel(logging.INFO)  # Or logging.DEBUG for more verbose logs

# File handler
file_handler = logging.FileHandler(log_file_path)
file_handler.setLevel(logging.INFO)  # Level for file log

# Console handler (for non-daemon mode, or specific messages)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # Level for console output

# Formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers
if not logger.handlers:  # Avoid adding handlers multiple times if script reloads
    logger.addHandler(file_handler)
    # Only add console handler if not in daemon mode, or based on specific cli args
    # This logic might need to be adjusted based on your argparse setup
    # For now, let's assume it's added by default and handled by _output_message
    # Or, you can explicitly add/remove it based on self.args.daemon in the main loop
    # For now, we'll rely on _output_message to handle print vs log


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
        self.download_folder = str(config.download_folder)
        self.channel = config.channel
        self.asset_suffix = config.asset_suffix
        self.asset_arch = config.asset_arch
        self.pages = config.pages
        self.color = Colors()
        self.logger = logger  # Make the global logger available in the class

        self.download_url = 'https://github.com/brave/brave-browser/releases/download/'
        self.repo = 'brave/brave-browser'
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'Authorization': f'{config.github_token}'
        }

        self.args = self._parse_arguments()
        self.installed_version = InstalledVersion(self.args)

        # Initialize notify2 once
        try:
            notify2.init('Brave Release Checker')
            self.notifications_enabled = True
        except Exception as e:  # pylint: disable=[W0718]
            # Use logger for this warning, as it's an initialization issue
            self.logger.warning("Could not initialize notify2: %s. Notifications will be disabled.", e)
            self.notifications_enabled = False

    def _parse_arguments(self) -> argparse.Namespace:
        """Parses command-line arguments."""
        parser = argparse.ArgumentParser(description='Check and download Brave Browser releases.')
        parser.add_argument('--channel', default=self.channel, choices=['stable', 'beta', 'nightly'], help='Release channel to check')
        parser.add_argument('--suffix', default=self.asset_suffix, choices=['.deb', '.rpm', '.tar.gz', '.apk', '.zip', '.dmg', '.pkg'],
                            help='Asset file suffix to filter')
        parser.add_argument('--arch', default=self.asset_arch, choices=['amd64', 'arm64', 'aarch64', 'x86_64'], help='Architecture to filter')
        parser.add_argument('--download-path', default=self.download_folder, help='Path to download')
        parser.add_argument('--asset-version', help='Specify the asset version')
        parser.add_argument('--pages', type=str, default=self.pages, help='Page number or range (e.g., 1 or 1-5) of releases to fetch')
        parser.add_argument('--list', action='store_true', help='List available releases based on criteria')
        parser.add_argument('--daemon', action='store_true', help='Run in daemon mode, checking periodically.')
        parser.add_argument('--interval', type=int, default=60, help='Interval in minutes for daemon mode checks (default: 60)')
        parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
        args = parser.parse_args()

        try:
            if '-' in args.pages:
                start_page_str, end_page_str = args.pages.split('-')
                args.start_page = int(start_page_str)
                args.end_page = int(end_page_str)
                if args.start_page < 1 or args.end_page < args.start_page:
                    raise ValueError('Invalid page range.')
            else:
                args.start_page = int(args.pages)
                args.end_page = int(args.pages)
                if args.start_page < 1:
                    raise ValueError('Page number must be a positive integer.')
        except ValueError as e:
            print(f'{self.color.bred}Error:{self.color.endc} Invalid page specification: {e}')
            self.logger.error("Invalid page specification: %s", e)  # Log this error too
            sys.exit(1)
        return args

    def send_notification(self, summary: str, body: str) -> None:
        """Sends a D-Bus notification using notify2."""
        if self.notifications_enabled:
            try:
                n = notify2.Notification(summary, body, 'brave-browser')
                n.show()
                self.logger.info("Notification sent: Summary='%s', Body='%s'", summary, body)
            except Exception as e:  # pylint: disable=[W0718]
                self.logger.error("Failed to send notify2 notification: %s", e)
        else:
            self.logger.warning("Notifications disabled. Summary: %s, Body: %s", summary, body)

    def _get_installed_version(self) -> Union[version.Version, None]:  # pylint: disable=R0912
        """Finds and returns the locally installed Brave Browser version."""
        distribution = distro.id().lower()
        version_info = None

        distribution_handlers = {
            'slackware': self.installed_version.get_slackware,
            'ubuntu': self.installed_version.get_debian_dpkg,
            'debian': self.installed_version.get_debian_dpkg,
            'fedora': self.installed_version.get_rpm_dnf,
            'centos': self.installed_version.get_rpm_dnf,
            'redhat': self.installed_version.get_rpm_dnf,
            'arch': self.installed_version.get_arch,
            'opensuse-tumbleweed': self.installed_version.get_opensuse,
            'opensuse-leap': self.installed_version.get_opensuse,
        }

        handler = distribution_handlers.get(distribution)
        if handler:
            version_info = handler()
        else:
            # For CLI mode, print. For daemon, log.
            if self.args.daemon:
                self.logger.warning("Unsupported distribution: %s. Cannot determine installed version.", distribution)
            else:
                print(f'Unsupported distribution: {distribution}. Cannot determine installed version.')

        return version_info

    def _fetch_github_releases(self) -> list[str]:
        """Fetches Brave Browser releases from GitHub API based on criteria."""
        all_assets: list[str] = []
        total_pages = self.args.end_page - self.args.start_page + 1

        for _, page in enumerate(range(self.args.start_page, self.args.end_page + 1)):
            if not self.args.daemon:
                status_message = f"{self.color.bold}Connecting to GitHub (Page {page}/{total_pages})... {self.color.endc}"
                sys.stdout.write(f"\r{status_message}")  # Use \r to overwrite the previous line
                sys.stdout.flush()
            try:
                response = requests.get(f"https://api.github.com/repos/{self.repo}/releases?page={page}", headers=self.headers, timeout=10)
                response.raise_for_status()
                releases = response.json()
                self._process_releases_for_page(releases, all_assets)
            except requests.exceptions.Timeout:
                msg = f"Connection to GitHub (Page {page}) timed out."
                if self.args.daemon:
                    self.logger.error(msg)
                    self.send_notification("Brave Checker Error", msg)
                    return []  # Return empty list in daemon mode to continue the loop

                sys.stdout.write(f"\r{self.color.bred}Error:{self.color.endc} {msg}{" " * 40}\n")
                sys.stdout.flush()
                sys.exit(1)
            except requests.exceptions.RequestException as e:
                msg = f"Failed to download releases from GitHub (Page {page}): {e}"
                if self.args.daemon:
                    self.logger.error(msg)
                    self.send_notification("Brave Checker Error", msg)
                    return []  # Return empty list in daemon mode to continue the loop

                sys.stdout.write(f"\r{self.color.bred}Error:{self.color.endc} {msg}{" " * 40}\n")
                sys.stdout.flush()
                sys.exit(1)

        if not self.args.daemon:
            sys.stdout.write(f'\r{self.color.bold}Connecting to GitHub (Pages {self.args.start_page}-{self.args.end_page})... '
                             f'{self.color.bgreen}Done{self.color.endc}{" " * 40}\n')
            sys.stdout.flush()
        return all_assets

    def _process_releases_for_page(self, releases: list[Any], all_assets: list[Any]) -> None:
        """Processes the releases fetched from a single GitHub API page."""
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
                        all_assets.append({
                            'version': release_version,
                            'asset_name': asset_name,
                            'tag_name': rel['tag_name']
                        })

    def _list_assets_found(self, all_found_assets: list[Any]) -> None:
        """List all available releases based on criteria."""
        print('\n' + '=' * 50)
        print(f'{self.color.bold}Available Brave Releases{self.color.endc}')
        print(f'{self.color.bold}Channel:{self.color.endc} {self.args.channel.capitalize()}')
        print(f'{self.color.bold}Architecture:{self.color.endc} {self.args.arch}')
        print(f'{self.color.bold}File Suffix:{self.color.endc} {self.args.suffix}')
        print(f'{self.color.bold}Page:{self.color.endc} {self.args.pages}')
        print('-' * 50)
        if all_found_assets:
            print(f'{self.color.bold}{'Version':<15} {'Filename'}{self.color.endc}')
            print('-' * 50)
            for asset in all_found_assets:
                print(f'{asset['version']:<15} {asset['asset_name']}')
        else:
            print(f'{self.color.byellow}No releases found matching your criteria on this page.{self.color.endc}')
        print('=' * 50 + '\n')
        sys.exit(0)

    def _check_and_download(self, installed_version: version.Version, all_found_assets: list[Any]) -> None:  # pylint: disable=[R0912,R0915]
        """Checks for newer versions and offers to download."""
        asset_version_arg = self.args.asset_version
        download_folder = self.args.download_path

        if download_folder:
            self.download_folder = download_folder

        if self.args.list:
            self._list_assets_found(all_found_assets)

        # Do not print headers and footers in daemon mode
        if not self.args.daemon:
            print('\n' + '=' * 50)
            print(f'{self.color.bold}Brave Releases Checker{self.color.endc}')
            print(f'{self.color.bold}Channel:{self.color.endc} {self.args.channel.capitalize()}')
            print(f'{self.color.bold}Architecture:{self.color.endc} {self.args.arch}')
            print(f'{self.color.bold}File Suffix:{self.color.endc} {self.args.suffix}')
            print(f'{self.color.bold}Checking Page:{self.color.endc} {self.args.pages}')
            print('-' * 50)
            print(f'{self.color.bold}Installed Version:{self.color.endc} v{installed_version}')
            print('=' * 50)

        filtered_assets = []
        if asset_version_arg:
            target_version = version.parse(asset_version_arg)
            for asset in all_found_assets:
                if version.parse(asset['version']) == target_version:
                    filtered_assets.append(asset)
            if filtered_assets:
                latest_asset = filtered_assets[0]
            else:
                msg = f'No asset found for version v{asset_version_arg} with the specified criteria.'
                if self.args.daemon:
                    self.logger.error(msg)  # Log error instead of print
                    self.send_notification("Brave Update Error", msg)
                else:
                    print(f'\n{self.color.bred}Error:{self.color.endc} {msg}')
                    print('=' * 50 + '\n')
                return
        elif all_found_assets:
            all_found_assets.sort(key=lambda x: version.parse(x['version']), reverse=True)
            latest_asset = all_found_assets[0]
        else:
            msg = (f'No {self.args.channel.capitalize()} {self.args.suffix} files for'
                   f' {self.args.arch} were found on page {self.args.pages}.')
            if self.args.daemon:
                self.logger.info(msg)  # Log info instead of print
            else:
                print(f'\n{self.color.bold}{msg}{self.color.endc}\n')
                print('=' * 50 + '\n')
            return

        latest_version = version.parse(latest_asset['version'])
        asset_file = latest_asset['asset_name']  # Corrected to use 'asset_name'
        tag_version = latest_asset['tag_name']

        if not self.args.daemon:
            print(f'{self.color.bold}Latest Version Available:{self.color.endc} v{latest_version} ({latest_asset['asset_name']})')
            print('=' * 50)

        # latest_version = version.parse('1.80.0')
        if latest_version > installed_version:
            msg = f'A newer version is available: v{latest_version}'
            if self.args.daemon:
                self.logger.info(msg)  # Log info instead of print
                self.send_notification("Brave Browser Update!", msg)
                return  # In daemon mode, just send notification and return

            print(f'\n{self.color.byellow}{msg}{self.color.endc}')
            try:
                answer = input(f'\nDo you want to download it? [{self.color.bgreen}y{self.color.endc}/{self.color.bold}N{self.color.endc}] ')
            except (KeyboardInterrupt, EOFError):
                print('\nDownload cancelled.')
                sys.exit(1)
            if answer.lower() == 'y':
                download_url = f'{self.download_url}{tag_version}/{asset_file}'
                print(f'\n{self.color.bold}Downloading:{self.color.endc} {asset_file} to:\n'
                      f'  {self.download_folder}')
                subprocess.call(
                    f"wget -c -q --tries=3 --progress=bar:force:noscroll --show-progress "
                    f"--directory-prefix={self.download_folder} '{download_url}'", shell=True
                )
                print(f'\n{self.color.bgreen}Download complete!{self.color.endc} File saved in: \n'
                      f'  {self.download_folder}{asset_file}')
            else:
                print('\nDownload skipped.')
        elif asset_version_arg:
            msg = f'The specified version (v{latest_version}) matches the latest available.'
            if not self.args.daemon:  # Print only for CLI
                print(f'\n{self.color.green}{msg}{self.color.endc}')
            else:  # For daemon, log info
                self.logger.info(msg)
        else:
            msg = f'Your Brave Browser is up to date! (v{installed_version} is the latest {self.args.channel} version)'
            if not self.args.daemon:  # Print only for CLI
                print(f'\n{self.color.green}{msg}{self.color.endc}')
            else:  # For daemon, log info
                self.logger.info(msg)

        if not self.args.daemon:  # Print final separator only if not in daemon mode
            print('=' * 50 + '\n')

    def run(self) -> None:
        """Main method to check and download releases. This is called once per execution or repeatedly in daemon mode."""
        installed_version = self._get_installed_version()
        if installed_version is None:
            # Logic for daemon mode when installed version is not found
            if self.args.daemon:
                self.logger.warning("Brave Browser is not installed or its version cannot be determined. Skipping download prompt in daemon mode.")
                self.send_notification("Brave Checker Warning", "Brave Browser version not found. Cannot check for updates.")
                return  # Return to continue the daemon loop

            # Logic for CLI mode when installed version is not found
            try:
                answer = input(f'{self.color.bred}Warning:{self.color.endc} Brave Browser is not installed or its version cannot be determined.\n'
                               f'\nDo you want to continue and download the latest release? '
                               f'[{self.color.bgreen}y{self.color.endc}/{self.color.bold}N{self.color.endc}] ')
                if answer.lower() != 'y':
                    print('Download cancelled by user.')
                    sys.exit(0)
                else:
                    latest_releases = self._fetch_github_releases()
                    self._check_and_download(version.Version('0.0.0'), latest_releases)  # Pass a dummy version
                    return
            except (KeyboardInterrupt, EOFError):
                print('\nOperation cancelled.')
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

    if checker.args.daemon:
        checker.logger.info("Starting Brave Release Checker in daemon mode. Checking for updates every %s minutes...", checker.args.interval)
        while True:
            try:
                checker.run()
            except Exception as e:  # pylint: disable=broad-exception-caught
                # Use logger.exception() to get full traceback in log file
                checker.logger.exception("An unexpected error occurred during daemon check: %s", e)
                checker.send_notification("Brave Checker Daemon Error", f"An unexpected error occurred: {e}")
            time.sleep(checker.args.interval * 60)
    else:
        # Normal CLI operation - executes only once
        checker.run()


if __name__ == '__main__':
    main()
