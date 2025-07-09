"""
pytest configuration and fixtures for AADT tests
"""

import json
import pytest
import tempfile
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch

from aadt.config import AddonConfig, Config


@pytest.fixture
def temp_project_dir():
    """Create a temporary directory for test projects"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_addon_config() -> Dict[str, Any]:
    """Sample addon.json configuration for testing"""
    return {
        "display_name": "Test Addon",
        "module_name": "test_addon",
        "repo_name": "test-addon",
        "author": "Test Author",
        "ankiweb_id": "123456",
        "conflicts": [],
        "targets": ["qt6"],
        "contact": "test@example.com",
        "homepage": "https://example.com",
        "tags": "test,addon",
        "min_anki_version": "25.06",
        "max_anki_version": "25.12",
        "tested_anki_version": "25.06",
        "build_config": {
            "output_dir": "dist",
            "trash_patterns": ["*.pyc", "*.pyo", "__pycache__"],
            "ui_config": {
                "ui_dir": "ui",
                "designer_dir": "designer", 
                "resources_dir": "resources"
            }
        }
    }


@pytest.fixture
def addon_config_file(temp_project_dir, sample_addon_config):
    """Create an addon.json file in temp directory"""
    config_path = temp_project_dir / "addon.json"
    with open(config_path, 'w') as f:
        json.dump(sample_addon_config, f, indent=2)
    return config_path


@pytest.fixture
def project_structure(temp_project_dir):
    """Create a basic project structure"""
    src_dir = temp_project_dir / "src" / "test_addon"
    src_dir.mkdir(parents=True)
    
    ui_dir = temp_project_dir / "ui"
    ui_dir.mkdir()
    
    designer_dir = ui_dir / "designer"
    designer_dir.mkdir()
    
    resources_dir = ui_dir / "resources"
    resources_dir.mkdir()
    
    return {
        "root": temp_project_dir,
        "src": src_dir,
        "ui": ui_dir,
        "designer": designer_dir,
        "resources": resources_dir
    }


@pytest.fixture
def mock_git_repo(temp_project_dir):
    """Mock git repository for testing"""
    git_dir = temp_project_dir / ".git"
    git_dir.mkdir()
    
    # Create a mock git config
    config_file = git_dir / "config"
    config_file.write_text("[core]\n    repositoryformatversion = 0\n")
    
    return temp_project_dir


@pytest.fixture
def mock_version_manager():
    """Mock version manager for consistent test results"""
    with patch('aadt.git.VersionManager') as mock:
        mock_instance = mock.return_value
        mock_instance.parse_version.return_value = "1.0.0"
        mock_instance.modtime.return_value = 1234567890
        mock_instance.archive.return_value = None
        yield mock_instance


@pytest.fixture
def sample_ui_file():
    """Sample Qt Designer UI file content"""
    return """<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>Dialog</class>
 <widget class="QDialog" name="Dialog">
  <property name="geometry">
   <rect>
    <x>0</x>
    <y>0</y>
    <width>400</width>
    <height>300</height>
   </rect>
  </property>
  <property name="windowTitle">
   <string>Dialog</string>
  </property>
  <layout class="QVBoxLayout" name="verticalLayout">
   <item>
    <widget class="QLabel" name="label">
     <property name="text">
      <string>Hello World</string>
     </property>
    </widget>
   </item>
  </layout>
 </widget>
</ui>
"""