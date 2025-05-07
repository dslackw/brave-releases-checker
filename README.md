# Brave Releases Checker

A simple command-line tool to check for the latest Brave Browser releases from GitHub. It supports selecting a specific channel (stable, beta, nightly) and retrieving information about the assets (installation files) for the chosen architecture.

## Features

* **Release Checking:** Fetches the most recent Brave Browser releases from the official GitHub repository.
* **Channel Selection:** Ability to filter releases for the `stable`, `beta`, and `nightly` channels.
* **Architecture Filtering:** Option to display assets for a specific architecture (e.g., `x64`, `arm64`).
* **Flexible Configuration:** Settings can be configured via a `config.ini` file.
* **Console Script:** Provides a convenient console script `brc` for easy command-line usage.

## Installation

```bash
pip install brave-releases-checker
```

## Usage

From your command line, use the `brc` script with the appropriate options.

```bash
brc --help
```

To check the latest stable releases for the x64 architecture:

```bash
brc --channel stable --arch amd64
```

or just type:

```bash
brc
```

To check the latest nightly releases:

```bash
brc --channel nightly
```

## Configuration

Settings can be modified in the config.ini file located at the root of the project. You can define default download paths, the package name prefix, and your GitHub token (if you want to avoid rate limiting).

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Feel free to report issues or submit pull requests to the repository.
