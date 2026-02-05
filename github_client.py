"""GitHub API client for the DPD Updater.

This module provides a wrapper around the GitHub REST API for fetching
release information and comparing versions.
"""

from dataclasses import dataclass
from typing import Optional

import requests
from packaging.version import Version, InvalidVersion

from dpd_updater import GITHUB_API_URL


@dataclass
class ReleaseInfo:
    """Information about a GitHub release.

    Attributes:
        version: The release version tag (e.g., "v2.5.1")
        name: The release name/title
        body: The release notes/description
        published_at: ISO 8601 timestamp of release publication
        asset_url: URL to the GoldenDict asset for this release
        html_url: URL to the release page on GitHub
    """

    version: str
    name: str
    body: str
    published_at: str
    asset_url: Optional[str]
    html_url: str


class GitHubClient:
    """Client for interacting with the GitHub API.

    Provides methods to fetch release information and compare versions.
    Uses unauthenticated requests (60 requests/hour limit).
    """

    def __init__(self, api_url: str = GITHUB_API_URL) -> None:
        """Initialize the GitHub client.

        Args:
            api_url: The GitHub API URL to use (default: DPD repo)
        """
        self.api_url = api_url
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "DPD-Updater/1.0",
            }
        )

    def get_latest_release(self) -> ReleaseInfo:
        """Fetch the latest release from GitHub.

        Returns:
            ReleaseInfo object with release details

        Raises:
            requests.RequestException: If the API request fails
        """
        response = self.session.get(self.api_url, timeout=30)
        response.raise_for_status()

        data = response.json()

        # Extract GoldenDict asset URL
        asset_url = None
        assets = data.get("assets", [])
        for asset in assets:
            name = asset.get("name", "")
            # Match pattern: dpd-goldendict*.zip (with or without version)
            if name.startswith("dpd-goldendict") and name.endswith(".zip"):
                asset_url = asset.get("browser_download_url")
                break

        return ReleaseInfo(
            version=data.get("tag_name", "unknown"),
            name=data.get("name", ""),
            body=data.get("body", ""),
            published_at=data.get("published_at", ""),
            asset_url=asset_url,
            html_url=data.get("html_url", ""),
        )

    def compare_versions(self, current: str, latest: str) -> int:
        """Compare two version strings.

        Args:
            current: The current installed version (e.g., "v2.5.0" or "2.5.0")
            latest: The latest available version (e.g., "v2.5.1" or "2.5.1")

        Returns:
            -1 if current < latest (update available)
             0 if current == latest (up to date)
             1 if current > latest (current is newer - unusual)

        Raises:
            InvalidVersion: If either version string cannot be parsed
        """
        # Remove 'v' prefix if present
        current_clean = current.lstrip("v") if current != "unknown" else "0.0.0"
        latest_clean = latest.lstrip("v")

        try:
            current_ver = Version(current_clean)
            latest_ver = Version(latest_clean)

            if current_ver < latest_ver:
                return -1
            elif current_ver > latest_ver:
                return 1
            else:
                return 0
        except InvalidVersion:
            # Fallback to string comparison for non-standard versions
            if current_clean < latest_clean:
                return -1
            elif current_clean > latest_clean:
                return 1
            else:
                return 0

    def is_update_available(self, current_version: str, latest_version: str) -> bool:
        """Check if an update is available.

        Args:
            current_version: The currently installed version
            latest_version: The latest available version from GitHub

        Returns:
            True if latest > current, False otherwise
        """
        return self.compare_versions(current_version, latest_version) < 0

    def format_release_notes(self, body: str, max_length: int = 500) -> str:
        """Format release notes for display, truncating if necessary.

        Args:
            body: The raw release notes from GitHub
            max_length: Maximum length before truncation

        Returns:
            Formatted release notes string
        """
        # Remove markdown headers and code blocks for cleaner display
        lines = body.split("\n")
        cleaned_lines = []

        for line in lines:
            # Skip empty lines at the start
            if not cleaned_lines and not line.strip():
                continue
            # Remove markdown headers
            if line.startswith("#"):
                line = line.lstrip("#").strip()
            cleaned_lines.append(line)

        cleaned = "\n".join(cleaned_lines).strip()

        if len(cleaned) > max_length:
            return cleaned[:max_length].rsplit(" ", 1)[0] + "..."

        return cleaned


class GitHubAPIError(Exception):
    """Exception raised for GitHub API errors."""

    pass
