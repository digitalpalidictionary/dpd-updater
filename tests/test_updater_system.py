"""Tests for the DPD Updater system manager module.

Tests cover GoldenDict process detection, closing, and reopening.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from exporter.updater.system_manager import GoldenDictManager


class TestGoldenDictManager:
    """Tests for the GoldenDictManager class."""

    def test_init(self) -> None:
        """Test manager initialization."""
        manager = GoldenDictManager()
        assert "goldendict" in [p.lower() for p in manager.process_name_patterns]
        assert "GoldenDict.exe" in manager.process_name_patterns

    @patch("psutil.process_iter")
    def test_is_running_true(self, mock_process_iter: Mock) -> None:
        """Test detecting GoldenDict is running."""
        mock_proc = Mock()
        mock_proc.info = {"name": "goldendict", "pid": 1234}
        mock_process_iter.return_value = [mock_proc]

        manager = GoldenDictManager()
        assert manager.is_running() is True

    @patch("psutil.process_iter")
    def test_is_running_false(self, mock_process_iter: Mock) -> None:
        """Test detecting GoldenDict is not running."""
        mock_proc = Mock()
        mock_proc.info = {"name": "firefox", "pid": 1234}
        mock_process_iter.return_value = [mock_proc]

        manager = GoldenDictManager()
        assert manager.is_running() is False

    @patch("psutil.process_iter")
    def test_is_running_case_insensitive(self, mock_process_iter: Mock) -> None:
        """Test process detection is case insensitive."""
        mock_proc = Mock()
        mock_proc.info = {"name": "GoldenDict", "pid": 1234}
        mock_process_iter.return_value = [mock_proc]

        manager = GoldenDictManager()
        assert manager.is_running() is True

    @patch("time.sleep")
    @patch("time.time")
    @patch.object(GoldenDictManager, "is_running")
    @patch.object(GoldenDictManager, "_terminate_gracefully")
    def test_close_gracefully(
        self,
        mock_terminate: Mock,
        mock_is_running: Mock,
        mock_time: Mock,
        mock_sleep: Mock,
    ) -> None:
        """Test closing GoldenDict gracefully."""
        # Simulate process stopping after first check
        mock_is_running.side_effect = [True, True, False]
        mock_time.side_effect = [0, 0.5, 1.0, 1.5]

        manager = GoldenDictManager()
        result = manager.close(timeout=5)

        assert result is True
        mock_terminate.assert_called_once()

    @patch("time.sleep")
    @patch("time.time")
    @patch.object(GoldenDictManager, "is_running")
    @patch.object(GoldenDictManager, "_terminate_gracefully")
    @patch.object(GoldenDictManager, "_kill_forcefully")
    def test_close_force_kill(
        self,
        mock_kill: Mock,
        mock_terminate: Mock,
        mock_is_running: Mock,
        mock_time: Mock,
        mock_sleep: Mock,
    ) -> None:
        """Test force killing GoldenDict when graceful close fails."""
        # Simulate process not stopping
        mock_is_running.return_value = True
        mock_time.side_effect = list(range(100))  # Prevent infinite loop

        manager = GoldenDictManager()
        result = manager.close(timeout=2)

        assert result is False  # Process still running
        mock_terminate.assert_called_once()
        mock_kill.assert_called_once()

    @patch.object(GoldenDictManager, "is_running")
    def test_close_not_running(self, mock_is_running: Mock) -> None:
        """Test close when GoldenDict is not running."""
        mock_is_running.return_value = False

        manager = GoldenDictManager()
        result = manager.close()

        assert result is True

    @patch("psutil.process_iter")
    def test_terminate_gracefully(self, mock_process_iter: Mock) -> None:
        """Test graceful termination sends terminate signal."""
        mock_proc = Mock()
        mock_proc.info = {"name": "goldendict", "pid": 1234}
        mock_process_iter.return_value = [mock_proc]

        manager = GoldenDictManager()
        manager._terminate_gracefully()

        mock_proc.terminate.assert_called_once()

    @patch("psutil.process_iter")
    def test_kill_forcefully(self, mock_process_iter: Mock) -> None:
        """Test force kill sends kill signal."""
        mock_proc = Mock()
        mock_proc.info = {"name": "goldendict", "pid": 1234}
        mock_process_iter.return_value = [mock_proc]

        manager = GoldenDictManager()
        manager._kill_forcefully()

        mock_proc.kill.assert_called_once()

    @patch("subprocess.Popen")
    @patch.object(GoldenDictManager, "_find_executable")
    def test_reopen_success(self, mock_find_exec: Mock, mock_popen: Mock) -> None:
        """Test reopening GoldenDict successfully."""
        mock_find_exec.return_value = Path("/usr/bin/goldendict")

        manager = GoldenDictManager()
        result = manager.reopen()

        assert result is True
        mock_popen.assert_called_once()

    @patch.object(GoldenDictManager, "_find_executable")
    def test_reopen_no_executable(self, mock_find_exec: Mock) -> None:
        """Test reopen fails when executable not found."""
        mock_find_exec.return_value = None

        manager = GoldenDictManager()
        result = manager.reopen()

        assert result is False

    @patch("subprocess.Popen")
    @patch.object(GoldenDictManager, "_find_executable")
    def test_reopen_exception(self, mock_find_exec: Mock, mock_popen: Mock) -> None:
        """Test reopen handles exceptions."""
        mock_find_exec.return_value = Path("/usr/bin/goldendict")
        mock_popen.side_effect = Exception("Failed to start")

        manager = GoldenDictManager()
        result = manager.reopen()

        assert result is False

    @patch("exporter.updater.system_manager.platform.system")
    @patch.object(GoldenDictManager, "_find_windows_executable")
    def test_find_executable_windows(self, mock_find_win: Mock, mock_platform: Mock) -> None:
        """Test finding executable on Windows."""
        mock_platform.return_value = "Windows"
        mock_find_win.return_value = Path("C:/Program Files/GoldenDict/GoldenDict.exe")

        manager = GoldenDictManager()
        result = manager._find_executable()

        assert result == Path("C:/Program Files/GoldenDict/GoldenDict.exe")
        mock_find_win.assert_called_once()

    @patch("exporter.updater.system_manager.platform.system")
    @patch.object(GoldenDictManager, "_find_macos_executable")
    def test_find_executable_macos(self, mock_find_mac: Mock, mock_platform: Mock) -> None:
        """Test finding executable on macOS."""
        mock_platform.return_value = "Darwin"
        mock_find_mac.return_value = Path("/Applications/GoldenDict.app/Contents/MacOS/GoldenDict")

        manager = GoldenDictManager()
        result = manager._find_executable()

        assert result == Path("/Applications/GoldenDict.app/Contents/MacOS/GoldenDict")
        mock_find_mac.assert_called_once()

    @patch("exporter.updater.system_manager.platform.system")
    @patch.object(GoldenDictManager, "_find_linux_executable")
    def test_find_executable_linux(self, mock_find_linux: Mock, mock_platform: Mock) -> None:
        """Test finding executable on Linux."""
        mock_platform.return_value = "Linux"
        mock_find_linux.return_value = Path("/usr/bin/goldendict")

        manager = GoldenDictManager()
        result = manager._find_executable()

        assert result == Path("/usr/bin/goldendict")
        mock_find_linux.assert_called_once()

    @patch("exporter.updater.system_manager.subprocess.run")
    def test_find_linux_executable_from_path(self, mock_run: Mock) -> None:
        """Test finding Linux executable from PATH."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "/usr/bin/goldendict\n"
        mock_run.return_value = mock_result

        manager = GoldenDictManager()
        result = manager._find_linux_executable()

        assert result == Path("/usr/bin/goldendict")

    @patch("exporter.updater.system_manager.subprocess.run")
    def test_find_linux_executable_fallback(self, mock_run: Mock) -> None:
        """Test finding Linux executable from common locations."""
        mock_run.return_value = Mock(returncode=1)

        with patch.object(Path, "exists", return_value=True):
            manager = GoldenDictManager()
            result = manager._find_linux_executable()

            assert result is not None

    @patch("exporter.updater.system_manager.subprocess.run")
    def test_find_linux_executable_not_found(self, mock_run: Mock) -> None:
        """Test when Linux executable not found."""
        mock_run.return_value = Mock(returncode=1)

        with patch.object(Path, "exists", return_value=False):
            manager = GoldenDictManager()
            result = manager._find_linux_executable()

            assert result is None
