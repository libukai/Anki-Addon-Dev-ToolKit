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
Utility functions
"""

import fnmatch
import logging
import shutil
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any


def call_shell(command: Sequence[str], echo: bool = False, error_exit: bool = True, **kwargs: Any) -> str:
    try:
        result = subprocess.run(  # noqa: S603
            command,
            capture_output=True,
            text=True,
            check=True,
            **kwargs,
        )
        output = result.stdout
        if echo:
            logging.info(output.strip())
        return output.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"Error while running command: '{' '.join(command)}'")
        if e.stderr:
            logging.error(e.stderr.strip())
        if error_exit:
            sys.exit(1)
        return ""
    except FileNotFoundError:
        logging.error(f"Error: Command not found: '{command[0]}'")
        if error_exit:
            sys.exit(1)
        return ""


def purge(path: str | Path, patterns: list[str], recursive: bool = False) -> None:
    """
    Deletes files matching given patterns using Python's standard library.

    Arguments:
        path: Path to look through
        patterns: List of shell-like glob patterns to delete

    Keyword Arguments:
        recursive: Whether to search recursively (default: False)
    """
    base_path = Path(path)
    if not base_path.is_dir() or not patterns:
        return

    items = base_path.rglob("*") if recursive else base_path.glob("*")

    for item in items:
        if any(fnmatch.fnmatch(item.name, pattern) for pattern in patterns):
            try:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
            except OSError as e:
                logging.warning(f"Could not remove {item}: {e}")


def copy_recursively(source: str | Path, target: str | Path) -> None:
    """
    Recursively copies a source directory to a target using shutil.copytree.
    """
    src_path = Path(source)
    dst_path = Path(target)
    if not src_path.exists():
        logging.warning(f"Source path {src_path} does not exist. Skipping copy.")
        return

    shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
