"""Configuration management for the DPD Updater.

This module handles all configuration file I/O, including:
- Cross-platform config path detection
- Config file read/write operations
- Config schema validation
"""

import json
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Config:
    """Configuration data model.

    Attributes:
        goldendict_path: Path to the GoldenDict content/dictionaries folder
        installed_version: Currently installed DPD version (or "unknown")
        auto_check_updates: Whether to check for updates on startup
        backup_before_update: Whether to backup before installing updates
    """

    goldendict_path: Optional[Path] = None
    installed_version: str = "unknown"
    auto_check_updates: bool = True
    backup_before_update: bool = True

    def to_dict(self) -> dict:
        """Convert config to dictionary for JSON serialization."""
        return {
            "goldendict_path": str(self.goldendict_path)
            if self.goldendict_path
            else None,
            "installed_version": self.installed_version,
            "auto_check_updates": self.auto_check_updates,
            "backup_before_update": self.backup_before_update,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        """Create Config from dictionary (JSON deserialization)."""
        path_str = data.get("goldendict_path")
        return cls(
            goldendict_path=Path(path_str) if path_str else None,
            installed_version=data.get("installed_version", "unknown"),
            auto_check_updates=data.get("auto_check_updates", True),
            backup_before_update=data.get("backup_before_update", True),
        )


class ConfigManager:
    """Manages configuration file I/O and validation.

    Handles cross-platform config directory detection and provides
    methods for loading and saving configuration.
    """

    CONFIG_FILENAME = "config.json"

    def __init__(self, config_dir: Optional[Path] = None) -> None:
        """Initialize the config manager.

        Args:
            config_dir: Optional custom config directory. If not provided,
                       uses platform-specific default location.
        """
        if config_dir:
            self.config_dir = config_dir
        else:
            self.config_dir = self._get_default_config_dir()

        self.config_file = self.config_dir / self.CONFIG_FILENAME

    def _get_default_config_dir(self) -> Path:
        r"""Get the default configuration directory for the current platform.

        Returns:
            Path to the configuration directory

        Platform locations:
            - Windows: %APPDATA%\dpd-updater\
            - macOS: ~/Library/Application Support/dpd-updater/
            - Linux: ~/.config/dpd-updater/
        """
        system = platform.system()

        if system == "Windows":
            app_data = Path.home() / "AppData" / "Roaming"
            return app_data / "dpd-updater"
        elif system == "Darwin":  # macOS
            return Path.home() / "Library" / "Application Support" / "dpd-updater"
        else:  # Linux and other Unix-like
            return Path.home() / ".config" / "dpd-updater"

    def _ensure_config_dir_exists(self) -> None:
        """Create the configuration directory if it doesn't exist."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def load_config(self) -> Config:
        """Load configuration from file.

        Returns:
            Config object with loaded values, or default Config if file doesn't exist
        """
        if not self.config_file.exists():
            return Config()

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Config.from_dict(data)
        except (json.JSONDecodeError, KeyError, TypeError):
            # If config file is corrupted, return default config
            return Config()

    def save_config(self, config: Config) -> None:
        """Save configuration to file.

        Args:
            config: Config object to save
        """
        self._ensure_config_dir_exists()

        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config.to_dict(), f, indent=2)

    def validate_goldendict_path(self, path: Path) -> tuple[bool, str]:
        """Validate that a path is a valid GoldenDict folder.

        Args:
            path: Path to validate

        Returns:
            Tuple of (is_valid, message)
        """
        if not path.exists():
            return False, f"Path does not exist: {path}"

        if not path.is_dir():
            return False, f"Path is not a directory: {path}"

        # Check if user selected a DPD subfolder instead of parent
        dpd_folders = ["dpd", "dpd-grammar", "dpd-deconstructor", "dpd-deconstructor2", "dpd-variants"]
        if path.name.lower() in [f.lower() for f in dpd_folders]:
            parent = path.parent
            return (
                True,
                f"⚠ You selected the '{path.name}' folder. Using parent folder: {parent}",
            )

        # Check for common GoldenDict indicators
        # GoldenDict content folder typically contains dictionary files
        # or subdirectories with dictionary files
        contents = list(path.iterdir())

        if not contents:
            return (
                False,
                "Directory is empty. Please select a folder containing dictionaries.",
            )

        # Look for common dictionary file extensions or folders
        dict_indicators = [".ifo", ".dsl", ".zip", ".dz", ".idx"]
        has_dict_files = any(
            any(f.suffix.lower() == ext for ext in dict_indicators)
            for f in contents
            if f.is_file()
        )

        if not has_dict_files and not any(f.is_dir() for f in contents):
            return False, "No dictionary files found in this folder."

        return True, "Valid GoldenDict folder"
