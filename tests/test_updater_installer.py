"""Tests for the DPD Updater installer module.

Tests cover download, backup, and installation functionality.
"""

import tempfile
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests

from exporter.updater.config import Config
from exporter.updater.installer import Installer


class TestInstaller:
    """Tests for the Installer class."""
    
    def test_init_with_config(self) -> None:
        """Test installer initialization with config."""
        config = Config(goldendict_path=Path("/test/goldendict"))
        installer = Installer(config=config)
        
        assert installer.config == config
        assert installer.progress_callback is None
    
    def test_init_with_callback(self) -> None:
        """Test installer initialization with progress callback."""
        config = Config()
        callback = Mock()
        installer = Installer(config=config, progress_callback=callback)
        
        assert installer.progress_callback == callback
    
    def test_report_progress_with_callback(self) -> None:
        """Test that progress is reported via callback."""
        config = Config()
        callback = Mock()
        installer = Installer(config=config, progress_callback=callback)
        
        installer._report_progress("Testing", 50)
        
        callback.assert_called_once_with("Testing", 50)
    
    def test_report_progress_without_callback(self) -> None:
        """Test that progress reporting works without callback."""
        config = Config()
        installer = Installer(config=config, progress_callback=None)
        
        # Should not raise
        installer._report_progress("Testing", 50)
    
    @patch("requests.Session")
    def test_download_release_success(self, mock_session_class: Mock) -> None:
        """Test successful download of release asset."""
        # Mock the session and response
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.headers = {"content-length": "1000"}
        mock_response.iter_content.return_value = [b"test data" * 100]
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response
        
        config = Config()
        installer = Installer(config=config)
        installer.session = mock_session
        
        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir)
            url = "https://github.com/test/dpd-goldendict-v2.5.1.zip"
            
            result = installer.download_release(url, dest, chunk_size=100)
            
            assert result.exists()
            assert result.name == "dpd-goldendict-v2.5.1.zip"
            mock_session.get.assert_called_once_with(url, stream=True, timeout=300)
    
    def test_get_filename_from_response_content_disposition(self) -> None:
        """Test extracting filename from Content-Disposition header."""
        config = Config()
        installer = Installer(config=config)
        
        mock_response = Mock()
        mock_response.headers = {
            "content-disposition": 'attachment; filename="dpd-v2.5.1.zip"'
        }
        
        result = installer._get_filename_from_response(
            mock_response, "https://example.com/download"
        )
        
        assert result == "dpd-v2.5.1.zip"
    
    def test_get_filename_from_url(self) -> None:
        """Test extracting filename from URL when no header."""
        config = Config()
        installer = Installer(config=config)
        
        mock_response = Mock()
        mock_response.headers = {}
        
        result = installer._get_filename_from_response(
            mock_response, "https://example.com/dpd-v2.5.1.zip"
        )
        
        assert result == "dpd-v2.5.1.zip"
    
    def test_get_filename_fallback(self) -> None:
        """Test fallback filename when URL has no path."""
        config = Config()
        installer = Installer(config=config)
        
        mock_response = Mock()
        mock_response.headers = {}
        
        result = installer._get_filename_from_response(
            mock_response, "https://example.com/"
        )
        
        assert result == "dpd-update.zip"
    
    def test_format_size_bytes(self) -> None:
        """Test formatting byte sizes."""
        config = Config()
        installer = Installer(config=config)
        
        assert installer._format_size(500) == "500.0 B"
        assert installer._format_size(1024) == "1.0 KB"
        assert installer._format_size(1536) == "1.5 KB"
        assert installer._format_size(1024 * 1024) == "1.0 MB"
        assert installer._format_size(1024 * 1024 * 1024) == "1.0 GB"
    
    def test_backup_existing_disabled(self) -> None:
        """Test backup is skipped when disabled."""
        config = Config(backup_before_update=False)
        installer = Installer(config=config)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            result = installer.backup_existing(Path(tmpdir))
            assert result is None
    
    def test_backup_existing_no_dpd_files(self) -> None:
        """Test backup returns None when no DPD files found."""
        config = Config(backup_before_update=True)
        installer = Installer(config=config)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            gd_path = Path(tmpdir) / "goldendict"
            gd_path.mkdir()
            (gd_path / "other-dict.ifo").write_text("test")
            
            result = installer.backup_existing(gd_path)
            
            assert result is None
            # Backup dir should be removed
            assert not (gd_path / "backup_").exists()
    
    def test_backup_existing_with_dpd_files(self) -> None:
        """Test backup creates backup of DPD files."""
        config = Config(backup_before_update=True)
        installer = Installer(config=config)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            gd_path = Path(tmpdir) / "goldendict"
            gd_path.mkdir()
            (gd_path / "dpd.ifo").write_text("test ifo")
            (gd_path / "dpd.idx").write_text("test idx")
            
            result = installer.backup_existing(gd_path)
            
            assert result is not None
            assert result.exists()
            assert "backup_" in result.name
            assert (result / "dpd.ifo").exists()
            assert (result / "dpd.idx").exists()
    
    def test_backup_existing_with_dpd_folder(self) -> None:
        """Test backup creates backup of DPD folder."""
        config = Config(backup_before_update=True)
        installer = Installer(config=config)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            gd_path = Path(tmpdir) / "goldendict"
            gd_path.mkdir()
            dpd_folder = gd_path / "dpd-data"
            dpd_folder.mkdir()
            (dpd_folder / "file.txt").write_text("test")
            
            result = installer.backup_existing(gd_path)
            
            assert result is not None
            assert (result / "dpd-data" / "file.txt").exists()
    
    def test_install_update_success(self) -> None:
        """Test successful installation of update."""
        config = Config()
        installer = Installer(config=config)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a zip file to extract
            download_path = Path(tmpdir) / "download.zip"
            goldendict_path = Path(tmpdir) / "goldendict"
            goldendict_path.mkdir()

            # Create zip with test content (simulating actual release structure with multiple folders)
            with zipfile.ZipFile(download_path, "w") as zf:
                zf.writestr("dpd/", "")  # Directory
                zf.writestr("dpd/test.txt", "test content")
                zf.writestr("dpd-grammar/", "")  # Second folder
                zf.writestr("dpd-grammar/test.txt", "grammar content")

            installer.install_update(download_path, goldendict_path)

            # Verify files were extracted
            assert (goldendict_path / "dpd" / "test.txt").exists()
            assert (goldendict_path / "dpd" / "test.txt").read_text() == "test content"
            assert (goldendict_path / "dpd-grammar" / "test.txt").exists()
            # Download file should be removed
            assert not download_path.exists()
    
    def test_install_update_replaces_existing(self) -> None:
        """Test that install replaces existing files."""
        config = Config()
        installer = Installer(config=config)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            download_path = Path(tmpdir) / "download.zip"
            goldendict_path = Path(tmpdir) / "goldendict"
            goldendict_path.mkdir()
            
            # Create existing file
            existing_dir = goldendict_path / "dpd"
            existing_dir.mkdir()
            (existing_dir / "old.txt").write_text("old content")
            
            # Create zip with new content
            with zipfile.ZipFile(download_path, "w") as zf:
                zf.writestr("dpd/", "")
                zf.writestr("dpd/new.txt", "new content")
            
            installer.install_update(download_path, goldendict_path)
            
            # Old file should be gone
            assert not (goldendict_path / "dpd" / "old.txt").exists()
            # New file should exist
            assert (goldendict_path / "dpd" / "new.txt").exists()
    
    def test_install_update_with_dpd_folders(self) -> None:
        """Test install handles zip with dpd and dpd-grammar folders (actual release structure)."""
        config = Config()
        installer = Installer(config=config)

        with tempfile.TemporaryDirectory() as tmpdir:
            download_path = Path(tmpdir) / "download.zip"
            goldendict_path = Path(tmpdir) / "goldendict"
            goldendict_path.mkdir()

            # Create zip matching actual release structure
            with zipfile.ZipFile(download_path, "w") as zf:
                zf.writestr("dpd/", "")
                zf.writestr("dpd/dpd.ifo", "test ifo")
                zf.writestr("dpd/dpd.idx", "test idx")
                zf.writestr("dpd/res/", "")
                zf.writestr("dpd/res/style.css", "test css")
                zf.writestr("dpd-grammar/", "")
                zf.writestr("dpd-grammar/dpd-grammar.ifo", "grammar ifo")

            installer.install_update(download_path, goldendict_path)

            # Should extract both folders directly
            assert (goldendict_path / "dpd" / "dpd.ifo").exists()
            assert (goldendict_path / "dpd" / "res" / "style.css").exists()
            assert (goldendict_path / "dpd-grammar" / "dpd-grammar.ifo").exists()
    
    def test_update_dpd_no_path_configured(self) -> None:
        """Test update fails when no GoldenDict path configured."""
        config = Config(goldendict_path=None)
        installer = Installer(config=config)
        
        with pytest.raises(ValueError, match="GoldenDict path not configured"):
            installer.update_dpd("https://example.com/download.zip", "v2.5.1")
    
    @patch("exporter.updater.installer.Installer.download_release")
    @patch("exporter.updater.installer.Installer.backup_existing")
    @patch("exporter.updater.installer.Installer.install_update")
    def test_update_dpd_success(
        self,
        mock_install: Mock,
        mock_backup: Mock,
        mock_download: Mock
    ) -> None:
        """Test successful full update process."""
        with tempfile.TemporaryDirectory() as tmpdir:
            gd_path = Path(tmpdir)
            download_path = gd_path / "temp" / "download.zip"
            download_path.parent.mkdir()
            mock_download.return_value = download_path
            
            config = Config(goldendict_path=gd_path)
            installer = Installer(config=config)
            
            result = installer.update_dpd("https://example.com/download.zip", "v2.5.1")
            
            assert result is True
            mock_download.assert_called_once()
            mock_backup.assert_called_once()
            mock_install.assert_called_once()
    
    @patch("exporter.updater.installer.Installer.download_release")
    def test_update_dpd_cleanup_on_failure(self, mock_download: Mock) -> None:
        """Test that temp directory is cleaned up on failure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            gd_path = Path(tmpdir)
            config = Config(goldendict_path=gd_path)
            installer = Installer(config=config)
            
            # Make download fail
            mock_download.side_effect = Exception("Download failed")
            
            with pytest.raises(Exception):
                installer.update_dpd("https://example.com/download.zip", "v2.5.1")
            
            # Temp directory should be cleaned up
            assert not (gd_path / "_dpd_download_temp").exists()
