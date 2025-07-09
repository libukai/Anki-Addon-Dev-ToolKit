"""
Tests for aadt.builder module
"""

import os
import shutil
import zipfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, call

from aadt.builder import (
    AddonBuilder, 
    BuildError, 
    VersionError, 
    clean_repo
)
from aadt.config import Config


class TestCleanRepo:
    """Test clean_repo function"""
    
    def test_clean_repo_default_patterns(self, temp_project_dir):
        """Test clean_repo with default trash patterns"""
        # Create test files
        test_files = [
            temp_project_dir / "test.pyc",
            temp_project_dir / "test.pyo",
            temp_project_dir / "__pycache__" / "test.pyc"
        ]
        
        for file in test_files:
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text("test")
        
        # Create dist directory
        dist_dir = temp_project_dir / "dist" / "build"
        dist_dir.mkdir(parents=True)
        (dist_dir / "test.txt").write_text("test")
        
        with patch('aadt.builder.PATH_DIST', dist_dir):
            with patch('aadt.builder.purge') as mock_purge:
                clean_repo()
                
                assert not dist_dir.exists()
                mock_purge.assert_called_once_with(
                    ".", 
                    ["*.pyc", "*.pyo", "__pycache__"], 
                    recursive=True
                )
    
    def test_clean_repo_custom_patterns(self, temp_project_dir):
        """Test clean_repo with custom trash patterns"""
        custom_patterns = ["*.tmp", "*.log"]
        
        with patch('aadt.builder.PATH_DIST', temp_project_dir / "nonexistent"):
            with patch('aadt.builder.purge') as mock_purge:
                clean_repo(custom_patterns)
                
                mock_purge.assert_called_once_with(
                    ".", 
                    custom_patterns, 
                    recursive=True
                )


