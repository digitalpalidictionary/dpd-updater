"""First-time setup wizard UI for the DPD Updater.

Provides a guided setup experience for users launching the updater for the first time.
"""

from pathlib import Path
from typing import Callable, Optional

import flet as ft

from config import Config, ConfigManager


class SetupWizard:
    """First-time setup wizard for configuring the DPD Updater.

    Guides users through:
    1. Welcome/introduction
    2. GoldenDict folder selection
    3. Validation and confirmation
    """

    def __init__(
        self,
        page: ft.Page,
        on_complete: Callable[[Config], None],
        config_manager: ConfigManager,
    ) -> None:
        """Initialize the setup wizard.

        Args:
            page: The Flet page object
            on_complete: Callback when setup is completed successfully
            config_manager: Configuration manager instance
        """
        self.page = page
        self.on_complete = on_complete
        self.config_manager = config_manager
        self.selected_path: Optional[Path] = None

        # UI Components
        self.path_text = ft.Text(
            "No folder selected", italic=True, color=ft.Colors.GREY_500
        )
        self.status_text = ft.Text("", color=ft.Colors.RED_400)
        self.continue_button = ft.ElevatedButton(
            "Continue",
            on_click=self._on_continue,
            disabled=True,
            icon=ft.Icons.ARROW_FORWARD,
        )

    def show(self) -> None:
        """Display the setup wizard UI."""
        self.page.clean()

        # Welcome header
        welcome_text = ft.Text(
            "Welcome to DPD Updater", size=28, weight=ft.FontWeight.BOLD
        )

        intro_text = ft.Text(
            "This wizard will help you set up the DPD Updater for your GoldenDict installation.\n\n"
            "Please select your GoldenDict content/dictionaries folder.",
            size=14,
        )

        # Folder selection row
        select_button = ft.ElevatedButton(
            "Select Folder", on_click=self._on_select_folder, icon=ft.Icons.FOLDER_OPEN
        )

        path_row = ft.Row(
            [select_button, self.path_text], alignment=ft.MainAxisAlignment.START
        )

        # Info about what we're looking for
        info_text = ft.Text(
            "This folder should only contain subfolders with dictionaries.",
            size=12,
            color=ft.Colors.GREY_600,
            italic=True,
        )

        # Main content column
        content = ft.Column(
            [
                welcome_text,
                ft.Divider(),
                intro_text,
                ft.Container(height=20),
                ft.Text("GoldenDict Folder:", weight=ft.FontWeight.BOLD),
                path_row,
                info_text,
                ft.Container(height=10),
                self.status_text,
                ft.Container(expand=True),  # Push buttons to bottom
                ft.Row(
                    [
                        ft.Container(expand=True),  # Spacer
                        self.continue_button,
                    ]
                ),
            ],
            expand=True,
        )

        self.page.add(content)

    def _on_select_folder(self, e: ft.ControlEvent) -> None:
        """Handle folder selection button click."""

        def on_dialog_result(e: ft.FilePickerResultEvent) -> None:
            if e.path:
                path = Path(e.path)

                # Check if user selected a DPD subfolder instead of parent
                dpd_folders = ["dpd", "dpd-grammar", "dpd-deconstructor", "dpd-deconstructor2", "dpd-variants"]
                if path.name.lower() in [f.lower() for f in dpd_folders]:
                    # Use parent folder instead
                    path = path.parent

                self.selected_path = path
                self.path_text.value = str(path)
                self.path_text.italic = False
                self.path_text.color = ft.Colors.GREEN_400
                self._validate_path(path)
                self.page.update()

        # Create file picker dialog
        file_picker = ft.FilePicker(on_result=on_dialog_result)
        self.page.overlay.append(file_picker)
        self.page.update()
        file_picker.get_directory_path()

    def _validate_path(self, path: Path) -> None:
        """Validate the selected path and update UI accordingly.

        Args:
            path: The selected folder path
        """
        is_valid, message = self.config_manager.validate_goldendict_path(path)

        if is_valid:
            self.status_text.value = f"✓ {message}"
            self.status_text.color = ft.Colors.GREEN_400
            self.continue_button.disabled = False
        else:
            self.status_text.value = f"⚠ {message}"
            self.status_text.color = ft.Colors.ORANGE_400
            self.continue_button.disabled = False  # Allow user to proceed anyway

        self.page.update()

    def _on_continue(self, e: ft.ControlEvent) -> None:
        """Handle continue button click."""
        if not self.selected_path:
            return

        # Create initial config
        config = Config(
            goldendict_path=self.selected_path,
            installed_version="unknown",  # Will be detected on first update check
            auto_check_updates=True,
            backup_before_update=True,
        )

        # Save config
        self.config_manager.save_config(config)

        # Notify completion
        self.on_complete(config)
