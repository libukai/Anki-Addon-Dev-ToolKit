# Anki Add-on Builder
#
# Copyright (C)  2016-2021 Aristotelis P. <https://glutanimate.com/>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version, with the additions
# listed at the end of the license file that accompanied this program.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# NOTE: This program is subject to certain additional terms pursuant to
# Section 7 of the GNU Affero General Public License.  You should have
# received a copy of these additional terms immediately following the
# terms and conditions of the GNU Affero General Public License that
# accompanied this program.
#
# If not, please request a copy through one of the means of contact
# listed here: <https://glutanimate.com/contact/>.
#
# Any modifications to this file must keep this entire header intact.

"""
Basic Git interface with fallback support
"""

import logging
import shutil
import zipfile
from datetime import UTC
from pathlib import Path

from aadt.utils import call_shell


class GitError(Exception):
    """Exception raised for Git-related errors"""

    pass


class GitAvailabilityError(Exception):
    """Exception raised when Git is not available or not in a Git repository"""

    pass


class Git:
    @staticmethod
    def is_git_available() -> bool:
        """Check if Git is available and we're in a Git repository"""
        try:
            call_shell(["git", "rev-parse", "--git-dir"])
            return True
        except Exception:
            return False

    @staticmethod
    def check_git_availability() -> None:
        """Raise GitAvailabilityError if Git is not available"""
        if not Git.is_git_available():
            raise GitAvailabilityError("Git is not available or current directory is not a Git repository")

    def get_latest_tag(self) -> str:
        """Get the latest Git tag"""
        try:
            version = call_shell(["git", "describe", "--tags", "--abbrev=0"], error_exit=False)
            return version.strip() if version else ""
        except Exception as e:
            raise GitError(f"Failed to get latest tag: {e}") from e

    def get_current_commit(self) -> str:
        """Get the current commit hash"""
        try:
            commit = call_shell(["git", "rev-parse", "--short", "HEAD"], error_exit=False)
            return commit.strip() if commit else ""
        except Exception as e:
            raise GitError(f"Failed to get current commit: {e}") from e

    def parse_version(self, vstring: str | None = None) -> str:
        """Parse version string with Git-specific logic"""
        match vstring:
            case None | "release":
                tag = self.get_latest_tag()
                if not tag:
                    raise GitError("No Git tags found. Cannot determine release version.")
                return tag
            case "current":
                return self.get_current_commit()
            case "dev":
                # Check if there are uncommitted changes
                try:
                    git_status = call_shell(["git", "status", "--porcelain"], error_exit=False)
                    if git_status.strip() == "":
                        return self.get_current_commit()
                    return "dev"
                except Exception as e:
                    raise GitError(f"Failed to check Git status: {e}") from e
            case _:
                return vstring

    def archive(self, version: str, outpath: Path) -> bool:
        """Archive Git version to specified path"""
        logging.info(f"Archiving {version} using Git...")

        # Ensure output directory exists
        outpath.mkdir(parents=True, exist_ok=True)

        zip_path = outpath / "addon.zip"
        cmd = ["git", "archive", "--prefix=", version, "--output", str(zip_path)]

        try:
            # Execute git archive command
            call_shell(cmd, error_exit=False)

            # Check if archive was created successfully
            if not zip_path.exists() or zip_path.stat().st_size == 0:
                raise GitError(f"Git archive failed to create {zip_path}")

            # Extract the archive
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(outpath)

            # Clean up the zip file
            zip_path.unlink()

            logging.info("Git archive completed successfully")
            return True

        except Exception as e:
            # Clean up partial files
            if zip_path.exists():
                zip_path.unlink()
            raise GitError(f"Failed to archive version {version}: {e}") from e

    def modtime(self, version: str) -> str:
        """Get modification time of Git version"""
        logging.info("Getting Git modification time...")
        try:
            cmd = ["git", "log", "-1", "--format=%cd", "--date=iso", version]
            modtime = call_shell(cmd, error_exit=False)
            if not modtime:
                raise GitError(f"Failed to get modification time for {version}")
            # Convert to ISO format for Anki compatibility
            # Git ISO format: "2025-07-02 18:02:16 +0800"
            # Target format:   "2025-07-02T18:02:16+0800"
            parts = modtime.strip().split(maxsplit=2)
            match parts:
                case [date_part, time_part, tz_part]:
                    return f"{date_part}T{time_part}{tz_part}"
                case _:
                    # Fallback to simple replacement if format unexpected
                    return modtime.replace(" ", "T")
        except Exception as e:
            raise GitError(f"Failed to get modification time for {version}: {e}") from e


