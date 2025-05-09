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

To check the latest stable releases for the amd64 architecture:

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

Settings can be modified in the `config.ini` file. The program will search for this file in the following order:

1.  `/etc/brave-releases-checker/config.ini`
2.  `~/.config/brave-releases-checker/config.ini` (in the user's personal folder)

If a configuration file is not found in either of these locations, default values will be used.

To customize the settings, you can create the `config.ini` (or copy from the project) file in one of these locations. In the case of the second location (`~/.config/brave-releases-checker/config.ini`), you might need to create the `brave-releases-checker` folder inside the `.config` folder of your personal directory first.

You can define default download paths, the package name prefix, and your GitHub token (if you want to avoid rate limiting) within the `config.ini` file.

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Feel free to report issues or submit pull requests to the repository.

**Regarding Unsupported Distributions:**

This tool has been primarily tested on Debian-based (using `apt` and `snap`), Fedora (using `dnf`), Arch-based (using `pacman`), openSUSE (using `zypper`), and Slackware systems.

If you encounter issues or wish to use this tool on a distribution that is not fully supported for automatic installed version detection, please:

1.  **Open a new issue** detailing your operating system and the problem you are facing.
2.  If you have knowledge of how to retrieve the installed Brave Browser version on your distribution (e.g., specific commands or file paths), please include this information in the issue.
3.  Pull requests with added support for other distributions are highly appreciated! Please follow the existing code structure and provide clear explanations of your changes.

Your feedback and contributions are valuable in making this tool more versatile.
