"""Tests for the DPD Updater GitHub client module.

Tests cover GitHub API integration, version comparison, and release info parsing.
"""

from unittest.mock import Mock, patch

import pytest
import requests
from packaging.version import InvalidVersion

from exporter.updater.github_client import GitHubClient, ReleaseInfo


class TestReleaseInfo:
    """Tests for the ReleaseInfo dataclass."""
    
    def test_release_info_creation(self) -> None:
        """Test creating a ReleaseInfo object."""
        release = ReleaseInfo(
            version="v2.5.1",
            name="Version 2.5.1",
            body="Release notes here",
            published_at="2024-01-15T10:00:00Z",
            asset_url="https://example.com/asset.zip",
            html_url="https://github.com/release"
        )
        
        assert release.version == "v2.5.1"
        assert release.name == "Version 2.5.1"
        assert release.body == "Release notes here"
        assert release.published_at == "2024-01-15T10:00:00Z"
        assert release.asset_url == "https://example.com/asset.zip"
        assert release.html_url == "https://github.com/release"


class TestGitHubClient:
    """Tests for the GitHubClient class."""
    
    def test_init_default_url(self) -> None:
        """Test client initialization with default URL."""
        client = GitHubClient()
        assert "api.github.com" in client.api_url
        assert "digitalpalidictionary" in client.api_url
    
    def test_init_custom_url(self) -> None:
        """Test client initialization with custom URL."""
        custom_url = "https://api.github.com/repos/test/repo/releases/latest"
        client = GitHubClient(api_url=custom_url)
        assert client.api_url == custom_url
    
    @patch("requests.Session")
    def test_get_latest_release_success(self, mock_session_class: Mock) -> None:
        """Test fetching latest release successfully."""
        # Mock the session and response
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "tag_name": "v2.5.1",
            "name": "Version 2.5.1",
            "body": "Release notes",
            "published_at": "2024-01-15T10:00:00Z",
            "html_url": "https://github.com/release",
            "assets": [
                {
                    "name": "dpd-goldendict-v2.5.1.zip",
                    "browser_download_url": "https://github.com/asset.zip"
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response
        
        client = GitHubClient()
        client.session = mock_session
        
        release = client.get_latest_release()
        
        assert release.version == "v2.5.1"
        assert release.name == "Version 2.5.1"
        assert release.asset_url == "https://github.com/asset.zip"
        mock_session.get.assert_called_once()
    
    @patch("requests.Session")
    def test_get_latest_release_no_asset(self, mock_session_class: Mock) -> None:
        """Test fetching release with no matching asset."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "tag_name": "v2.5.1",
            "name": "Version 2.5.1",
            "body": "Release notes",
            "published_at": "2024-01-15T10:00:00Z",
            "html_url": "https://github.com/release",
            "assets": [
                {
                    "name": "other-file.zip",  # Doesn't match pattern
                    "browser_download_url": "https://github.com/other.zip"
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response
        
        client = GitHubClient()
        client.session = mock_session
        
        release = client.get_latest_release()
        
        assert release.asset_url is None
    
    @patch("requests.Session")
    def test_get_latest_release_api_error(self, mock_session_class: Mock) -> None:
        """Test handling API error when fetching release."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        mock_session.get.side_effect = requests.RequestException("API Error")
        
        client = GitHubClient()
        client.session = mock_session
        
        with pytest.raises(requests.RequestException):
            client.get_latest_release()
    
    def test_compare_versions_update_available(self) -> None:
        """Test version comparison when update is available."""
        client = GitHubClient()
        
        result = client.compare_versions("v2.5.0", "v2.5.1")
        assert result == -1
        
        result = client.compare_versions("2.5.0", "2.6.0")
        assert result == -1
        
        result = client.compare_versions("v2.5.0", "v3.0.0")
        assert result == -1
    
    def test_compare_versions_up_to_date(self) -> None:
        """Test version comparison when versions are equal."""
        client = GitHubClient()
        
        result = client.compare_versions("v2.5.0", "v2.5.0")
        assert result == 0
        
        result = client.compare_versions("2.5.0", "v2.5.0")
        assert result == 0
    
    def test_compare_versions_current_newer(self) -> None:
        """Test version comparison when current is newer (unusual case)."""
        client = GitHubClient()
        
        result = client.compare_versions("v2.5.1", "v2.5.0")
        assert result == 1
    
    def test_compare_versions_unknown_current(self) -> None:
        """Test version comparison with unknown current version."""
        client = GitHubClient()
        
        result = client.compare_versions("unknown", "v2.5.0")
        assert result == -1  # Should treat unknown as needing update
    
    def test_compare_versions_with_prefix_variations(self) -> None:
        """Test version comparison with different prefix formats."""
        client = GitHubClient()
        
        # Mix of v-prefix and no prefix
        result = client.compare_versions("v2.5.0", "2.5.1")
        assert result == -1
        
        result = client.compare_versions("2.5.0", "v2.5.1")
        assert result == -1
    
    def test_compare_versions_prerelease(self) -> None:
        """Test version comparison with prerelease versions."""
        client = GitHubClient()
        
        result = client.compare_versions("v2.5.0", "v2.5.1-beta")
        assert result == -1
        
        result = client.compare_versions("v2.5.1-beta", "v2.5.1")
        assert result == -1
    
    def test_is_update_available_true(self) -> None:
        """Test update available detection returns True."""
        client = GitHubClient()
        
        assert client.is_update_available("v2.5.0", "v2.5.1") is True
        assert client.is_update_available("unknown", "v2.5.0") is True
    
    def test_is_update_available_false(self) -> None:
        """Test update available detection returns False."""
        client = GitHubClient()
        
        assert client.is_update_available("v2.5.0", "v2.5.0") is False
        assert client.is_update_available("v2.5.1", "v2.5.0") is False
    
    def test_format_release_notes_simple(self) -> None:
        """Test formatting simple release notes."""
        client = GitHubClient()
        
        body = "This is a release with bug fixes and improvements."
        result = client.format_release_notes(body)
        
        assert result == body
    
    def test_format_release_notes_with_headers(self) -> None:
        """Test formatting release notes with markdown headers."""
        client = GitHubClient()
        
        body = "# Version 2.5.1\n\n## Bug Fixes\n- Fixed issue 1\n- Fixed issue 2"
        result = client.format_release_notes(body)
        
        assert "#" not in result
        assert "Version 2.5.1" in result
        assert "Bug Fixes" in result
    
    def test_format_release_notes_truncation(self) -> None:
        """Test that long release notes are truncated."""
        client = GitHubClient()
        
        body = "A" * 1000
        result = client.format_release_notes(body, max_length=100)
        
        assert len(result) < 110  # Should be truncated
        assert result.endswith("...")
    
    def test_format_release_notes_empty_lines(self) -> None:
        """Test formatting release notes with leading empty lines."""
        client = GitHubClient()
        
        body = "\n\n\nActual content here"
        result = client.format_release_notes(body)
        
        assert not result.startswith("\n")
        assert result == "Actual content here"
