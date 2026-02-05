"""Tests for the DPD Updater configuration module.

Tests cover config file I/O, cross-platform path detection, and schema validation.
"""

import json
import platform
import tempfile
from pathlib import Path

import pytest

from exporter.updater.config import Config, ConfigManager


class TestConfig:
    """Tests for the Config dataclass."""
    
    def test_config_default_values(self) -> None:
        """Test that Config has correct default values."""
        config = Config()
        
        assert config.goldendict_path is None
        assert config.installed_version == "unknown"
        assert config.auto_check_updates is True
        assert config.backup_before_update is True
    
    def test_config_custom_values(self) -> None:
        """Test Config with custom values."""
        config = Config(
            goldendict_path=Path("/test/path"),
            installed_version="v2.5.0",
            auto_check_updates=False,
            backup_before_update=False
        )
        
        assert config.goldendict_path == Path("/test/path")
        assert config.installed_version == "v2.5.0"
        assert config.auto_check_updates is False
        assert config.backup_before_update is False
    
    def test_config_to_dict(self) -> None:
        """Test Config serialization to dictionary."""
        config = Config(
            goldendict_path=Path("/test/path"),
            installed_version="v2.5.0",
            auto_check_updates=True,
            backup_before_update=True
        )
        
        data = config.to_dict()
        
        assert data["goldendict_path"] == "/test/path"
        assert data["installed_version"] == "v2.5.0"
        assert data["auto_check_updates"] is True
        assert data["backup_before_update"] is True
    
    def test_config_to_dict_none_path(self) -> None:
        """Test Config serialization with None path."""
        config = Config(goldendict_path=None)
        data = config.to_dict()
        
        assert data["goldendict_path"] is None
    
    def test_config_from_dict(self) -> None:
        """Test Config deserialization from dictionary."""
        data = {
            "goldendict_path": "/test/path",
            "installed_version": "v2.5.0",
            "auto_check_updates": True,
            "backup_before_update": False
        }
        
        config = Config.from_dict(data)
        
        assert config.goldendict_path == Path("/test/path")
        assert config.installed_version == "v2.5.0"
        assert config.auto_check_updates is True
        assert config.backup_before_update is False
    
    def test_config_from_dict_none_path(self) -> None:
        """Test Config deserialization with None path."""
        data = {
            "goldendict_path": None,
            "installed_version": "unknown",
            "auto_check_updates": True,
            "backup_before_update": True
        }
        
        config = Config.from_dict(data)
        
        assert config.goldendict_path is None
    
    def test_config_from_dict_missing_keys(self) -> None:
        """Test Config deserialization with missing keys uses defaults."""
        data = {
            "goldendict_path": "/test/path"
        }
        
        config = Config.from_dict(data)
        
        assert config.goldendict_path == Path("/test/path")
        assert config.installed_version == "unknown"
        assert config.auto_check_updates is True
        assert config.backup_before_update is True


