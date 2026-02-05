"""Utilities for the DPD Updater.

This module provides helper functions for detecting and validating
DPD dictionary installations.
"""

from pathlib import Path
from typing import Optional


def detect_installed_version(goldendict_path: Path) -> Optional[str]:
    """Detect the installed DPD version by scanning the GoldenDict folder.
    
    Checks for the presence of DPD dictionary folders and files to determine
    if DPD is installed and potentially what version.
    
    Args:
        goldendict_path: Path to the GoldenDict content/dictionaries folder
        
    Returns:
        Version string if DPD is detected, None otherwise
    """
    if not goldendict_path.exists():
        return None
    
    # Look for DPD dictionary folders
    dpd_folders = [
        "dpd",
        "dpd-grammar", 
        "dpd-deconstructor",
        "dpd-deconstructor2",
        "dpd-variants"
    ]
    
    found_folders = []
    for folder_name in dpd_folders:
        folder_path = goldendict_path / folder_name
        if folder_path.exists() and folder_path.is_dir():
            # Check if it contains dictionary files
            if any(folder_path.glob("*.ifo")):
                found_folders.append(folder_name)
    
    if not found_folders:
        return None
    
    # Try to extract the build date from .ifo file
    # The date field (e.g., date=2026-02-04T11:04:24) represents when DPD was built
    dpd_folder = goldendict_path / "dpd"
    if dpd_folder.exists():
        ifo_files = list(dpd_folder.glob("*.ifo"))
        if ifo_files:
            try:
                with open(ifo_files[0], "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("date="):
                            date_str = line.strip().split("=", 1)[1]
                            # Return the date as-is (e.g., "2026-02-04T11:04:24")
                            return date_str
            except Exception:
                pass
    
    # If we found folders but couldn't parse date, return "installed"
    return "installed"


def verify_dpd_installation(goldendict_path: Path) -> tuple[bool, list[str]]:
    """Verify that DPD is properly installed in the GoldenDict folder.
    
    Args:
        goldendict_path: Path to the GoldenDict content/dictionaries folder
        
    Returns:
        Tuple of (is_valid, list of issues)
    """
    issues = []
    
    if not goldendict_path.exists():
        return False, ["GoldenDict folder does not exist"]
    
    if not goldendict_path.is_dir():
        return False, ["GoldenDict path is not a directory"]
    
    # Check for main DPD dictionary
    dpd_folder = goldendict_path / "dpd"
    if not dpd_folder.exists():
        issues.append("Main 'dpd' folder not found")
    else:
        # Check for required dictionary files
        required_files = ["dpd.ifo", "dpd.idx", "dpd.dict.dz"]
        for req_file in required_files:
            if not (dpd_folder / req_file).exists():
                issues.append(f"Missing {req_file} in dpd folder")
    
    # Check for other DPD components
    optional_folders = [
        ("dpd-grammar", "Grammar dictionary"),
        ("dpd-deconstructor", "Deconstructor dictionary"),
        ("dpd-variants", "Variants dictionary")
    ]
    
    for folder_name, description in optional_folders:
        folder_path = goldendict_path / folder_name
        if folder_path.exists():
            # Verify it has .ifo file
            if not any(folder_path.glob("*.ifo")):
                issues.append(f"{description} folder exists but missing .ifo file")
    
    is_valid = len(issues) == 0 or (dpd_folder.exists() and len(issues) < 3)
    return is_valid, issues


def scan_for_changes(goldendict_path: Path, last_known_version: str) -> tuple[bool, Optional[str]]:
    """Scan GoldenDict folder for changes since last known state.
    
    Args:
        goldendict_path: Path to the GoldenDict folder
        last_known_version: The version stored in config
        
    Returns:
        Tuple of (has_changed, current_version)
    """
    current_version = detect_installed_version(goldendict_path)
    
    if current_version is None:
        # DPD no longer installed
        return last_known_version != "unknown", None
    
    if last_known_version == "unknown":
        # DPD now installed but wasn't before
        return True, current_version
    
    # Check if version changed
    if current_version != last_known_version:
        return True, current_version
    
    # Even if version matches, verify files are present
    is_valid, issues = verify_dpd_installation(goldendict_path)
    if not is_valid and issues:
        return True, current_version  # Something changed (files missing)
    
    return False, current_version
