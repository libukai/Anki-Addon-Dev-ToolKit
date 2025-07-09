"""
Anki Add-on Runtime Module

Handles symbolic linking and running of add-ons for development and testing.
Provides cross-platform support for linking add-ons and launching Anki.
"""

import platform
import subprocess
from pathlib import Path
from typing import Any

from aadt.config import AddonConfig


class AddonLinker:
    """
    Manages symbolic links between development add-ons and Anki's addon directory.

    Provides cross-platform support for linking add-ons during development,
    allowing real-time testing without manual file copying.
    """

    def __init__(self, config: AddonConfig) -> None:
        self.config = config
        self.project_root = Path.cwd()
        self.src_dir = self.project_root / "src" / config.module_name

    def get_anki_addon_dir(self) -> Path:
        """Get the Anki addons21 directory path for the current platform."""
        system = platform.system()

        match system:
            case "Darwin":  # macOS
                return Path.home() / "Library" / "Application Support" / "Anki2" / "addons21"
            case "Windows":
                return Path.home() / "AppData" / "Roaming" / "Anki2" / "addons21"
            case "Linux":
                return Path.home() / ".local" / "share" / "Anki2" / "addons21"
            case _:
                raise OSError(f"Unsupported platform: {system}")

    def get_link_path(self) -> Path:
        """Get the target link path in Anki's addon directory."""
        return self.get_anki_addon_dir() / self.config.module_name

    def link_addon(self) -> bool:
        """Create a symbolic link from the add-on source to Anki's addon directory."""
        if not self.src_dir.exists():
            print(f"❌ Source directory not found: {self.src_dir}")
            print("   Make sure you're in the correct project directory")
            return False

        try:
            addon_dir = self.get_anki_addon_dir()
            addon_dir.mkdir(parents=True, exist_ok=True)

            link_path = self.get_link_path()

            # Remove existing link/directory if it exists
            if not self._remove_existing_link(link_path):
                return False

            # Create new symbolic link
            if platform.system() == "Windows":
                return self._create_windows_junction(link_path)
            else:
                return self._create_unix_symlink(link_path)

        except OSError as e:
            print(f"❌ Failed to set up add-on link: {e}")
            return False

    def unlink_addon(self) -> bool:
        """Remove the symbolic link for the add-on."""
        link_path = self.get_link_path()

        if not (link_path.exists() or link_path.is_symlink()):
            print(f"🔗 No link found at: {link_path}")
            return True

        return self._remove_existing_link(link_path, unlink_mode=True)

    def _remove_existing_link(self, link_path: Path, unlink_mode: bool = False) -> bool:
        """Remove existing link or warn about directory conflicts."""
        if not (link_path.exists() or link_path.is_symlink()):
            return True

        if link_path.is_symlink():
            action = "Unlinking" if unlink_mode else "Removing existing symlink"
            print(f"🔗 {action}: {link_path}")
            link_path.unlink()
            return True
        elif link_path.is_dir():
            if unlink_mode:
                print(f"📁 Warning: {link_path} is a directory, not a symlink")
                print("   Cannot unlink a regular directory")
            else:
                print(f"📁 Warning: Directory exists at {link_path}")
                print("   Please remove it manually or use a different module name")
            return False
        else:
            print(f"📄 Warning: File exists at {link_path}")
            return False

    def _create_windows_junction(self, link_path: Path) -> bool:
        """Create a Windows junction point (requires no special permissions)."""
        try:
            subprocess.run(  # noqa: S602
                ["mklink", "/J", str(link_path), str(self.src_dir.resolve())],  # noqa: S607
                check=True,
                shell=True,
                capture_output=True,
            )
            print(f"🔗 Created junction: {link_path} -> {self.src_dir}")
            print(f"📁 Anki will load the add-on from: {self.src_dir}")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to create junction. Try running as administrator.")
            return False

    def _create_unix_symlink(self, link_path: Path) -> bool:
        """Create a symbolic link on Unix-like systems (macOS, Linux)."""
        try:
            link_path.symlink_to(self.src_dir.resolve())
            print(f"🔗 Created symlink: {link_path} -> {self.src_dir}")
            print(f"📁 Anki will load the add-on from: {self.src_dir}")
            return True
        except OSError as e:
            print(f"❌ Failed to create symlink: {e}")
            return False

    def status(self) -> dict[str, Any]:
        """Get the current linking status."""
        link_path = self.get_link_path()

        status = {
            "src_exists": self.src_dir.exists(),
            "link_exists": link_path.exists() or link_path.is_symlink(),
            "is_symlink": link_path.is_symlink(),
            "src_path": str(self.src_dir),
            "link_path": str(link_path),
        }

        if status["is_symlink"]:
            try:
                target = link_path.resolve()
                status["link_target"] = str(target)
                status["link_valid"] = target == self.src_dir.resolve()
            except OSError:
                status["link_target"] = None
                status["link_valid"] = False

        return status