class FileSystemArchiver:
    """Fallback archiver that works without Git"""

    def __init__(self, project_root: Path, exclude_patterns: list[str]):
        self.project_root = project_root
        self.exclude_patterns = set(exclude_patterns)

    def parse_version(self, vstring: str | None = None) -> str:
        """Parse version without Git - use fallback strategies"""
        match vstring:
            case None | "release":
                # Try to read version from common files
                version = self._read_version_from_files()
                if version:
                    return version
                raise GitAvailabilityError(
                    "No version information found. Please create a VERSION file, "
                    "set version in pyproject.toml, or use an explicit version."
                )
            case "current" | "dev":
                # For non-Git environments, current and dev are the same
                from datetime import datetime

                return f"dev-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            case _:
                return vstring

    def _read_version_from_files(self) -> str | None:
        """Try to read version from common version files"""
        import re  # Import once at the top of the method

        version_files = [
            self.project_root / "__version__.py",
            self.project_root / "VERSION",
            self.project_root / "version.txt",
            self.project_root / "pyproject.toml",
        ]

        for version_file in version_files:
            if version_file.exists():
                try:
                    content = version_file.read_text(encoding="utf-8")

                    if version_file.name == "pyproject.toml":
                        # Extract version from pyproject.toml
                        match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
                        if match:
                            return match.group(1)
                    elif version_file.name == "__version__.py":
                        # Extract version from __version__.py
                        match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
                        if match:
                            return match.group(1)
                    else:
                        # Plain version file
                        return content.strip().split("\n")[0].strip()
                except Exception as e:
                    logging.debug(f"Failed to read version from {version_file}: {e}")
                    continue

        return None

    def archive(self, version: str, outpath: Path) -> bool:
        """Archive current directory to outpath/src/ without using Git"""
        logging.info(f"Archiving current directory (version: {version}) to {outpath}...")

        src_path = outpath / "src"
        if src_path.exists():
            shutil.rmtree(src_path)
        src_path.mkdir(parents=True, exist_ok=True)

        self._copy_directory_selective(self.project_root, src_path, self.exclude_patterns)

        logging.info("Fallback archive completed successfully")
        return True

    def _copy_directory_selective(self, src_dir: Path, dst_dir: Path, exclude_patterns: set[str]) -> None:
        """
        Recursively copies a directory, excluding files and directories
        that match the given glob patterns.
        """
        import fnmatch

        for item in src_dir.iterdir():
            # Check against exclude patterns for both files and directories
            if any(fnmatch.fnmatch(item.name, pattern) for pattern in exclude_patterns):
                continue

            if item.is_dir():
                # Check if the directory itself should be excluded
                is_excluded = False
                for pattern in exclude_patterns:
                    if fnmatch.fnmatch(item.name, pattern) or any(
                        p.startswith(item.name + "/") for p in exclude_patterns
                    ):
                        is_excluded = True
                        break
                if is_excluded:
                    continue

                new_dst_dir = dst_dir / item.name
                new_dst_dir.mkdir(exist_ok=True)
                self._copy_directory_selective(item, new_dst_dir, exclude_patterns)
            else:
                # Copy file if it doesn't match exclude patterns
                shutil.copy2(item, dst_dir / item.name)

    def modtime(self, version: str) -> str:
        """Get modification time without Git"""
        from datetime import datetime

        return datetime.now(UTC).isoformat()


class VersionManager:
    """
    Manages versioning by dynamically selecting a strategy
    based on Git availability.
    """

    def __init__(self, project_root: Path, exclude_patterns: list[str] | None = None):
        if Git.is_git_available():
            self.strategy: Git | FileSystemArchiver = Git()
        else:
            logging.warning("Git not found or not in a Git repository. Using fallback for versioning.")
            # Ensure exclude_patterns is not None for FileSystemArchiver
            if exclude_patterns is None:
                exclude_patterns = []  # Should be provided by config
            self.strategy = FileSystemArchiver(project_root, exclude_patterns)

    def parse_version(self, vstring: str | None = None) -> str:
        """
        Parse the version string using the selected strategy (Git or fallback).
        """
        try:
            return self.strategy.parse_version(vstring)
        except (GitError, GitAvailabilityError) as e:
            if isinstance(self.strategy, Git):
                logging.warning(f"Git version parsing failed: {e}, falling back to filesystem")
                fallback = FileSystemArchiver(self.project_root, self.exclude_patterns)
                try:
                    return fallback.parse_version(vstring)
                except Exception as fallback_e:
                    logging.error(f"Fallback version parsing also failed: {fallback_e}")
                    # Ultimate fallback
                    from datetime import datetime

                    return f"fallback-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            else:
                raise
        except Exception as e:
            logging.warning(f"Unexpected version parsing error: {e}, using fallback")
            # Ultimate fallback for any other errors
            from datetime import datetime

            return f"fallback-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    def archive(self, version: str, outpath: Path) -> bool:
        """Archive with automatic fallback"""
        try:
            return self.strategy.archive(version, outpath)
        except (GitError, GitAvailabilityError) as e:
            if isinstance(self.strategy, Git):
                logging.warning(f"Git archive failed: {e}, falling back to filesystem copy")
                fallback = FileSystemArchiver(self.project_root, self.exclude_patterns)
                return fallback.archive(version, outpath)
            else:
                raise
        except Exception as e:
            # For any other errors, try filesystem fallback if we're in Git mode
            if isinstance(self.strategy, Git):
                logging.warning(f"Git archive failed with unexpected error: {e}, falling back to filesystem copy")
                fallback = FileSystemArchiver(self.project_root, self.exclude_patterns)
                return fallback.archive(version, outpath)
            else:
                raise

    def modtime(self, version: str) -> str:
        """Get modification time with fallback"""
        try:
            return self.strategy.modtime(version)
        except Exception as e:
            logging.debug(f"Failed to get modification time: {e}, using current time")
            from datetime import datetime

            return datetime.now().isoformat()
