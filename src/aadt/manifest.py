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

import json
import logging
from pathlib import Path
from typing import Any, Literal

from aadt.config import Config

DistType = Literal["local"] | Literal["ankiweb"]


class ManifestUtils:
    @classmethod
    def generate_and_write_manifest(
        cls,
        addon_properties: Config,
        version: str,
        dist_type: DistType,
        target_dir: Path,
        mod_time: str,
    ) -> None:
        logging.info("Writing manifest...")
        manifest = cls.generate_manifest_from_properties(
            addon_properties=addon_properties,
            version=version,
            dist_type=dist_type,
            mod_time=mod_time,
        )
        cls.write_manifest(manifest=manifest, target_dir=target_dir)

    @classmethod
    def generate_manifest_from_properties(
        cls,
        addon_properties: Config,
        version: str,
        dist_type: DistType,
        mod_time: str,
    ) -> dict[str, Any]:
        manifest = {
            "name": addon_properties["display_name"],
            "package": addon_properties["module_name"],
        }

        # Add required/common fields
        if version:
            manifest["version"] = version
        if addon_properties.get("author"):
            manifest["author"] = addon_properties["author"]

        # Add optional fields only if they have values
        if addon_properties.get("ankiweb_id"):
            manifest["ankiweb_id"] = addon_properties["ankiweb_id"]
        if addon_properties.get("homepage"):
            manifest["homepage"] = addon_properties["homepage"]
        if addon_properties.get("contact"):
            manifest["contact"] = addon_properties["contact"]
        if addon_properties.get("description"):
            manifest["description"] = addon_properties["description"]
        elif addon_properties.get("tags"):
            manifest["description"] = addon_properties["tags"]  # Fallback to tags

        # Add repository info if homepage looks like a git repo
        if addon_properties.get("homepage") and "github.com" in addon_properties["homepage"]:
            manifest["repository"] = {
                "type": "git",
                "url": addon_properties["homepage"],
            }

        # Add dependencies (empty for now)
        manifest["dependencies"] = {}

        # Add version specifiers:

        min_anki_version = addon_properties.get("min_anki_version")
        max_anki_version = addon_properties.get("max_anki_version")
        tested_anki_version = addon_properties.get("tested_anki_version")

        if min_anki_version:
            manifest["min_point_version"] = cls._min_point_version(min_anki_version)

        if max_anki_version or tested_anki_version:
            manifest["max_point_version"] = cls._max_point_version(max_anki_version, tested_anki_version)

        # Update values for distribution type
        if dist_type == "ankiweb" and addon_properties.get("ankiweb_id"):
            manifest["package"] = addon_properties["ankiweb_id"]

        return manifest

    @classmethod
    def write_manifest(cls, manifest: dict[str, Any], target_dir: Path) -> None:
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / "manifest.json"
        with target_path.open("w", encoding="utf-8") as manifest_file:
            manifest_file.write(json.dumps(manifest, indent=4, sort_keys=False, ensure_ascii=False))

    @classmethod
    def _anki_version_to_point_version(cls, version: str) -> int:
        return int(version.split(".")[-1])

    @classmethod
    def _min_point_version(cls, min_anki_version: str) -> int:
        return cls._anki_version_to_point_version(min_anki_version)

    @classmethod
    def _max_point_version(cls, max_anki_version: str | None, tested_anki_version: str | None) -> int | None:
        if max_anki_version:
            # -version in "max_point_version" specifies a definite max supported version
            return -1 * cls._anki_version_to_point_version(max_anki_version)
        elif tested_anki_version:
            # +version in "max_point_version" indicates version tested on
            return cls._anki_version_to_point_version(tested_anki_version)
        return None