class TestAddonBuilder:
    """Test AddonBuilder class"""
    
    def test_init_with_valid_version(self, addon_config_file, mock_version_manager):
        """Test AddonBuilder initialization with valid version"""
        with patch('aadt.builder.PATH_PROJECT_ROOT', addon_config_file.parent):
            with patch('aadt.builder.Config') as mock_config:
                mock_config.return_value.as_dataclass.return_value.build_config.archive_exclude_patterns = []
                
                builder = AddonBuilder(version="1.0.0")
                
                assert builder._version == "1.0.0"
                mock_version_manager.parse_version.assert_called_once_with("1.0.0")
    
    def test_init_with_invalid_version(self, addon_config_file):
        """Test AddonBuilder initialization with invalid version"""
        with patch('aadt.builder.PATH_PROJECT_ROOT', addon_config_file.parent):
            with patch('aadt.builder.Config') as mock_config:
                mock_config.return_value.as_dataclass.return_value.build_config.archive_exclude_patterns = []
                
                with patch('aadt.git.VersionManager') as mock_vm:
                    mock_vm.return_value.parse_version.return_value = None
                    
                    with pytest.raises(VersionError) as exc_info:
                        AddonBuilder(version="invalid")
                    
                    assert "Version could not be determined" in str(exc_info.value)
    
    def test_init_without_version(self, addon_config_file, mock_version_manager):
        """Test AddonBuilder initialization without version"""
        with patch('aadt.builder.PATH_PROJECT_ROOT', addon_config_file.parent):
            with patch('aadt.builder.Config') as mock_config:
                mock_config.return_value.as_dataclass.return_value.build_config.archive_exclude_patterns = []
                
                builder = AddonBuilder()
                
                mock_version_manager.parse_version.assert_called_once_with(None)
    
    def test_build_invalid_disttype(self, addon_config_file, mock_version_manager):
        """Test build with invalid distribution type"""
        with patch('aadt.builder.PATH_PROJECT_ROOT', addon_config_file.parent):
            with patch('aadt.builder.Config') as mock_config:
                mock_config.return_value.as_dataclass.return_value.build_config.archive_exclude_patterns = []
                
                builder = AddonBuilder(version="1.0.0")
                
                with pytest.raises(BuildError) as exc_info:
                    builder.build(disttype="invalid")
                
                assert "Invalid distribution type" in str(exc_info.value)
    
    def test_build_success(self, addon_config_file, mock_version_manager):
        """Test successful build process"""
        with patch('aadt.builder.PATH_PROJECT_ROOT', addon_config_file.parent):
            with patch('aadt.builder.Config') as mock_config:
                mock_config.return_value.as_dataclass.return_value.build_config.archive_exclude_patterns = []
                mock_addon_config = mock_config.return_value.as_dataclass.return_value
                mock_addon_config.display_name = "Test Addon"
                
                builder = AddonBuilder(version="1.0.0")
                
                with patch.object(builder, 'create_dist') as mock_create:
                    with patch.object(builder, 'build_dist') as mock_build:
                        with patch.object(builder, 'package_dist') as mock_package:
                            with patch.object(builder, '_cleanup_dist') as mock_cleanup:
                                mock_package.return_value = Path("/test/path")
                                
                                result = builder.build(disttype="local")
                                
                                mock_create.assert_called_once()
                                mock_build.assert_called_once_with(disttype="local")
                                mock_package.assert_called_once_with(disttype="local")
                                mock_cleanup.assert_called_once()
                                assert result == Path("/test/path")
    
    def test_create_dist(self, addon_config_file, mock_version_manager):
        """Test create_dist method"""
        with patch('aadt.builder.PATH_PROJECT_ROOT', addon_config_file.parent):
            with patch('aadt.builder.Config') as mock_config:
                mock_config.return_value.as_dataclass.return_value.build_config.archive_exclude_patterns = []
                mock_addon_config = mock_config.return_value.as_dataclass.return_value
                mock_addon_config.display_name = "Test Addon"
                mock_addon_config.build_config.trash_patterns = ["*.pyc"]
                
                builder = AddonBuilder(version="1.0.0")
                
                with patch('aadt.builder.clean_repo') as mock_clean:
                    with patch('aadt.builder.PATH_DIST') as mock_dist:
                        mock_dist.mkdir = MagicMock()
                        
                        builder.create_dist()
                        
                        mock_clean.assert_called_once_with(trash_patterns=["*.pyc"])
                        mock_dist.mkdir.assert_called_once_with(parents=True)
                        mock_version_manager.archive.assert_called_once_with("1.0.0", mock_dist)
    
    def test_build_dist(self, addon_config_file, mock_version_manager):
        """Test build_dist method"""
        with patch('aadt.builder.PATH_PROJECT_ROOT', addon_config_file.parent):
            with patch('aadt.builder.Config') as mock_config:
                mock_config.return_value.as_dataclass.return_value.build_config.archive_exclude_patterns = []
                
                builder = AddonBuilder(version="1.0.0")
                
                with patch.object(builder, '_copy_licenses') as mock_licenses:
                    with patch.object(builder, '_copy_changelog') as mock_changelog:
                        with patch.object(builder, '_copy_optional_icons') as mock_icons:
                            with patch.object(builder, '_write_manifest') as mock_manifest:
                                with patch('aadt.builder.UIBuilder') as mock_ui_builder:
                                    with patch.object(builder, '_path_changelog') as mock_changelog_path:
                                        with patch.object(builder, '_path_optional_icons') as mock_icons_path:
                                            
                                            # Setup mocks
                                            mock_changelog_path.exists.return_value = True
                                            mock_icons_path.exists.return_value = True
                                            mock_ui_instance = mock_ui_builder.return_value
                                            mock_ui_instance.build.return_value = True
                                            
                                            builder.build_dist(disttype="local")
                                            
                                            mock_licenses.assert_called_once()
                                            mock_changelog.assert_called_once()
                                            mock_icons.assert_called_once()
                                            mock_manifest.assert_called_once_with("local")
                                            mock_ui_instance.build.assert_called_once()
                                            mock_ui_instance.create_qt_shim.assert_called_once()
    
    def test_package_dist(self, addon_config_file, mock_version_manager, temp_project_dir):
        """Test package_dist method"""
        with patch('aadt.builder.PATH_PROJECT_ROOT', addon_config_file.parent):
            with patch('aadt.builder.Config') as mock_config:
                mock_config.return_value.as_dataclass.return_value.build_config.archive_exclude_patterns = []
                mock_addon_config = mock_config.return_value.as_dataclass.return_value
                mock_addon_config.repo_name = "test-addon"
                mock_addon_config.build_config.output_dir = "dist"
                
                builder = AddonBuilder(version="1.0.0")
                
                with patch.object(builder, '_package') as mock_package:
                    mock_package.return_value = Path("/test/path")
                    
                    result = builder.package_dist(disttype="local")
                    
                    mock_package.assert_called_once_with("local")
                    assert result == Path("/test/path")
    
    def test_package_method(self, addon_config_file, mock_version_manager, temp_project_dir):
        """Test _package method"""
        with patch('aadt.builder.PATH_PROJECT_ROOT', addon_config_file.parent):
            with patch('aadt.builder.Config') as mock_config:
                mock_config.return_value.as_dataclass.return_value.build_config.archive_exclude_patterns = []
                mock_addon_config = mock_config.return_value.as_dataclass.return_value
                mock_addon_config.repo_name = "test-addon"
                mock_addon_config.build_config.output_dir = "dist"
                
                builder = AddonBuilder(version="1.0.0")
                
                # Create a mock module directory with test files
                module_dir = temp_project_dir / "test_module"
                module_dir.mkdir()
                test_file = module_dir / "test.py"
                test_file.write_text("# test file")
                
                with patch.object(builder, '_path_dist_module', module_dir):
                    result = builder._package("local")
                    
                    expected_path = addon_config_file.parent / "dist" / "test-addon-1.0.0.ankiaddon"
                    assert result == expected_path
                    assert result.exists()
                    
                    # Verify zip contents
                    with zipfile.ZipFile(result, 'r') as zip_file:
                        assert "test.py" in zip_file.namelist()
    
    def test_write_manifest(self, addon_config_file, mock_version_manager):
        """Test _write_manifest method"""
        with patch('aadt.builder.PATH_PROJECT_ROOT', addon_config_file.parent):
            with patch('aadt.builder.Config') as mock_config:
                mock_config.return_value.as_dataclass.return_value.build_config.archive_exclude_patterns = []
                
                builder = AddonBuilder(version="1.0.0")
                
                with patch('aadt.builder.ManifestUtils') as mock_manifest:
                    builder._write_manifest("local")
                    
                    mock_manifest.generate_and_write_manifest.assert_called_once_with(
                        addon_properties=mock_config.return_value,
                        version="1.0.0",
                        dist_type="local",
                        target_dir=builder._path_dist_module,
                        mod_time=1234567890
                    )
    
    def test_copy_licenses(self, addon_config_file, mock_version_manager, temp_project_dir):
        """Test _copy_licenses method"""
        with patch('aadt.builder.PATH_PROJECT_ROOT', addon_config_file.parent):
            with patch('aadt.builder.Config') as mock_config:
                mock_config.return_value.as_dataclass.return_value.build_config.archive_exclude_patterns = []
                mock_addon_config = mock_config.return_value.as_dataclass.return_value
                mock_addon_config.module_name = "test_addon"
                mock_addon_config.build_config.license_paths = ["."]
                
                builder = AddonBuilder(version="1.0.0")
                
                # Create license files
                license_dir = temp_project_dir / "licenses"
                license_dir.mkdir()
                license_file = license_dir / "LICENSE"
                license_file.write_text("MIT License")
                
                module_dir = temp_project_dir / "module"
                module_dir.mkdir()
                
                with patch.object(builder, '_paths_licenses', [license_dir]):
                    with patch.object(builder, '_path_dist_module', module_dir):
                        builder._copy_licenses()
                        
                        target_file = module_dir / "LICENSE.txt"
                        assert target_file.exists()
                        assert target_file.read_text() == "MIT License"
    
    def test_copy_changelog(self, addon_config_file, mock_version_manager, temp_project_dir):
        """Test _copy_changelog method"""
        with patch('aadt.builder.PATH_PROJECT_ROOT', addon_config_file.parent):
            with patch('aadt.builder.Config') as mock_config:
                mock_config.return_value.as_dataclass.return_value.build_config.archive_exclude_patterns = []
                mock_addon_config = mock_config.return_value.as_dataclass.return_value
                mock_addon_config.module_name = "test_addon"
                
                builder = AddonBuilder(version="1.0.0")
                
                # Create changelog file
                changelog_file = temp_project_dir / "CHANGELOG.md"
                changelog_file.write_text("# Changelog")
                
                module_dir = temp_project_dir / "module"
                module_dir.mkdir()
                
                with patch.object(builder, '_path_changelog', changelog_file):
                    with patch.object(builder, '_path_dist_module', module_dir):
                        builder._copy_changelog()
                        
                        target_file = module_dir / "CHANGELOG.md"
                        assert target_file.exists()
                        assert target_file.read_text() == "# Changelog"
    
    def test_copy_optional_icons(self, addon_config_file, mock_version_manager):
        """Test _copy_optional_icons method"""
        with patch('aadt.builder.PATH_PROJECT_ROOT', addon_config_file.parent):
            with patch('aadt.builder.Config') as mock_config:
                mock_config.return_value.as_dataclass.return_value.build_config.archive_exclude_patterns = []
                
                builder = AddonBuilder(version="1.0.0")
                
                with patch('aadt.builder.copy_recursively') as mock_copy:
                    with patch('aadt.builder.PATH_DIST', Path("/test/dist")):
                        builder._copy_optional_icons()
                        
                        mock_copy.assert_called_once_with(
                            builder._path_optional_icons,
                            Path("/test/dist") / "resources" / "icons" / ""
                        )
    
    def test_cleanup_dist(self, addon_config_file, mock_version_manager, temp_project_dir):
        """Test _cleanup_dist method"""
        with patch('aadt.builder.PATH_PROJECT_ROOT', addon_config_file.parent):
            with patch('aadt.builder.Config') as mock_config:
                mock_config.return_value.as_dataclass.return_value.build_config.archive_exclude_patterns = []
                
                builder = AddonBuilder(version="1.0.0")
                
                # Create dist directory
                dist_dir = temp_project_dir / "dist"
                dist_dir.mkdir()
                (dist_dir / "test.txt").write_text("test")
                
                with patch('aadt.builder.PATH_DIST', dist_dir):
                    builder._cleanup_dist()
                    
                    assert not dist_dir.exists()
    
    def test_callback_archive_called(self, addon_config_file, mock_version_manager):
        """Test that callback_archive is called during build_dist"""
        with patch('aadt.builder.PATH_PROJECT_ROOT', addon_config_file.parent):
            with patch('aadt.builder.Config') as mock_config:
                mock_config.return_value.as_dataclass.return_value.build_config.archive_exclude_patterns = []
                
                callback_mock = MagicMock()
                builder = AddonBuilder(version="1.0.0", callback_archive=callback_mock)
                
                with patch.object(builder, '_copy_licenses'):
                    with patch.object(builder, '_write_manifest'):
                        with patch('aadt.builder.UIBuilder') as mock_ui_builder:
                            mock_ui_builder.return_value.build.return_value = False
                            
                            builder.build_dist()
                            
                            callback_mock.assert_called_once()


