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
Project config parser
"""

import json
from collections import UserDict
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any

import jsonschema
from jsonschema.exceptions import ValidationError

from aadt import PATH_PACKAGE, PATH_PROJECT_ROOT

PATH_CONFIG = PATH_PROJECT_ROOT / "addon.json"


@dataclass
class UIConfig:
    """Configuration for UI-related paths and settings"""

    ui_dir: str = "ui"
    designer_dir: str = "designer"
    resources_dir: str = "resources"
    forms_package: str = "forms"
    exclude_optional_resources: bool = False
    create_resources_package: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "UIConfig":
        if not data:
            return cls()
        valid_fields = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


@dataclass
class BuildConfig:
    """Configuration for build process and output settings"""

    output_dir: str = "dist"
    trash_patterns: list[str] = field(default_factory=lambda: ["*.pyc", "*.pyo", "__pycache__"])
    license_paths: list[str] = field(default_factory=lambda: [".", "resources"])
    archive_exclude_patterns: list[str] = field(
        default_factory=lambda: [
            ".git",
            ".gitignore",
            "__pycache__",
            "*.pyc",
            "*.pyo",
            ".venv",
            "venv",
            ".env",
            "node_modules",
            ".DS_Store",
            "build",
            "dist",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "*.ankiaddon",
            "*.zip",
            ".aab",
            "Thumbs.db",
            "*.swp",
            "*.swo",
        ]
    )
    ui_config: UIConfig = field(default_factory=UIConfig)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "BuildConfig":
        if not data:
            return cls()

        # Get field names from dataclass fields, not hasattr
        field_names = {f.name for f in fields(cls)}
        init_data = {k: v for k, v in data.items() if k in field_names}

        if "ui_config" in init_data and isinstance(init_data["ui_config"], dict):
            init_data["ui_config"] = UIConfig.from_dict(init_data["ui_config"])

        return cls(**init_data)


@dataclass
class AddonConfig:
    """Modern dataclass-based configuration for add-on properties"""

    display_name: str
    module_name: str
    repo_name: str
    author: str
    conflicts: list[str]
    ankiweb_id: str | None = None
    targets: list[str] = field(default_factory=lambda: ["qt6"])
    contact: str | None = None
    homepage: str | None = None
    tags: str | None = None
    copyright_start: int | None = None
    min_anki_version: str | None = None
    max_anki_version: str | None = None
    tested_anki_version: str | None = None
    ankiweb_conflicts_with_local: bool = True
    local_conflicts_with_ankiweb: bool = True
    build_config: BuildConfig = field(default_factory=BuildConfig)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AddonConfig":
        """
        Create AddonConfig from dictionary, handling nested dataclasses.
        """
        # Get field names from dataclass fields, not hasattr
        field_names = {f.name for f in fields(cls)}
        init_data = {k: v for k, v in data.items() if k in field_names}

        if "build_config" in init_data and isinstance(init_data["build_config"], dict):
            init_data["build_config"] = BuildConfig.from_dict(init_data["build_config"])

        return cls(**init_data)

    def to_dict(self) -> dict[str, Any]:
        """Convert AddonConfig to dictionary, excluding None values"""
        return {k: v for k, v in asdict(self).items() if v is not None}


class ConfigError(Exception):
    """Custom exception for configuration errors"""

    pass


class Config(UserDict[str, Any]):
    """
    Simple dictionary-like interface to the repository config file
    """

    with (PATH_PACKAGE / "schema.json").open("r", encoding="utf-8") as f:
        _schema: dict[str, Any] = json.loads(f.read())

    def __init__(self, path: str | Path | None = None) -> None:
        self._path: Path = Path(path) if path else PATH_CONFIG
        try:
            with self._path.open(encoding="utf-8") as f:
                data: dict[str, Any] = json.loads(f.read())
            jsonschema.validate(data, self._schema)
            self.data = data
        except OSError as e:
            raise ConfigError(f"Could not read config file '{self._path}': {e}") from e
        except ValueError as e:
            raise ConfigError(f"Invalid JSON in config file '{self._path}': {e}") from e
        except ValidationError as e:
            raise ConfigError(f"Config validation failed for '{self._path}': {e.message}") from e

    def as_dataclass(self) -> AddonConfig:
        """Convert to modern dataclass representation"""
        return AddonConfig.from_dict(self.data)

    def __setitem__(self, name: str, value: Any) -> None:
        self.data[name] = value
        self._write(self.data)

    def _write(self, data: dict[str, Any]) -> None:
        try:
            with self._path.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4, sort_keys=False)
        except OSError as e:
            raise ConfigError(f"Could not write to config file '{self._path}': {e}") from e
