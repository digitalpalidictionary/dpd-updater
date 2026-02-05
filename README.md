# DPD Updater/Installer

A standalone, cross-platform GUI application that automates checking for and installing updates to the Digital Pāḷi Dictionary (DPD) for GoldenDict users.

## Overview

The DPD Updater provides a simple way for GoldenDict users to keep their DPD dictionary up to date without manually downloading and extracting files from GitHub releases.

## Features

- **Automatic Version Checking**: Queries GitHub API for the latest DPD release
- **One-Click Updates**: Downloads and installs updates with automatic backups
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **First-Time Setup**: Guides users through initial GoldenDict folder configuration
- **Configurable**: Settings for update preferences and folder paths

## Installation

### Windows
Download `dpd-updater.exe` from the latest release and run it directly (no Python installation required).

### macOS
Download `DPD Updater.app` from the latest release and copy it to your Applications folder.

### Linux
Download `dpd-updater` from the latest release, make it executable (`chmod +x dpd-updater`), and run it.

## Usage

1. **First Launch**: The updater will prompt you to select your GoldenDict content/dictionaries folder
2. **Version Check**: On startup, the application checks for available updates
3. **Update**: If an update is available, click "Update Now" to download and install
4. **Settings**: Access settings to change your GoldenDict folder or update preferences

## Module Structure

```
exporter/updater/
├── __init__.py          # Module initialization and constants
├── main.py              # Application entry point (GUI)
├── config.py            # Configuration management
├── github_client.py     # GitHub API integration
├── installer.py         # Download and installation logic
├── ui_setup.py          # First-time setup wizard UI
└── ui_main.py           # Main application UI
```

## Configuration

Configuration is stored in platform-specific locations:

- **Windows**: `%APPDATA%\dpd-updater\config.json`
- **macOS**: `~/Library/Application Support/dpd-updater/config.json`
- **Linux**: `~/.config/dpd-updater/config.json`

The configuration file stores:
- GoldenDict folder path
- Currently installed DPD version
- Auto-check preference (default: true)
- Backup preference (default: true)

## Build for Your Own OS

Want to build the DPD Updater locally? It's easy!

### Build Instructions

1. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Navigate to the dpd-updater directory:**
   ```bash
   cd resources/dpd-updater
   ```

3. **Install dependencies:**
   ```bash
   uv sync
   ```

4. **Build the executable:**
   ```bash
   uv run python build.py
   ```

That's it! The built executable will be in the `dist/` folder.

### What You'll Get

- **Windows**: `dist/DPD-Updater.exe`
- **macOS**: `dist/DPD Updater.app`
- **Linux**: `dist/dpd-updater`

### Requirements

- Python 3.10 or higher
- Internet connection (for downloading dependencies)
- About 100MB free space for the build

### Troubleshooting

**"Python not found"**: Install Python 3.10+ from [python.org](https://python.org)

**Build fails**: Make sure you're in the `dpd-updater` directory (where `build.py` is located)

## Development

For detailed development setup and architecture, see the source code structure below.

## Dependencies

- Python 3.10+
- Flet (UI framework)
- requests (GitHub API calls)
- packaging (version comparison)

## License

This project is part of the Digital Pāḷi Dictionary (DPD) project.