class TestConfigManager:
    """Tests for the ConfigManager class."""
    
    def test_get_default_config_dir_windows(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test Windows config directory detection."""
        monkeypatch.setattr(platform, "system", lambda: "Windows")
        monkeypatch.setattr(Path, "home", lambda: Path("C:/Users/TestUser"))
        
        manager = ConfigManager()
        expected = Path("C:/Users/TestUser/AppData/Roaming/dpd-updater")
        
        assert manager.config_dir == expected
    
    def test_get_default_config_dir_macos(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test macOS config directory detection."""
        monkeypatch.setattr(platform, "system", lambda: "Darwin")
        monkeypatch.setattr(Path, "home", lambda: Path("/Users/testuser"))
        
        manager = ConfigManager()
        expected = Path("/Users/testuser/Library/Application Support/dpd-updater")
        
        assert manager.config_dir == expected
    
    def test_get_default_config_dir_linux(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test Linux config directory detection."""
        monkeypatch.setattr(platform, "system", lambda: "Linux")
        monkeypatch.setattr(Path, "home", lambda: Path("/home/testuser"))
        
        manager = ConfigManager()
        expected = Path("/home/testuser/.config/dpd-updater")
        
        assert manager.config_dir == expected
    
    def test_custom_config_dir(self) -> None:
        """Test using a custom config directory."""
        custom_dir = Path("/custom/config/dir")
        manager = ConfigManager(config_dir=custom_dir)
        
        assert manager.config_dir == custom_dir
        assert manager.config_file == custom_dir / "config.json"
    
    def test_load_config_file_not_exists(self) -> None:
        """Test loading config when file doesn't exist returns defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConfigManager(config_dir=Path(tmpdir))
            config = manager.load_config()
            
            assert config.goldendict_path is None
            assert config.installed_version == "unknown"
    
    def test_load_config_success(self) -> None:
        """Test loading existing config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            config_file = config_dir / "config.json"
            
            # Create a config file
            data = {
                "goldendict_path": "/test/goldendict",
                "installed_version": "v2.5.0",
                "auto_check_updates": False,
                "backup_before_update": True
            }
            config_dir.mkdir(parents=True, exist_ok=True)
            with open(config_file, "w") as f:
                json.dump(data, f)
            
            manager = ConfigManager(config_dir=config_dir)
            config = manager.load_config()
            
            assert config.goldendict_path == Path("/test/goldendict")
            assert config.installed_version == "v2.5.0"
            assert config.auto_check_updates is False
            assert config.backup_before_update is True
    
    def test_load_config_corrupted(self) -> None:
        """Test loading corrupted config file returns defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            config_file = config_dir / "config.json"
            
            # Create a corrupted config file
            config_dir.mkdir(parents=True, exist_ok=True)
            with open(config_file, "w") as f:
                f.write("not valid json")
            
            manager = ConfigManager(config_dir=config_dir)
            config = manager.load_config()
            
            assert config.goldendict_path is None
            assert config.installed_version == "unknown"
    
    def test_save_config_creates_directory(self) -> None:
        """Test that saving config creates the directory if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "nested" / "config"
            manager = ConfigManager(config_dir=config_dir)
            
            config = Config(goldendict_path=Path("/test/path"))
            manager.save_config(config)
            
            assert config_dir.exists()
            assert (config_dir / "config.json").exists()
    
    def test_save_and_load_roundtrip(self) -> None:
        """Test that saving and loading config preserves data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConfigManager(config_dir=Path(tmpdir))
            
            original = Config(
                goldendict_path=Path("/test/goldendict"),
                installed_version="v2.5.1",
                auto_check_updates=False,
                backup_before_update=False
            )
            
            manager.save_config(original)
            loaded = manager.load_config()
            
            assert loaded.goldendict_path == original.goldendict_path
            assert loaded.installed_version == original.installed_version
            assert loaded.auto_check_updates == original.auto_check_updates
            assert loaded.backup_before_update == original.backup_before_update
    
    def test_validate_goldendict_path_nonexistent(self) -> None:
        """Test validation fails for non-existent path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConfigManager(config_dir=Path(tmpdir))
            is_valid, message = manager.validate_goldendict_path(Path("/nonexistent/path"))
            
            assert is_valid is False
            assert "does not exist" in message
    
    def test_validate_goldendict_path_not_directory(self) -> None:
        """Test validation fails for non-directory path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test")
            
            manager = ConfigManager(config_dir=Path(tmpdir))
            is_valid, message = manager.validate_goldendict_path(test_file)
            
            assert is_valid is False
            assert "not a directory" in message
    
    def test_validate_goldendict_path_empty(self) -> None:
        """Test validation fails for empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_dir = Path(tmpdir) / "empty"
            empty_dir.mkdir()
            
            manager = ConfigManager(config_dir=Path(tmpdir))
            is_valid, message = manager.validate_goldendict_path(empty_dir)
            
            assert is_valid is False
            assert "empty" in message
    
    def test_validate_goldendict_path_valid(self) -> None:
        """Test validation succeeds for valid GoldenDict folder."""
        with tempfile.TemporaryDirectory() as tmpdir:
            gd_dir = Path(tmpdir) / "goldendict"
            gd_dir.mkdir()
            (gd_dir / "dictionary.ifo").write_text("test")
            
            manager = ConfigManager(config_dir=Path(tmpdir))
            is_valid, message = manager.validate_goldendict_path(gd_dir)
            
            assert is_valid is True
            assert "Valid" in message
    
    def test_validate_goldendict_path_with_subdirs(self) -> None:
        """Test validation succeeds for folder with subdirectories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            gd_dir = Path(tmpdir) / "goldendict"
            gd_dir.mkdir()
            (gd_dir / "dictionaries").mkdir()
            
            manager = ConfigManager(config_dir=Path(tmpdir))
            is_valid, message = manager.validate_goldendict_path(gd_dir)
            
            assert is_valid is True
