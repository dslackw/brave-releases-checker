# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Changed
- **Refactored Configuration Handling:** Configuration settings are now managed through a dedicated `config.py` file, utilizing `dataclasses` for structured configuration. The `load_config` function handles reading from `config.ini` files in `/etc/brave-releases-checker/` or `~/.config/brave-releases-checker/`. This change improves code organization, readability, and maintainability by centralizing configuration logic.

### Added
- Introduced a `Colors` `dataclass` within `config.py` to manage ANSI escape codes for terminal colors and styles, enhancing the visual output of the application.

## [0.1.2] - 2025-05-08
### Fixed
- Fixed an issue where the 'brc' console script was not being correctly registered during installation.

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
