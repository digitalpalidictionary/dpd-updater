"""Main entry point for the DPD Updater GUI application.

This module provides the main application window and coordinates between
the setup wizard and main UI components.
"""

import flet as ft

from config import Config, ConfigManager
from ui_setup import SetupWizard
from ui_main import MainWindow
from utils import scan_for_changes


class DPDUpdaterApp:
    """Main application controller for the DPD Updater."""

    def __init__(self) -> None:
        """Initialize the application."""
        self.config_manager: ConfigManager = None  # type: ignore
        self.config: Config = None  # type: ignore
        self.page: ft.Page = None  # type: ignore

    def main(self, page: ft.Page) -> None:
        """Main application entry point.

        Args:
            page: The Flet page object
        """
        self.page = page
        self.page.title = "DPD Updater"
        self.page.theme_mode = ft.ThemeMode.SYSTEM
        self.page.padding = 20
        self.page.window.width = 800
        self.page.window.height = 600

        # Add keyboard shortcut to quit (Ctrl+Q)
        self.page.on_keyboard_event = self._on_keyboard

        # Initialize configuration
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()

        # Check if this is first run (no GoldenDict path configured)
        if not self.config.goldendict_path:
            self._show_setup_wizard()
        else:
            # Scan for changes in GoldenDict folder
            self._scan_and_update_state()
            self._show_main_window()

    def _scan_and_update_state(self) -> None:
        """Scan GoldenDict folder for changes and update config if needed."""
        if not self.config.goldendict_path:
            return

        has_changed, detected_version = scan_for_changes(
            self.config.goldendict_path, self.config.installed_version
        )

        if has_changed:
            if detected_version is None:
                # DPD was removed
                self.config.installed_version = "unknown"
                self.config_manager.save_config(self.config)
            else:
                # DPD version changed or was installed
                self.config.installed_version = detected_version
                self.config_manager.save_config(self.config)

    def _on_keyboard(self, e: ft.KeyboardEvent) -> None:
        """Handle keyboard shortcuts.

        Args:
            e: Keyboard event
        """
        # Ctrl+Q to quit
        if e.key == "Q" and e.ctrl:
            self.page.window.close()

    def _show_setup_wizard(self) -> None:
        """Display the first-time setup wizard."""

        def on_setup_complete(config: Config) -> None:
            """Callback when setup is completed."""
            self.config = config
            self._show_main_window()

        wizard = SetupWizard(
            page=self.page,
            on_complete=on_setup_complete,
            config_manager=self.config_manager,
        )
        wizard.show()

    def _show_main_window(self) -> None:
        """Display the main application window."""
        main_window = MainWindow(
            page=self.page, config=self.config, config_manager=self.config_manager
        )
        main_window.show()


def main() -> None:
    """Application entry point."""
    app = DPDUpdaterApp()
    ft.app(target=app.main)


if __name__ == "__main__":
    main()