class TestBuilderIntegration:
    """Integration tests for builder functionality"""
    
    def test_full_build_workflow(self, temp_project_dir, sample_addon_config):
        """Test complete build workflow"""
        # Setup project structure
        config_file = temp_project_dir / "addon.json"
        with open(config_file, 'w') as f:
            import json
            json.dump(sample_addon_config, f)
        
        src_dir = temp_project_dir / "src" / "test_addon"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("# Test addon")
        
        # Create git repo mock
        git_dir = temp_project_dir / ".git"
        git_dir.mkdir()
        
        with patch('aadt.builder.PATH_PROJECT_ROOT', temp_project_dir):
            with patch('aadt.git.VersionManager') as mock_vm:
                mock_vm.return_value.parse_version.return_value = "1.0.0"
                mock_vm.return_value.modtime.return_value = 1234567890
                mock_vm.return_value.archive.return_value = None
                
                with patch('aadt.builder.UIBuilder') as mock_ui:
                    mock_ui.return_value.build.return_value = False
                    
                    builder = AddonBuilder(version="1.0.0")
                    
                    # This should not raise any exceptions
                    with patch.object(builder, '_cleanup_dist'):
                        result = builder.build(disttype="local")
                        
                        assert result.name.endswith(".ankiaddon")
                        assert "test-addon" in result.name
                        assert "1.0.0" in result.name