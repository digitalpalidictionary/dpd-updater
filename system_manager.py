"""System-level operations for the DPD Updater.

This module handles detecting, closing, and reopening GoldenDict
in a cross-platform manner.
"""

import platform
import subprocess
import time
from pathlib import Path
from typing import Optional

import psutil


class GoldenDictManager:
    """Manages GoldenDict process detection and control.

    Provides methods to check if GoldenDict is running, close it gracefully,
    and reopen it after updates. Works cross-platform (Windows, macOS, Linux).
    """

    def __init__(self) -> None:
        """Initialize the GoldenDict manager."""
        self.process_name_patterns = [
            "goldendict",
            "GoldenDict",
            "GoldenDict.exe",
            "goldendict.exe",
        ]

    def is_running(self) -> bool:
        """Check if GoldenDict is currently running.

        Returns:
            True if GoldenDict process is found, False otherwise
        """
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                proc_name = proc.info["name"]
                if proc_name and any(
                    pattern.lower() in proc_name.lower()
                    for pattern in self.process_name_patterns
                ):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False

    def close(self, timeout: int = 10) -> bool:
        """Close GoldenDict gracefully, with forceful termination as fallback.

        Args:
            timeout: Seconds to wait for graceful shutdown before force kill

        Returns:
            True if GoldenDict was closed successfully, False otherwise
        """
        if not self.is_running():
            return True

        # First try graceful termination (SIGTERM / Ctrl+C equivalent)
        self._terminate_gracefully()

        # Wait for process to close
        start_time = time.time()
        while time.time() - start_time < timeout:
            if not self.is_running():
                return True
            time.sleep(0.5)

        # If still running, force kill
        self._kill_forcefully()

        # Final check
        return not self.is_running()

    def _terminate_gracefully(self) -> None:
        """Send graceful termination signal to GoldenDict processes."""
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                proc_name = proc.info["name"]
                if proc_name and any(
                    pattern.lower() in proc_name.lower()
                    for pattern in self.process_name_patterns
                ):
                    proc.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

    def _kill_forcefully(self) -> None:
        """Force kill GoldenDict processes."""
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                proc_name = proc.info["name"]
                if proc_name and any(
                    pattern.lower() in proc_name.lower()
                    for pattern in self.process_name_patterns
                ):
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

    def reopen(self) -> bool:
        """Reopen GoldenDict after update.

        Returns:
            True if GoldenDict was launched successfully, False otherwise
        """
        try:
            executable = self._find_executable()
            if executable:
                subprocess.Popen(
                    [str(executable)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                return True
            return False
        except Exception:
            return False

    def _find_executable(self) -> Optional[Path]:
        """Find GoldenDict executable path based on platform.

        Returns:
            Path to GoldenDict executable or None if not found
        """
        system = platform.system()

        if system == "Windows":
            return self._find_windows_executable()
        elif system == "Darwin":  # macOS
            return self._find_macos_executable()
        else:  # Linux
            return self._find_linux_executable()

    def _find_windows_executable(self) -> Optional[Path]:
        """Find GoldenDict executable on Windows."""
        common_paths = [
            Path("C:/Program Files/GoldenDict/GoldenDict.exe"),
            Path("C:/Program Files (x86)/GoldenDict/GoldenDict.exe"),
            Path.home() / "AppData/Local/GoldenDict/GoldenDict.exe",
        ]

        # Also check PATH
        try:
            result = subprocess.run(
                ["where", "goldendict"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                path = result.stdout.strip().split("\n")[0]
                if path:
                    return Path(path)
        except Exception:
            pass

        for path in common_paths:
            if path.exists():
                return path

        return None

    def _find_macos_executable(self) -> Optional[Path]:
        """Find GoldenDict executable on macOS."""
        common_paths = [
            Path("/Applications/GoldenDict.app/Contents/MacOS/GoldenDict"),
            Path.home() / "Applications/GoldenDict.app/Contents/MacOS/GoldenDict",
        ]

        # Also check PATH
        try:
            result = subprocess.run(
                ["which", "goldendict"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                path = result.stdout.strip()
                if path:
                    return Path(path)
        except Exception:
            pass

        for path in common_paths:
            if path.exists():
                return path

        return None

    def _find_linux_executable(self) -> Optional[Path]:
        """Find GoldenDict executable on Linux."""
        # Check PATH first
        try:
            result = subprocess.run(
                ["which", "goldendict"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                path = result.stdout.strip()
                if path:
                    return Path(path)
        except Exception:
            pass

        # Check common locations
        common_paths = [
            Path("/usr/bin/goldendict"),
            Path("/usr/local/bin/goldendict"),
            Path("/opt/goldendict/goldendict"),
            Path.home() / ".local/bin/goldendict",
        ]

        for path in common_paths:
            if path.exists():
                return path

        return None
