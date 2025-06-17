# Brave Releases Checker

A simple command-line tool to check for the latest Brave Browser releases from GitHub. It supports selecting a specific channel (stable, beta, nightly), filtering by architecture, file suffix, and even listing all available releases based on your criteria. Configuration can be managed through a config.ini file for persistent settings.

## Features

* **Latest Release Checking:** Fetches the most recent Brave Browser releases from the official GitHub repository.
* **Release Channel Selection:** Filter releases by channel: stable, beta, or nightly.
* **Architecture Filtering:** Display assets for a specific architecture (e.g., amd64, arm64, aarch64, x86_64).
* **File Suffix Filtering:** Specify the asset file type to filter (e.g., .deb, .rpm, .tar.gz, .apk, .zip, .dmg, .pkg).
* **List Available Releases:** Option to list all matching releases on a specific page or a range of pages without checking for an installed version.
* **Page Range Search:** Ability to search for releases across a specified range of pages on the GitHub API.
* **Flexible Configuration:** Default settings can be configured and persisted in a config.ini file.
* **Console Script:** Provides a convenient `brc` command-line script for easy use.
* **Daemon Mode:** Run the checker in the background, periodically checking for new releases and notifying you of updates.
* **Daemon Logging:** Comprehensive logging to a dedicated file for background operations.

## Installation

Brave Releases Checker is written in Python and requires some system dependencies, especially for desktop notifications.

Step 1: Install Python D-Bus Bindings (Required for Notifications)

Before installing brave-releases-checker, you need to install the D-Bus bindings for Python on your system. This package is typically provided by your distribution's package manager:

* Debian/Ubuntu/Mint: sudo apt install python3-dbus
* Fedora/RHEL/CentOS: sudo dnf install python3-dbus
* Arch Linux/Manjaro: sudo pacman -Sy python-dbus
* openSUSE: sudo zypper install python3-dbus
* Slackware: Look for the dbus-python or python3-dbus package in the official Slackware packages or on SlackBuilds.org and install it manually.

Step 2: Install Brave Releases Checker

We recommend installing brave-releases-checker system-wide for the smooth operation of desktop notifications:

1. Clone the repository:

    ```bash
    git clone https://github.com/your-username/brave-releases-checker.git
    cd brave-releases-checker
    ```

2. Install using pip: 

    ```bash
    sudo pip install .
    ```

## Usage

Use the brc script from your command line with various options to tailor your release checks.

```bash
brc --help
```

### Basic Checks

* Check the latest stable release for the default architecture (configured in config.ini or defaults to amd64):
    ```bash
    brc
    ```

* Check the latest stable release for a specific architecture:
    ```bash
    brc --channel stable --arch arm64
    ```

* Check the latest nightly release for the default architecture:
    ```bash
    brc --channel nightly
    ```

### Filtering by File Suffix

* Check for the latest beta .rpm package for the default architecture:
    ```bash
    brc --channel beta --suffix .rpm
    ```

### Listing Available Releases

The `--list` option allows you to see all available releases that match your specified criteria without comparing against an installed version.

* List all stable .deb releases on the first page:
    ```bash
    brc --list --channel stable --suffix .deb --page 1
    ```

* List all beta .rpm releases across pages 1 to 3:
    ```bash
    brc --list --channel beta --suffix .rpm --pages 1-3
    ```

### Specifying Page or Page Range

The `--page` option (when not using `--list`) specifies which page of releases to check. The `--pages` option (especially useful with `--list`) allows you to define a range of pages to search.

* Check the latest stable release on the second page:
    ```bash
    brc --channel stable --page 2
    ```

* List all nightly releases across pages 1 to 5:

    ```bash
    brc --list --channel nightly --pages 1-5
    ```

### Specifying an Asset Version

* You can target a specific asset version:

    ```bash
    brc --asset-version 1.79.105
    ```

Combine this with other options to find a specific release for a channel and architecture.

## Daemon Mode

For automatic background checks, you can run brave-releases-checker as a daemon.

* For systemd-based systems (Debian, Ubuntu, Fedora, Arch, openSUSE, etc.):
  Create a systemd service file. See the example in docs/systemd-service.md (or include it directly here).

* For systems without systemd (e.g., Slackware with SysVinit):
  You can start the daemon at system boot by adding the command to /etc/rc.d/rc.local (or an equivalent boot script):

```bash
nohup /usr/local/bin/brc --daemon --interval 60 &
```
(Ensure the path /usr/local/bin/brc is correct and adjust the interval as desired.)

Run the Brave Releases Checker in the background as a daemon. It will periodically check for new releases and send desktop notifications when an update is available.

* Run the checker in daemon mode, checking every 60 minutes (default):
    
    ```bash
    brc --daemon
    ```
* Run the checker in daemon mode, checking every 30 minutes:

    ```bash
    brc --daemon --interval 30
    ```

## Daemon Logging

When running in daemon mode, all operational messages, warnings, and errors are logged to a file. This is crucial for monitoring the daemon's activity without needing a console.

Log File Location: The daemon logs are stored in:
```~/.local/share/brave_checker/logs/brave_checker.log```
(The directory will be created automatically if it doesn't exist.)

* Accessing Logs: You can view the log file using standard command-line tools:

    ```bash
    tail -f ~/.local/share/brave_checker/logs/brave_checker.log
    ```
Or simply open it with a text editor.

## Configuration

The `config.ini` file allows you to set default values for various options, so you don't have to specify them every time you run the script. The program searches for this file in the following order:

1.  /etc/brave-releases-checker/config.ini
2.  ~/.config/brave-releases-checker/config.ini

If no configuration file is found, default values are used.

To customize, create the `config.ini` file (you might find a sample in the project repository) in one of these locations. For the second location, you might need to create the `brave-releases-checker` directory inside your `~/.config` directory first.

Here's an example `config.ini` file:

```
[PACKAGE]
path = /var/log/packages/
[DEFAULT]
channel = beta
suffix = .rpm
arch = arm64
pages = 1
download_path = /tmp/brave_downloads
[GITHUB]
token=your_github_personal_access_token_here
[DAEMON]
log_path = ~/.local/share/brave_checker/logs/
```

You can define default values for channel, suffix, arch, download_path, and the default pages to check. Command-line arguments will always override the settings in the config.ini file.

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Feel free to report issues or submit pull requests to the repository.

Regarding Unsupported Distributions:

This tool has been primarily tested on Debian-based (apt, snap), Fedora (dnf), Arch-based (pacman), openSUSE (zypper), and Slackware systems for automatic installed version detection.

If you encounter issues or wish to use this tool on a distribution without full support for automatic installed version detection:

1.  Open a new issue detailing your operating system and the problem.
2.  Include information on how to retrieve the installed Brave Browser version on your distribution (e.g., commands, file paths).
3.  Pull requests adding support for other distributions are highly encouraged. Please adhere to the existing code structure and provide clear explanations of your changes.

Your feedback and contributions are invaluable for expanding the tool's compatibility.
