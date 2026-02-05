"""Main application UI for the DPD Updater.

Provides the main window interface for checking and installing DPD updates.
"""

from pathlib import Path
from typing import Optional

import flet as ft

from config import Config, ConfigManager
from github_client import GitHubClient, ReleaseInfo
from installer import Installer
from system_manager import GoldenDictManager


class MainWindow:
    """Main application window for the DPD Updater.

    Displays:
    - Current and latest version information
    - Update status and notifications
    - Settings and configuration options
    """

    def __init__(
        self, page: ft.Page, config: Config, config_manager: ConfigManager
    ) -> None:
        """Initialize the main window.

        Args:
            page: The Flet page object
            config: Current configuration
            config_manager: Configuration manager instance
        """
        self.page = page
        self.config = config
        self.config_manager = config_manager
        self.github_client = GitHubClient()

        self.latest_release: Optional[ReleaseInfo] = None
        self.is_checking: bool = False
        self.is_updating: bool = False

        # UI Components
        self.current_version_text = ft.Text(
            f"Installed: {config.installed_version}", size=16
        )
        self.latest_version_text = ft.Text(
            "Latest: Checking...", size=16, color=ft.Colors.GREY_400
        )
        self.status_text = ft.Text("", size=14, weight=ft.FontWeight.BOLD)

        self.check_button = ft.ElevatedButton(
            "Check for Updates", on_click=self._on_check_updates, icon=ft.Icons.REFRESH
        )
        self.update_button = ft.ElevatedButton(
            "Update Now",
            on_click=self._on_update,
            icon=ft.Icons.DOWNLOAD,
            disabled=True,
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.GREEN_600,
        )

        self.progress_bar = ft.ProgressBar(width=400, visible=False)
        self.progress_text = ft.Text("", size=12)

    def show(self) -> None:
        """Display the main application window."""
        self.page.clean()

        # Header
        header = ft.Row(
            [
                ft.Icon(ft.Icons.BOOK, size=40, color=ft.Colors.BLUE_400),
                ft.Text("DPD Updater", size=32, weight=ft.FontWeight.BOLD),
            ]
        )

        # Version info section
        version_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            "Version Information", weight=ft.FontWeight.BOLD, size=18
                        ),
                        self.current_version_text,
                        self.latest_version_text,
                        ft.Divider(),
                        self.status_text,
                        ft.Container(height=10),
                    ]
                ),
                padding=20,
            )
        )

        # Progress section
        progress_section = ft.Column(
            [self.progress_text, self.progress_bar], visible=False
        )
        self.progress_section = progress_section

        # Action buttons
        button_row = ft.Row(
            [self.check_button, self.update_button],
            alignment=ft.MainAxisAlignment.CENTER,
        )

        # Settings section
        settings_button = ft.TextButton(
            "Settings", on_click=self._on_settings, icon=ft.Icons.SETTINGS
        )

        # Main content
        content = ft.Column(
            [
                header,
                ft.Divider(),
                version_card,
                ft.Container(height=20),
                progress_section,
                ft.Container(height=10),
                button_row,
                ft.Container(expand=True),
                ft.Row(
                    [
                        settings_button,
                        ft.Container(expand=True),
                        ft.Text(
                            f"GoldenDict: {self.config.goldendict_path}",
                            size=11,
                            color=ft.Colors.GREY_500,
                            italic=True,
                        ),
                    ]
                ),
            ],
            expand=True,
        )

        self.page.add(content)

        # Auto-check on startup if enabled
        if self.config.auto_check_updates:
            self._check_updates()

    def _check_updates(self) -> None:
        """Check for available updates from GitHub."""
        if self.is_checking:
            return

        self.is_checking = True
        self.check_button.disabled = True
        self.status_text.value = "Checking for updates..."
        self.status_text.color = ft.Colors.BLUE_400
        self.page.update()

        try:
            # First, rescan GoldenDict folder to detect any local changes
            if self.config.goldendict_path:
                from utils import detect_installed_version
                detected_version = detect_installed_version(self.config.goldendict_path)
                if detected_version and detected_version != self.config.installed_version:
                    self.config.installed_version = detected_version
                    self.config_manager.save_config(self.config)
                    self.current_version_text.value = f"Installed: {self.config.installed_version}"
                    self.page.update()

            self.latest_release = self.github_client.get_latest_release()

            latest_version = self.latest_release.version
            current_version = self.config.installed_version

            self.latest_version_text.value = f"Latest: {latest_version}"
            self.latest_version_text.color = ft.Colors.GREEN_400

            # Compare build dates to determine status
            # Use local build date (from .ifo file) vs GitHub release date
            local_date = current_version if "T" in current_version else "1970-01-01T00:00:00"
            github_date = self.latest_release.published_at
            comparison = -1 if local_date < github_date else (1 if local_date > github_date else 0)

            if comparison < 0:
                # GitHub has newer version
                self.status_text.value = "✓ Update available!"
                self.status_text.color = ft.Colors.GREEN_600

                # Enable update button
                if self.latest_release.asset_url:
                    self.update_button.disabled = False
                else:
                    self.status_text.value = "⚠ No download available"
                    self.status_text.color = ft.Colors.ORANGE_400

            elif comparison > 0:
                # Local version is newer than GitHub
                self.status_text.value = "✓ You have a newer version than GitHub"
                self.status_text.color = ft.Colors.BLUE_400
                self.update_button.disabled = True

            else:
                # Versions are equal
                self.status_text.value = "✓ You are up to date"
                self.status_text.color = ft.Colors.GREEN_400
                self.update_button.disabled = True

        except Exception as e:
            self.status_text.value = f"✗ Error: {str(e)}"
            self.status_text.color = ft.Colors.RED_400
            self.latest_version_text.value = "Latest: Unknown"

        finally:
            self.is_checking = False
            self.check_button.disabled = False
            self.page.update()

    def _on_check_updates(self, e: ft.ControlEvent) -> None:
        """Handle check for updates button click."""
        self._check_updates()

    def _on_update(self, e: ft.ControlEvent) -> None:
        """Handle update button click."""
        if not self.latest_release or not self.latest_release.asset_url:
            return

        self.is_updating = True
        self.update_button.disabled = True
        self.check_button.disabled = True
        self.progress_section.visible = True
        self.page.update()

        gd_manager = GoldenDictManager()

        def progress_callback(message: str, percentage: int) -> None:
            """Update progress UI."""
            self.progress_text.value = message
            self.progress_bar.value = percentage / 100
            self.page.update()

        try:
            # Step 1: Close GoldenDict if running
            if gd_manager.is_running():
                self.progress_text.value = "Closing GoldenDict..."
                self.page.update()
                if not gd_manager.close():
                    raise RuntimeError("Failed to close GoldenDict. Please close it manually and try again.")

            # Step 2: Download and install update
            installer = Installer(
                config=self.config, progress_callback=progress_callback
            )

            success = installer.update_dpd(
                download_url=self.latest_release.asset_url,
                new_version=self.latest_release.version,
            )

            if success:
                # Update config with new version
                self.config.installed_version = self.latest_release.version
                self.config_manager.save_config(self.config)

                self.current_version_text.value = (
                    f"Installed: {self.config.installed_version}"
                )
                self.status_text.value = "Restarting GoldenDict..."
                self.status_text.color = ft.Colors.GREEN_600
                self.page.update()

                # Step 3: Reopen GoldenDict to trigger re-indexing
                if gd_manager.reopen():
                    self.status_text.value = "✓ GoldenDict restarted. The dictionary will be re-indexed."
                else:
                    self.status_text.value = "✓ Update complete. Please start GoldenDict manually."

                self.update_button.disabled = True

        except Exception as exc:
            self.status_text.value = f"✗ Update failed: {str(exc)}"
            self.status_text.color = ft.Colors.RED_400

        finally:
            self.is_updating = False
            self.check_button.disabled = False
            self.progress_section.visible = False
            self.page.update()

    def _on_settings(self, e: ft.ControlEvent) -> None:
        """Handle settings button click."""

        def on_path_change(e: ft.FilePickerResultEvent) -> None:
            if e.path:
                new_path = Path(e.path)
                is_valid, message = self.config_manager.validate_goldendict_path(
                    new_path
                )

                if is_valid:
                    self.config.goldendict_path = new_path
                    self.config_manager.save_config(self.config)
                    self.page.update()
                    dialog.open = False
                    self.show()  # Refresh UI
                else:
                    # Show error
                    pass

        def on_auto_check_change(e: ft.ControlEvent) -> None:
            self.config.auto_check_updates = e.control.value
            self.config_manager.save_config(self.config)

        def on_backup_change(e: ft.ControlEvent) -> None:
            self.config.backup_before_update = e.control.value
            self.config_manager.save_config(self.config)

        file_picker = ft.FilePicker(on_result=on_path_change)
        self.page.overlay.append(file_picker)

        dialog = ft.AlertDialog(
            title=ft.Text("Settings"),
            content=ft.Column(
                [
                    ft.Text("GoldenDict Folder:", weight=ft.FontWeight.BOLD),
                    ft.Text(str(self.config.goldendict_path), size=12),
                    ft.TextButton(
                        "Change Folder",
                        on_click=lambda _: file_picker.get_directory_path(),
                    ),
                    ft.Divider(),
                    ft.Checkbox(
                        label="Check for updates on startup",
                        value=self.config.auto_check_updates,
                        on_change=on_auto_check_change,
                    ),
                    ft.Checkbox(
                        label="Create backup before updating",
                        value=self.config.backup_before_update,
                        on_change=on_backup_change,
                    ),
                ],
                tight=True,
            ),
            actions=[
                ft.TextButton(
                    "Close", on_click=lambda _: self.page.close(dialog)
                )
            ],
        )

        self.page.open(dialog)
