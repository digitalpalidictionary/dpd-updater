"""Tests for the DPD Updater main entry point.

Tests cover the DPDUpdaterApp class and main execution flow.
"""

from unittest.mock import Mock, patch

import pytest

import flet as ft

from main import DPDUpdaterApp


class TestDPDUpdaterApp:
    """Tests for DPDUpdaterApp class."""

    @patch("main.ConfigManager")
    @patch("main.SetupWizard")
    @patch("main.MainWindow")
    def test_init(self, mock_main_window: Mock, mock_setup_wizard: Mock, mock_config_manager: Mock) -> None:
        """Test application initialization."""
        app = DPDUpdaterApp()

        assert app.page is None
        assert app.config_manager is None
        assert app.config is None

    @patch("main.ConfigManager")
    @patch("main.SetupWizard")
    @patch("main.MainWindow")
    @patch("main.scan_for_changes")
    def test_main_first_run(
        self,
        mock_scan: Mock,
        mock_config_manager: Mock,
        mock_setup_wizard: Mock,
        mock_main_window: Mock,
    ) -> None:
        """Test first run shows setup wizard."""
        mock_config = Mock()
        mock_config.goldendict_path = None
        mock_config_manager.return_value = mock_config

        app = DPDUpdaterApp()

        mock_page = Mock(spec=ft.Page)
        app.main(mock_page)

        mock_setup_wizard.assert_called_once()

    @patch("main.ConfigManager")
    @patch("main.SetupWizard")
    @patch("main.MainWindow")
    @patch("main.scan_for_changes")
    def test_main_existing_config(
        self,
        mock_scan: Mock,
        mock_config_manager: Mock,
        mock_setup_wizard: Mock,
        mock_main_window: Mock,
    ) -> None:
        """Test existing config shows main window."""
        mock_config = Mock()
        mock_config.goldendict_path = "/some/path"
        mock_config_manager.return_value = mock_config

        mock_scan.return_value = (False, "installed_version")

        app = DPDUpdaterApp()

        mock_page = Mock(spec=ft.Page)
        app.main(mock_page)

        mock_main_window.assert_called_once()
        mock_setup_wizard.assert_not_called()

    @patch("main.ConfigManager")
    @patch("main.SetupWizard")
    @patch("main.MainWindow")
    @patch("main.scan_for_changes")
    def test_main_with_changes(
        self,
        mock_scan: Mock,
        mock_config_manager: Mock,
        mock_setup_wizard: Mock,
        mock_main_window: Mock,
    ) -> None:
        """Test with changes updates config."""
        mock_config = Mock()
        mock_config.goldendict_path = "/some/path"
        mock_config.installed_version = "old_version"
        mock_config_manager.return_value = mock_config

        mock_scan.return_value = (True, "new_version")

        app = DPDUpdaterApp()

        mock_page = Mock(spec=ft.Page)
        app.main(mock_page)

        assert mock_config.installed_version == "new_version"
        mock_config_manager.return_value.save_config.assert_called_once()

    @patch("main.ConfigManager")
    @patch("main.SetupWizard")
    @patch("main.MainWindow")
    @patch("main.scan_for_changes")
    def test_keyboard_shortcut(
        self,
        mock_scan: Mock,
        mock_config_manager: Mock,
        mock_setup_wizard: Mock,
        mock_main_window: Mock,
    ) -> None:
        """Test Ctrl+Q closes window."""
        app = DPDUpdaterApp()

        mock_page = Mock(spec=ft.Page)
        app.main(mock_page)

        mock_event = Mock()
        mock_event.key = "Q"
        mock_event.ctrl = True

        app._on_keyboard(mock_event)

        mock_page.window.close.assert_called_once()


class TestMain:
    """Tests for the main function."""

    @patch("main.flet.app")
    def test_main_creates_and_runs_app(self, mock_flet_app: Mock) -> None:
        """Test main function creates and runs app."""
        main()

        mock_flet_app.assert_called_once()
