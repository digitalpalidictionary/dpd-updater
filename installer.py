"""Download and installation logic for the DPD Updater.

This module handles downloading DPD releases, backing up existing installations,
and extracting new versions to the GoldenDict folder.
"""

import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import urlparse

import requests

from config import Config


class Installer:
    """Handles download, backup, and installation of DPD updates.

    Provides progress callbacks for UI updates during long-running operations.
    """

    def __init__(
        self,
        config: Config,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> None:
        """Initialize the installer.

        Args:
            config: Configuration object with GoldenDict path
            progress_callback: Optional callback for progress updates.
                              Called with (message, percentage)
        """
        self.config = config
        self.progress_callback = progress_callback
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "DPD-Updater/1.0"})

    def _report_progress(self, message: str, percentage: int) -> None:
        """Report progress via callback if set.

        Args:
            message: Status message to display
            percentage: Progress percentage (0-100)
        """
        if self.progress_callback:
            self.progress_callback(message, percentage)

    def download_release(
        self, url: str, destination: Path, chunk_size: int = 8192
    ) -> Path:
        """Download a release asset from URL.

        Args:
            url: The download URL
            destination: Directory to save the file
            chunk_size: Size of download chunks in bytes

        Returns:
            Path to the downloaded file

        Raises:
            requests.RequestException: If download fails
        """
        self._report_progress("Starting download...", 0)

        response = self.session.get(url, stream=True, timeout=300)
        response.raise_for_status()

        # Get filename from URL or Content-Disposition header
        filename = self._get_filename_from_response(response, url)
        download_path = destination / filename

        # Get total size for progress calculation
        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0

        with open(download_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)

                    if total_size > 0:
                        percentage = int((downloaded / total_size) * 50)
                        self._report_progress(
                            f"Downloading... {self._format_size(downloaded)} / {self._format_size(total_size)}",
                            percentage,
                        )

        self._report_progress("Download complete", 50)
        return download_path

    def _get_filename_from_response(self, response, url: str) -> str:
        """Extract filename from response headers or URL.

        Args:
            response: The HTTP response object
            url: The request URL

        Returns:
            The filename to use for the downloaded file
        """
        # Try Content-Disposition header first
        content_disposition = response.headers.get("content-disposition", "")
        if "filename=" in content_disposition:
            filename = content_disposition.split("filename=")[-1].strip("\"'")
            return filename

        # Fallback to URL path
        parsed = urlparse(url)
        return Path(parsed.path).name or "dpd-update.zip"

    def _format_size(self, size_bytes: int) -> str:
        """Format byte size as human-readable string.

        Args:
            size_bytes: Size in bytes

        Returns:
            Human-readable size string (e.g., "1.5 MB")
        """
        size = float(size_bytes)
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def backup_existing(self, goldendict_path: Path) -> Optional[Path]:
        """Create a backup of existing DPD files.

        Args:
            goldendict_path: Path to GoldenDict folder

        Returns:
            Path to backup folder, or None if backup is disabled or no DPD files found
        """
        if not self.config.backup_before_update:
            return None

        self._report_progress("Creating backup...", 51)

        # Create backup folder with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = goldendict_path / f"backup_{timestamp}"
        backup_dir.mkdir(exist_ok=True)

        # Find and backup existing DPD files (look for dpd* files/directories)
        backed_up = False
        for item in goldendict_path.iterdir():
            if item.name.startswith("dpd") and item.name != backup_dir.name:
                if item.is_file():
                    shutil.copy2(item, backup_dir)
                    backed_up = True
                elif item.is_dir():
                    shutil.copytree(item, backup_dir / item.name)
                    backed_up = True

        if backed_up:
            self._report_progress(f"Backup created: {backup_dir.name}", 55)
            return backup_dir
        else:
            # No DPD files found, remove empty backup dir
            backup_dir.rmdir()
            return None

    def install_update(self, download_path: Path, goldendict_path: Path) -> None:
        """Extract and install the downloaded update.

        Args:
            download_path: Path to the downloaded zip file
            goldendict_path: Path to GoldenDict folder for installation

        Raises:
            zipfile.BadZipFile: If the downloaded file is not a valid zip
        """
        self._report_progress("Extracting files...", 60)

        # Extract to a temporary directory first
        extract_dir = goldendict_path / "_dpd_update_temp"
        if extract_dir.exists():
            shutil.rmtree(extract_dir)

        with zipfile.ZipFile(download_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)

        self._report_progress("Installing files...", 80)

        # Copy all items from extract_dir to GoldenDict folder
        for item in extract_dir.iterdir():
            dest = goldendict_path / item.name

            # Remove existing item if present
            if dest.exists():
                if dest.is_file():
                    dest.unlink()
                elif dest.is_dir():
                    shutil.rmtree(dest)

            # Move new item
            if item.is_file():
                shutil.move(str(item), str(dest))
            elif item.is_dir():
                shutil.move(str(item), str(dest))

        # Cleanup
        shutil.rmtree(extract_dir)
        download_path.unlink()

        self._report_progress("Installation complete!", 100)

    def update_dpd(self, download_url: str, new_version: str) -> bool:
        """Perform full update process: download, backup, install.

        Args:
            download_url: URL to download the update from
            new_version: The version being installed

        Returns:
            True if update was successful, False otherwise
        """
        try:
            if not self.config.goldendict_path:
                raise ValueError("GoldenDict path not configured")

            goldendict_path = Path(self.config.goldendict_path)

            # Create temp directory for download
            temp_dir = goldendict_path / "_dpd_download_temp"
            temp_dir.mkdir(exist_ok=True)

            try:
                # Download
                download_path = self.download_release(download_url, temp_dir)

                # Backup
                self.backup_existing(goldendict_path)

                # Install
                self.install_update(download_path, goldendict_path)

                return True

            finally:
                # Cleanup temp directory
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)

        except Exception as e:
            self._report_progress(f"Update failed: {str(e)}", 0)
            raise
