"""
Tests for aadt.config module
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from aadt.config import (
    Config, 
    AddonConfig, 
    UIConfig, 
    BuildConfig, 
    ConfigError
)


class TestUIConfig:
    """Test UIConfig dataclass"""
    
    def test_default_values(self):
        """Test default UIConfig values"""
        config = UIConfig()
        
        assert config.ui_dir == "ui"
        assert config.designer_dir == "designer"
        assert config.resources_dir == "resources"
        assert config.forms_package == "forms"
        assert config.exclude_optional_resources is False
    
    def test_from_dict_with_valid_data(self):
        """Test UIConfig creation from dictionary"""
        data = {
            "ui_dir": "custom_ui",
            "designer_dir": "custom_designer",
            "resources_dir": "custom_resources",
            "forms_package": "custom_forms",
            "exclude_optional_resources": True
        }
        
        config = UIConfig.from_dict(data)
        
        assert config.ui_dir == "custom_ui"
        assert config.designer_dir == "custom_designer"
        assert config.resources_dir == "custom_resources"
        assert config.forms_package == "custom_forms"
        assert config.exclude_optional_resources is True
    
    def test_from_dict_with_none(self):
        """Test UIConfig creation from None"""
        config = UIConfig.from_dict(None)
        
        assert config.ui_dir == "ui"
        assert config.designer_dir == "designer"
    
    def test_from_dict_with_invalid_keys(self):
        """Test UIConfig ignores invalid keys"""
        data = {
            "ui_dir": "custom_ui",
            "invalid_key": "should_be_ignored"
        }
        
        config = UIConfig.from_dict(data)
        
        assert config.ui_dir == "custom_ui"
        assert not hasattr(config, "invalid_key")


class TestBuildConfig:
    """Test BuildConfig dataclass"""
    
    def test_default_values(self):
        """Test default BuildConfig values"""
        config = BuildConfig()
        
        assert config.output_dir == "dist"
        assert "*.pyc" in config.trash_patterns
        assert "*.pyo" in config.trash_patterns
        assert "__pycache__" in config.trash_patterns
        assert "." in config.license_paths
        assert "resources" in config.license_paths
        assert isinstance(config.ui_config, UIConfig)
    
    def test_from_dict_with_nested_ui_config(self):
        """Test BuildConfig creation with nested UIConfig"""
        data = {
            "output_dir": "custom_dist",
            "trash_patterns": ["*.tmp"],
            "ui_config": {
                "ui_dir": "custom_ui"
            }
        }
        
        config = BuildConfig.from_dict(data)
        
        assert config.output_dir == "custom_dist"
        assert config.trash_patterns == ["*.tmp"]
        assert config.ui_config.ui_dir == "custom_ui"
    
    def test_from_dict_with_none(self):
        """Test BuildConfig creation from None"""
        config = BuildConfig.from_dict(None)
        
        assert config.output_dir == "dist"
        assert isinstance(config.ui_config, UIConfig)


class TestAddonConfig:
    """Test AddonConfig dataclass"""
    
    def test_from_dict_with_required_fields(self):
        """Test AddonConfig creation with required fields"""
        data = {
            "display_name": "Test Addon",
            "module_name": "test_addon",
            "repo_name": "test-addon",
            "author": "Test Author",
            "conflicts": ["conflict1", "conflict2"]
        }
        
        config = AddonConfig.from_dict(data)
        
        assert config.display_name == "Test Addon"
        assert config.module_name == "test_addon"
        assert config.repo_name == "test-addon"
        assert config.author == "Test Author"
        assert config.conflicts == ["conflict1", "conflict2"]
        assert config.targets == ["qt6"]  # default value
    
    def test_from_dict_with_all_fields(self):
        """Test AddonConfig creation with all fields"""
        data = {
            "display_name": "Test Addon",
            "module_name": "test_addon",
            "repo_name": "test-addon",
            "author": "Test Author",
            "conflicts": [],
            "ankiweb_id": "123456",
            "targets": ["qt6"],
            "contact": "test@example.com",
            "homepage": "https://example.com",
            "tags": "test,addon",
            "copyright_start": 2025,
            "min_anki_version": "25.06",
            "max_anki_version": "25.12",
            "tested_anki_version": "25.06",
            "build_config": {
                "output_dir": "custom_dist"
            }
        }
        
        config = AddonConfig.from_dict(data)
        
        assert config.display_name == "Test Addon"
        assert config.ankiweb_id == "123456"
        assert config.contact == "test@example.com"
        assert config.homepage == "https://example.com"
        assert config.tags == "test,addon"
        assert config.copyright_start == 2025
        assert config.min_anki_version == "25.06"
        assert config.max_anki_version == "25.12"
        assert config.tested_anki_version == "25.06"
        assert config.build_config.output_dir == "custom_dist"
    
    def test_to_dict_excludes_none_values(self):
        """Test AddonConfig.to_dict() excludes None values"""
        config = AddonConfig(
            display_name="Test Addon",
            module_name="test_addon",
            repo_name="test-addon",
            author="Test Author",
            conflicts=[],
            ankiweb_id=None,  # This should be excluded
            contact="test@example.com"
        )
        
        result = config.to_dict()
        
        assert "display_name" in result
        assert "contact" in result
        assert "ankiweb_id" not in result


class TestConfig:
    """Test Config class"""
    
    def test_config_initialization_success(self, addon_config_file):
        """Test successful Config initialization"""
        config = Config(addon_config_file)
        
        assert config["display_name"] == "Test Addon"
        assert config["module_name"] == "test_addon"
        assert config["author"] == "Test Author"
    
    def test_config_initialization_file_not_found(self):
        """Test Config initialization with non-existent file"""
        with pytest.raises(ConfigError) as exc_info:
            Config("/nonexistent/path/addon.json")
        
        assert "Could not read config file" in str(exc_info.value)
    
    def test_config_initialization_invalid_json(self, temp_project_dir):
        """Test Config initialization with invalid JSON"""
        config_path = temp_project_dir / "invalid.json"
        config_path.write_text("{ invalid json }")
        
        with pytest.raises(ConfigError) as exc_info:
            Config(config_path)
        
        assert "Invalid JSON" in str(exc_info.value)
    
    def test_config_initialization_schema_validation_error(self, temp_project_dir):
        """Test Config initialization with schema validation error"""
        config_path = temp_project_dir / "invalid_schema.json"
        config_data = {
            "display_name": "Test Addon",
            # Missing required fields
        }
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
        
        with pytest.raises(ConfigError) as exc_info:
            Config(config_path)
        
        assert "Config validation failed" in str(exc_info.value)
    
    def test_as_dataclass(self, addon_config_file):
        """Test Config.as_dataclass() method"""
        config = Config(addon_config_file)
        addon_config = config.as_dataclass()
        
        assert isinstance(addon_config, AddonConfig)
        assert addon_config.display_name == "Test Addon"
        assert addon_config.module_name == "test_addon"
    
    def test_setitem_updates_config(self, addon_config_file):
        """Test Config.__setitem__ updates configuration"""
        config = Config(addon_config_file)
        
        with patch.object(config, '_write') as mock_write:
            config["display_name"] = "Updated Addon"
            
            assert config["display_name"] == "Updated Addon"
            mock_write.assert_called_once()
    
    def test_write_method_success(self, addon_config_file):
        """Test Config._write method success"""
        config = Config(addon_config_file)
        
        test_data = {"test": "data"}
        config._write(test_data)
        
        # Verify file was written
        with open(addon_config_file) as f:
            written_data = json.load(f)
        
        assert written_data == test_data
    
    def test_write_method_failure(self, addon_config_file):
        """Test Config._write method failure"""
        config = Config(addon_config_file)
        
        # Make file unwritable
        addon_config_file.chmod(0o444)
        
        with pytest.raises(ConfigError) as exc_info:
            config._write({"test": "data"})
        
        assert "Could not write to config file" in str(exc_info.value)
        
        # Restore permissions
        addon_config_file.chmod(0o644)
    
    def test_default_config_path(self, temp_project_dir):
        """Test Config uses default path when none provided"""
        with patch('aadt.config.PATH_CONFIG', temp_project_dir / "addon.json"):
            # Create a minimal valid config
            config_data = {
                "display_name": "Test Addon",
                "module_name": "test_addon",
                "repo_name": "test-addon",
                "author": "Test Author",
                "conflicts": [],
                "ankiweb_id": "123456",
                "targets": ["qt6"]
            }
            
            with open(temp_project_dir / "addon.json", 'w') as f:
                json.dump(config_data, f)
            
            config = Config()
            assert config["display_name"] == "Test Addon"


class TestConfigIntegration:
    """Integration tests for Config system"""
    
    def test_full_config_workflow(self, temp_project_dir):
        """Test complete config workflow"""
        config_path = temp_project_dir / "addon.json"
        
        # Create initial config
        initial_data = {
            "display_name": "Test Addon",
            "module_name": "test_addon",
            "repo_name": "test-addon",
            "author": "Test Author",
            "conflicts": [],
            "ankiweb_id": "123456",
            "targets": ["qt6"],
            "build_config": {
                "output_dir": "custom_dist",
                "ui_config": {
                    "ui_dir": "custom_ui"
                }
            }
        }
        
        with open(config_path, 'w') as f:
            json.dump(initial_data, f)
        
        # Load and verify config
        config = Config(config_path)
        addon_config = config.as_dataclass()
        
        assert addon_config.display_name == "Test Addon"
        assert addon_config.build_config.output_dir == "custom_dist"
        assert addon_config.build_config.ui_config.ui_dir == "custom_ui"
        
        # Update config
        config["display_name"] = "Updated Addon"
        
        # Reload and verify persistence
        config2 = Config(config_path)
        assert config2["display_name"] == "Updated Addon"