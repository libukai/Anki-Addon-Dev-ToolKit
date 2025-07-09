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
# This program is subject to certain additional terms pursuant to
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
Main Add-on Builder
"""

import logging
import os
import shutil
import zipfile
from collections.abc import Callable
from pathlib import Path

from aadt import DIST_TYPES, PATH_DIST, PATH_PROJECT_ROOT
from aadt.config import Config
from aadt.git import VersionManager
from aadt.manifest import DistType, ManifestUtils
from aadt.ui import UIBuilder
from aadt.utils import copy_recursively, purge


class BuildError(Exception):
    """Custom exception for build-related errors"""

    pass


class VersionError(BuildError):
    """Exception raised when version cannot be determined"""

    pass


def clean_repo(trash_patterns: list[str] | None = None) -> None:
    """Clean repository with configurable trash patterns"""
    if trash_patterns is None:
        trash_patterns = ["*.pyc", "*.pyo", "__pycache__"]  # fallback default

    logging.info("Cleaning repository...")
    if PATH_DIST.exists():
        shutil.rmtree(PATH_DIST)
    purge(".", trash_patterns, recursive=True)


class AddonBuilder:
    def __init__(
        self,
        version: str | None = None,
        callback_archive: Callable[[], None] | None = None,
    ) -> None:
        # Load configuration for exclude patterns
        self._config = Config()
        self._addon_config = self._config.as_dataclass()
        exclude_patterns = self._addon_config.build_config.archive_exclude_patterns

        # Initialize version manager with fallback support
        self._version_manager = VersionManager(PATH_PROJECT_ROOT, exclude_patterns)

        # Parse version with fallback support
        self._version = self._version_manager.parse_version(version)

        # Handle 'dev' version refinement (handled by VersionManager)
        # No additional processing needed - VersionManager handles all fallbacks

        if not self._version:
            error_msg = "Version could not be determined"
            logging.error("Error: %s", error_msg)
            raise VersionError(error_msg)
        self._callback_archive = callback_archive
        self._path_dist_module = PATH_DIST / "src" / self._addon_config.module_name

        # Setup configurable paths
        self._build_config = self._addon_config.build_config
        self._path_optional_icons = PATH_PROJECT_ROOT / "ui" / "resources" / "icons" / "optional"
        self._path_changelog = PATH_DIST / "CHANGELOG.md"

        # License paths from config
        self._paths_licenses = [
            PATH_DIST if path == "." else PATH_DIST / path for path in self._build_config.license_paths
        ]

    def build(self, disttype: DistType = "local") -> Path:
        if disttype not in DIST_TYPES:
            raise BuildError(f"Invalid distribution type: {disttype}")

        logging.info(
            "\n--- Building %s %s for %s ---\n",
            self._addon_config.display_name,
            self._version,
            disttype,
        )

        self.create_dist()
        self.build_dist(disttype=disttype)

        package_path = self.package_dist(disttype=disttype)

        # Clean up temporary build directory after successful packaging
        self._cleanup_dist()

        return package_path

    def create_dist(self) -> None:
        logging.info(
            "Preparing source tree for %s %s ...",
            self._addon_config.display_name,
            self._version,
        )

        clean_repo(trash_patterns=self._build_config.trash_patterns)

        PATH_DIST.mkdir(parents=True)
        self._version_manager.archive(self._version, PATH_DIST)

    def build_dist(self, disttype: DistType = "local") -> None:
        self._copy_licenses()
        if self._path_changelog.exists():
            self._copy_changelog()
        if self._path_optional_icons.exists():
            self._copy_optional_icons()
        if self._callback_archive:
            self._callback_archive()

        self._write_manifest(disttype)

        ui_builder = UIBuilder(dist=PATH_DIST, config=self._config)
        should_create_qt_shim = ui_builder.build()

        if should_create_qt_shim:
            logging.info("Writing Qt compatibility shim...")
            ui_builder.create_qt_shim()
            logging.info("Done.")

    def package_dist(self, disttype: DistType = "local") -> Path:
        return self._package(disttype)

    def _package(self, disttype: DistType) -> Path:
        logging.info("Packaging add-on...")

        to_zip = self._path_dist_module
        ext = "ankiaddon"

        # Note: Only Qt6 is supported in this modernized version
        out_name = "{repo_name}-{version}{dist}.{ext}".format(
            repo_name=self._addon_config.repo_name,
            version=self._version,
            dist="" if disttype == "local" else "-" + disttype,
            ext=ext,
        )

        out_path = PATH_PROJECT_ROOT / self._build_config.output_dir / out_name

        # Ensure output directory exists
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if out_path.exists():
            out_path.unlink()

        with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as myzip:
            rootlen = len(str(to_zip)) + 1
            for root, _dirs, files in os.walk(to_zip):
                for file in files:
                    path = os.path.join(root, file)
                    myzip.write(path, path[rootlen:])

        logging.info(f"Package saved as {out_name}")
        logging.info("Done.")

        return out_path

    def _write_manifest(self, disttype: DistType) -> None:
        mod_time = self._version_manager.modtime(self._version)
        ManifestUtils.generate_and_write_manifest(
            addon_properties=self._config,
            version=self._version,
            dist_type=disttype,
            target_dir=self._path_dist_module,
            mod_time=mod_time,
        )

    def _copy_licenses(self) -> None:
        logging.info("Copying licenses...")
        for path in self._paths_licenses:
            if not path.is_dir():
                continue
            for file in path.glob("LICENSE*"):
                target = self._path_dist_module / f"{file.stem}.txt"
                shutil.copyfile(file, target)

    def _copy_changelog(self) -> None:
        logging.info("Copying changelog...")
        target = self._path_dist_module / "CHANGELOG.md"
        shutil.copy(self._path_changelog, target)

    def _copy_optional_icons(self) -> None:
        logging.info("Copying additional icons...")
        copy_recursively(self._path_optional_icons, PATH_DIST / "resources" / "icons" / "")

    def _cleanup_dist(self) -> None:
        """Clean up temporary build directory after successful packaging"""
        if PATH_DIST.exists():
            logging.info("Cleaning up temporary build files...")
            shutil.rmtree(PATH_DIST)
            logging.info("Cleanup completed.")
