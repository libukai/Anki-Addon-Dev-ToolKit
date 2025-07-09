# -*- coding: utf-8 -*-

# Anki Add-on Builder
#
# Copyright (C)  2016-2022 Aristotelis P. <https://glutanimate.com/>
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

import contextlib
import os
from pathlib import Path
from shutil import copytree
from typing import Union

from aadt.config import Config
from aadt.ui import UIBuilder
from tests import SAMPLE_PROJECT_NAME, SAMPLE_PROJECT_ROOT, SAMPLE_PROJECTS_FOLDER
from tests.util import list_files


@contextlib.contextmanager
def change_dir(path: Union[Path, str]):
    current = os.getcwd()
    os.chdir(str(path))
    try:
        yield
    finally:
        os.chdir(current)


def test_ui_builder(tmp_path: Path):
    test_project_root = tmp_path / SAMPLE_PROJECT_NAME
    copytree(SAMPLE_PROJECT_ROOT, test_project_root)

    gui_src_path = test_project_root / "src" / "sample" / "gui"

    expected_file_structure = """\
gui/
    forms/
        __init__.py
        qt6/
            form_dialog.py
            __init__.py\
"""

    config = Config(test_project_root / "addon.json")

    with change_dir(test_project_root):
        ui_builder = UIBuilder(dist=test_project_root, config=config)

        ui_builder.build()
        ui_builder.create_qt_shim()

    assert list_files(gui_src_path) == expected_file_structure, "Issue with GUI file structure"

    with (gui_src_path / "forms" / "qt6" / "form_dialog.py").open("r") as f:
        qt6_form_contents = f.read()

    # Test that PyQt6 imports are properly converted to aqt.qt imports
    assert "from aqt.qt import" in qt6_form_contents, "Should have aqt.qt imports"
    assert "from PyQt6" not in qt6_form_contents, "Should not have PyQt6 imports"

    # Test that module prefixes are removed
    assert "QtWidgets." not in qt6_form_contents, "Should not have QtWidgets prefix"
    assert "QtCore." not in qt6_form_contents, "Should not have QtCore prefix"
    assert "QtGui." not in qt6_form_contents, "Should not have QtGui prefix"

    # Test that specific classes are imported correctly
    assert "QVBoxLayout" in qt6_form_contents, "Should use direct QVBoxLayout"
    assert "QLabel" in qt6_form_contents, "Should use direct QLabel"

    # Test that type annotations are added for mypy compliance with intelligent type inference
    assert "def setupUi(self, Dialog: QDialog) -> None:" in qt6_form_contents, (
        "setupUi should have QDialog type annotations"
    )
    assert "def retranslateUi(self, Dialog: QDialog) -> None:" in qt6_form_contents, (
        "retranslateUi should have QDialog type annotations"
    )

    expected_shim_snippet = """\
from .qt6 import *  # noqa: F401\
"""

    with (gui_src_path / "forms" / "__init__.py").open("r") as f:
        shim_contents = f.read()

    assert expected_shim_snippet in shim_contents, "Qt shim not properly constructed"


def test_resources_only_no_forms(tmp_path: Path):
    test_project_root = tmp_path / "project-with-no-forms"
    sample_project_root = SAMPLE_PROJECTS_FOLDER / "project-with-no-forms"
    copytree(sample_project_root, test_project_root)

    gui_src_path = test_project_root / "src" / "sample_project" / "gui"

    # When there are no forms, no GUI directory should be created
    expected_file_structure = ""

    config = Config(test_project_root / "addon.json")

    with change_dir(test_project_root):
        ui_builder = UIBuilder(dist=test_project_root, config=config)

        assert ui_builder.build() is False
        assert ui_builder.create_qt_shim() is False

    assert list_files(gui_src_path) == expected_file_structure, "Issue with GUI file structure"
