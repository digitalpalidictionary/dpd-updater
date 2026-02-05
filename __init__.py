"""DPD Updater/Installer - A GUI application for managing DPD dictionary updates.

This module provides a cross-platform GUI application for checking and installing
updates to the Digital Pāḷi Dictionary (DPD) for GoldenDict users.

Usage:
    Run the updater GUI: python -m dpd_updater.main
"""

__version__ = "1.0.0"
__author__ = "Bodhirasa"
__description__ = "DPD Updater/Installer Application"

# Module exports
__all__ = [
    "__version__",
    "__author__",
    "__description__",
]

# Default paths and constants
DEFAULT_CONFIG_DIR_NAME = "dpd-updater"
GITHUB_API_URL = (
    "https://api.github.com/repos/digitalpalidictionary/dpd-db/releases/latest"
)
GOLDENDICT_ASSET_PATTERN = "dpd-goldendict*.zip"
