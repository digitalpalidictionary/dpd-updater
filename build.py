"""Build script for DPD Updater executables.

This script uses PyInstaller to create standalone executables for:
- Windows (.exe)
- macOS (.app bundle)
- Linux (executable)

Usage:
    python build.py              # Build for current platform
    python build.py --all        # Build for all platforms (requires cross-compilation setup)
"""

import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path


# Build configuration
UPDATER_DIR = Path(__file__).parent
BUILD_DIR = UPDATER_DIR / "build"
DIST_DIR = UPDATER_DIR / "dist"
ICON_DIR = UPDATER_DIR / "icons"

# Entry point
ENTRY_POINT = UPDATER_DIR / "main.py"

# Hidden imports (dependencies that PyInstaller might miss)
HIDDEN_IMPORTS = [
    "config",
    "github_client",
    "installer",
    "system_manager",
    "ui_setup",
    "ui_main",
    "utils",
]

# Data files to include
DATA_FILES = [
    # (source, destination in bundle)
]


def get_icon_path() -> Path | None:
    """Get the appropriate icon file for the current platform."""
    system = platform.system()
    
    if system == "Windows":
        # Windows needs .ico file
        ico_path = ICON_DIR / "dpd-logo.ico"
        if ico_path.exists():
            return ico_path
        # Try to convert from PNG if ICO doesn't exist
        png_path = ICON_DIR / "dpd-logo-512.png"
        if png_path.exists():
            return png_path
    elif system == "Darwin":  # macOS
        # macOS can use .icns or .png
        icns_path = ICON_DIR / "dpd-logo.icns"
        if icns_path.exists():
            return icns_path
        png_path = ICON_DIR / "dpd-logo-512.png"
        if png_path.exists():
            return png_path
    else:  # Linux
        # Linux can use .png
        png_path = ICON_DIR / "dpd-logo-512.png"
        if png_path.exists():
            return png_path
    
    # Fallback to SVG (PyInstaller will warn but may work)
    svg_path = ICON_DIR / "dpd-icon.svg"
    if svg_path.exists():
        return svg_path
    
    return None


def clean_build() -> None:
    """Clean previous build artifacts."""
    print("Cleaning previous builds...")
    for dir_path in [BUILD_DIR, DIST_DIR]:
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  Removed {dir_path}")


def build_windows() -> None:
    """Build Windows executable."""
    print("Building Windows executable...")
    
    icon_path = get_icon_path()
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=DPD-Updater",
        "--onefile",
        "--windowed",
        "--clean",
        "--noconfirm",
        f"--distpath={DIST_DIR}",
        f"--workpath={BUILD_DIR}",
        f"--specpath={BUILD_DIR}",
        "--collect-all=flet",
        "--collect-all=flet_desktop",
        "--collect-all=flet_core",
    ]
    
    if icon_path:
        cmd.append(f"--icon={icon_path}")
    
    for hidden in HIDDEN_IMPORTS:
        cmd.extend(["--hidden-import", hidden])
    
    cmd.append(str(ENTRY_POINT))
    
    subprocess.run(cmd, check=True)
    print(f"[OK] Windows build complete: {DIST_DIR / 'DPD-Updater.exe'}")


def build_macos() -> None:
    """Build macOS app bundle."""
    print("Building macOS app bundle...")
    
    icon_path = get_icon_path()
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=DPD Updater",
        "--onefile",
        "--windowed",
        "--clean",
        "--noconfirm",
        f"--distpath={DIST_DIR}",
        f"--workpath={BUILD_DIR}",
        f"--specpath={BUILD_DIR}",
        "--collect-all=flet",
        "--collect-all=flet_desktop",
        "--collect-all=flet_core",
    ]
    
    if icon_path:
        cmd.append(f"--icon={icon_path}")
    
    for hidden in HIDDEN_IMPORTS:
        cmd.extend(["--hidden-import", hidden])
    
    cmd.append(str(ENTRY_POINT))
    
    subprocess.run(cmd, check=True)
    print(f"[OK] macOS build complete: {DIST_DIR / 'DPD Updater'}")


def build_linux() -> None:
    """Build Linux executable."""
    print("Building Linux executable...")
    
    icon_path = get_icon_path()
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=dpd-updater",
        "--onefile",
        "--windowed",
        "--clean",
        "--noconfirm",
        f"--distpath={DIST_DIR}",
        f"--workpath={BUILD_DIR}",
        f"--specpath={BUILD_DIR}",
        "--collect-all=flet",
        "--collect-all=flet_desktop",
        "--collect-all=flet_core",
    ]
    
    if icon_path:
        cmd.append(f"--icon={icon_path}")
    
    for hidden in HIDDEN_IMPORTS:
        cmd.extend(["--hidden-import", hidden])
    
    cmd.append(str(ENTRY_POINT))
    
    subprocess.run(cmd, check=True)
    
    # Make executable
    output_path = DIST_DIR / "dpd-updater"
    output_path.chmod(0o755)
    
    print(f"[OK] Linux build complete: {output_path}")


def build_current_platform() -> None:
    """Build for the current platform."""
    system = platform.system()
    
    if system == "Windows":
        build_windows()
    elif system == "Darwin":
        build_macos()
    else:
        build_linux()


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Build DPD Updater executables"
    )
    parser.add_argument(
        "--clean", 
        action="store_true", 
        help="Clean build directories before building"
    )
    parser.add_argument(
        "--platform",
        choices=["windows", "macos", "linux", "all"],
        default="current",
        help="Target platform (default: current)"
    )
    
    args = parser.parse_args()
    
    if args.clean:
        clean_build()
    
    # Ensure directories exist
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    
    if args.platform == "all":
        print("Building for all platforms...")
        print("Note: Cross-compilation requires additional setup")
        build_windows()
        build_macos()
        build_linux()
    elif args.platform == "windows":
        build_windows()
    elif args.platform == "macos":
        build_macos()
    elif args.platform == "linux":
        build_linux()
    else:
        build_current_platform()
    
    print(f"\n[OK] Build complete! Output in: {DIST_DIR}")


if __name__ == "__main__":
    main()
