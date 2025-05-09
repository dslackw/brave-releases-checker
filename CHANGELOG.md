# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Fixed
- Fixed rpm return exit code:** Corrected the method for extracting the installed Brave Browser version from rpm packages on Fedora.
### Added
- **Added support:** Arch x86_64 for .rpm packages.
### Updated
- **Updated command:** Replaced command rpm with dnf to find the package installed and grab version.

## [0.1.5] - 2025-05-08
### Fixed
- Fixed Snap package version detection:** Corrected the method for extracting the installed Brave Browser version from Snap packages on Ubuntu, ensuring accurate version retrieval when Brave is installed via Snap.

## [0.1.4] - 2025-05-08
### Added
- **Added Snap support for Ubuntu:** Implemented functionality to detect the installed Brave Browser version on Ubuntu systems where it is installed as a Snap package. The tool will now attempt to retrieve the version using `snap info brave` if the standard Debian package check (`dpkg`) fails.

## [0.1.3] - 2025-05-08
### Changed
- **Refactored Configuration Handling:** Configuration settings are now managed through a dedicated `config.py` file, utilizing `dataclasses` for structured configuration. The `load_config` function handles reading from `config.ini` files in `/etc/brave-releases-checker/` or `~/.config/brave-releases-checker/`. This change improves code organization, readability, and maintainability by centralizing configuration logic.

### Added
- Introduced a `Colors` `dataclass` within `config.py` to manage ANSI escape codes for terminal colors and styles, enhancing the visual output of the application.
- **Added `--version` option:** Implemented a command-line option to display the current version of the Brave Releases Checker.

## [0.1.2] - 2025-05-08
### Fixed
- Fixed an issue where the 'brc' console script was not being correctly registered during installation.

## [0.1.1] - 2025-05-07
### Fixed
- Fixed an issue where the 'brc' console script was not being correctly registered during installation.

## [0.1.0] - 2025-05-07
### Added
- Initial release of Brave Releases Checker on PyPI.
- Support for checking stable, beta, and nightly releases.
- Ability to filter by architecture (e.g., x64).
- Reading configuration from `config.ini` (in `/etc/brave-releases-checker/` or `~/.config/brave-releases-checker/`).
- Provision of `brc` console script for command-line usage.
