"""
Tests for aadt.cli module
"""

import argparse
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import pytest

from aadt.cli import (
    CLIError,
    validate_cwd,
    build,
    ui,
    manifest,
    create_dist,
    build_dist,
    package_dist,
    clean,
    init,
    link,
    test,
    claude,
    _copy_file,
    _get_dist_list,
    _execute_multi_dist_task,
    construct_parser,
    main
)


class TestValidateCwd:
    """Test validate_cwd function"""
    
    def test_validate_cwd_valid_project(self, temp_project_dir):
        """Test validate_cwd with valid project structure"""
        # Create src directory and addon.json
        src_dir = temp_project_dir / "src"
        src_dir.mkdir()
        addon_json = temp_project_dir / "addon.json"
        addon_json.write_text("{}")
        
        with patch('aadt.cli.PATH_PROJECT_ROOT', temp_project_dir):
            with patch('aadt.cli.PATH_CONFIG', addon_json):
                assert validate_cwd() is True
    
    def test_validate_cwd_missing_src(self, temp_project_dir):
        """Test validate_cwd with missing src directory"""
        addon_json = temp_project_dir / "addon.json"
        addon_json.write_text("{}")
        
        with patch('aadt.cli.PATH_PROJECT_ROOT', temp_project_dir):
            with patch('aadt.cli.PATH_CONFIG', addon_json):
                assert validate_cwd() is False
    
    def test_validate_cwd_missing_config(self, temp_project_dir):
        """Test validate_cwd with missing addon.json"""
        src_dir = temp_project_dir / "src"
        src_dir.mkdir()
        
        with patch('aadt.cli.PATH_PROJECT_ROOT', temp_project_dir):
            with patch('aadt.cli.PATH_CONFIG', temp_project_dir / "addon.json"):
                assert validate_cwd() is False


class TestHelperFunctions:
    """Test CLI helper functions"""
    
    def test_get_dist_list_single(self):
        """Test _get_dist_list with single distribution"""
        result = _get_dist_list("local")
        assert result == ["local"]
    
    def test_get_dist_list_all(self):
        """Test _get_dist_list with all distributions"""
        with patch('aadt.cli.DIST_TYPES', ["local", "ankiweb"]):
            result = _get_dist_list("all")
            assert result == ["local", "ankiweb"]
    
    def test_execute_multi_dist_task_success(self):
        """Test _execute_multi_dist_task with successful execution"""
        mock_task = MagicMock()
        mock_builder = MagicMock()
        
        with patch('aadt.cli.AddonBuilder') as mock_builder_class:
            mock_builder_class.return_value = mock_builder
            
            _execute_multi_dist_task(
                task_name="test",
                dists=["local", "ankiweb"],
                task_func=mock_task,
                version="1.0.0",
                extra_arg="test"
            )
            
            mock_builder_class.assert_called_once_with(version="1.0.0")
            assert mock_task.call_count == 2
            mock_task.assert_has_calls([
                call(mock_builder, "local", extra_arg="test"),
                call(mock_builder, "ankiweb", extra_arg="test")
            ])
    
    def test_execute_multi_dist_task_version_error(self):
        """Test _execute_multi_dist_task with version error"""
        mock_task = MagicMock()
        
        with patch('aadt.cli.AddonBuilder') as mock_builder_class:
            from aadt.builder import VersionError
            mock_builder_class.side_effect = VersionError("Version error")
            
            with pytest.raises(CLIError) as exc_info:
                _execute_multi_dist_task(
                    task_name="test",
                    dists=["local"],
                    task_func=mock_task,
                    version="invalid"
                )
            
            assert "Failed to initialize builder" in str(exc_info.value)


class TestCommandFunctions:
    """Test CLI command functions"""
    
    def test_build_command(self):
        """Test build command function"""
        args = argparse.Namespace(dist="local", version="1.0.0")
        
        with patch('aadt.cli._execute_multi_dist_task') as mock_execute:
            build(args)
            
            mock_execute.assert_called_once()
            call_args = mock_execute.call_args
            assert call_args[1]["task_name"] == "build"
            assert call_args[1]["dists"] == ["local"]
            assert call_args[1]["version"] == "1.0.0"
    
    def test_ui_command(self):
        """Test ui command function"""
        args = argparse.Namespace()
        
        with patch('aadt.cli.UIBuilder') as mock_ui_builder:
            with patch('aadt.cli.Config') as mock_config:
                mock_ui_instance = mock_ui_builder.return_value
                mock_ui_instance.build.return_value = True
                
                ui(args)
                
                mock_ui_builder.assert_called_once()
                mock_ui_instance.build.assert_called_once()
                mock_ui_instance.create_qt_shim.assert_called_once()
    
    def test_ui_command_no_shim(self):
        """Test ui command function without shim creation"""
        args = argparse.Namespace()
        
        with patch('aadt.cli.UIBuilder') as mock_ui_builder:
            with patch('aadt.cli.Config') as mock_config:
                mock_ui_instance = mock_ui_builder.return_value
                mock_ui_instance.build.return_value = False
                
                ui(args)
                
                mock_ui_builder.assert_called_once()
                mock_ui_instance.build.assert_called_once()
                mock_ui_instance.create_qt_shim.assert_not_called()
    
    def test_manifest_command(self):
        """Test manifest command function"""
        args = argparse.Namespace(dist="local", version="1.0.0")
        
        with patch('aadt.cli.Config') as mock_config:
            with patch('aadt.cli.VersionManager') as mock_vm:
                with patch('aadt.cli.ManifestUtils') as mock_manifest:
                    mock_addon_config = MagicMock()
                    mock_addon_config.module_name = "test_addon"
                    mock_addon_config.build_config.archive_exclude_patterns = []
                    mock_config.return_value.as_dataclass.return_value = mock_addon_config
                    
                    mock_vm_instance = mock_vm.return_value
                    mock_vm_instance.parse_version.return_value = "1.0.0"
                    mock_vm_instance.modtime.return_value = 1234567890
                    
                    manifest(args)
                    
                    mock_manifest.generate_and_write_manifest.assert_called_once()
    
    def test_manifest_command_error(self):
        """Test manifest command with error"""
        args = argparse.Namespace(dist="local", version="1.0.0")
        
        with patch('aadt.cli.Config') as mock_config:
            mock_config.side_effect = Exception("Config error")
            
            with pytest.raises(CLIError) as exc_info:
                manifest(args)
            
            assert "Failed to generate manifest" in str(exc_info.value)
    
    def test_create_dist_command(self):
        """Test create_dist command function"""
        args = argparse.Namespace(version="1.0.0")
        
        with patch('aadt.cli.AddonBuilder') as mock_builder:
            mock_builder_instance = mock_builder.return_value
            
            create_dist(args)
            
            mock_builder.assert_called_once_with(version="1.0.0")
            mock_builder_instance.create_dist.assert_called_once()
    
    def test_create_dist_command_error(self):
        """Test create_dist command with version error"""
        args = argparse.Namespace(version="invalid")
        
        with patch('aadt.cli.AddonBuilder') as mock_builder:
            from aadt.builder import VersionError
            mock_builder.side_effect = VersionError("Version error")
            
            with pytest.raises(CLIError) as exc_info:
                create_dist(args)
            
            assert "Failed to create distribution" in str(exc_info.value)
    
    def test_build_dist_command(self):
        """Test build_dist command function"""
        args = argparse.Namespace(dist="local", version="1.0.0")
        
        with patch('aadt.cli._execute_multi_dist_task') as mock_execute:
            build_dist(args)
            
            mock_execute.assert_called_once()
            call_args = mock_execute.call_args
            assert call_args[1]["task_name"] == "build_dist"
    
    def test_package_dist_command(self):
        """Test package_dist command function"""
        args = argparse.Namespace(dist="local", version="1.0.0")
        
        with patch('aadt.cli._execute_multi_dist_task') as mock_execute:
            package_dist(args)
            
            mock_execute.assert_called_once()
            call_args = mock_execute.call_args
            assert call_args[1]["task_name"] == "package_dist"
    
    def test_clean_command(self):
        """Test clean command function"""
        args = argparse.Namespace()
        
        with patch('aadt.cli.clean_repo') as mock_clean:
            clean(args)
            
            mock_clean.assert_called_once()
    
    def test_init_command(self):
        """Test init command function"""
        args = argparse.Namespace(directory="test_dir", yes=False)
        
        with patch('aadt.cli.ProjectInitializer') as mock_initializer:
            mock_initializer_instance = mock_initializer.return_value
            
            init(args)
            
            mock_initializer.assert_called_once()
            mock_initializer_instance.init_project.assert_called_once_with(interactive=True)
    
    def test_init_command_current_dir(self):
        """Test init command with current directory"""
        args = argparse.Namespace(directory=None, yes=True)
        
        with patch('aadt.cli.ProjectInitializer') as mock_initializer:
            mock_initializer_instance = mock_initializer.return_value
            
            init(args)
            
            mock_initializer_instance.init_project.assert_called_once_with(interactive=False)
    
    def test_init_command_error(self):
        """Test init command with initialization error"""
        args = argparse.Namespace(directory="test_dir", yes=False)
        
        with patch('aadt.cli.ProjectInitializer') as mock_initializer:
            from aadt.init import ProjectInitializationError
            mock_initializer.return_value.init_project.side_effect = ProjectInitializationError("Init error")
            
            with pytest.raises(CLIError) as exc_info:
                init(args)
            
            assert "Failed to initialize project" in str(exc_info.value)
    
    def test_link_command(self):
        """Test link command function"""
        args = argparse.Namespace(unlink=False)
        
        with patch('aadt.cli.Config') as mock_config:
            with patch('aadt.cli.AddonLinker') as mock_linker:
                mock_linker_instance = mock_linker.return_value
                mock_linker_instance.link_addon.return_value = True
                
                link(args)
                
                mock_linker_instance.link_addon.assert_called_once()
    
    def test_link_command_unlink(self):
        """Test link command with unlink option"""
        args = argparse.Namespace(unlink=True)
        
        with patch('aadt.cli.Config') as mock_config:
            with patch('aadt.cli.AddonLinker') as mock_linker:
                mock_linker_instance = mock_linker.return_value
                mock_linker_instance.unlink_addon.return_value = True
                
                link(args)
                
                mock_linker_instance.unlink_addon.assert_called_once()
    
    def test_link_command_failure(self):
        """Test link command with failure"""
        args = argparse.Namespace(unlink=False)
        
        with patch('aadt.cli.Config') as mock_config:
            with patch('aadt.cli.AddonLinker') as mock_linker:
                mock_linker_instance = mock_linker.return_value
                mock_linker_instance.link_addon.return_value = False
                
                with pytest.raises(CLIError) as exc_info:
                    link(args)
                
                assert "Failed to link add-on" in str(exc_info.value)
    
    def test_test_command(self):
        """Test test command function"""
        args = argparse.Namespace()
        
        with patch('aadt.cli.Config') as mock_config:
            with patch('aadt.cli.AddonLinker') as mock_linker:
                with patch('aadt.cli.aqt') as mock_aqt:
                    mock_linker_instance = mock_linker.return_value
                    mock_linker_instance.link_addon.return_value = True
                    
                    test(args)
                    
                    mock_linker_instance.link_addon.assert_called_once()
                    mock_aqt.run.assert_called_once()
    
    def test_test_command_link_failure(self):
        """Test test command with link failure"""
        args = argparse.Namespace()
        
        with patch('aadt.cli.Config') as mock_config:
            with patch('aadt.cli.AddonLinker') as mock_linker:
                mock_linker_instance = mock_linker.return_value
                mock_linker_instance.link_addon.return_value = False
                
                with pytest.raises(CLIError) as exc_info:
                    test(args)
                
                assert "Failed to link add-on for testing" in str(exc_info.value)
    
    def test_test_command_anki_import_error(self):
        """Test test command with Anki import error"""
        args = argparse.Namespace()
        
        with patch('aadt.cli.Config') as mock_config:
            with patch('aadt.cli.AddonLinker') as mock_linker:
                mock_linker_instance = mock_linker.return_value
                mock_linker_instance.link_addon.return_value = True
                
                with patch('aadt.cli.aqt', side_effect=ImportError("No module named 'aqt'")):
                    with pytest.raises(CLIError) as exc_info:
                        test(args)
                    
                    assert "Anki (aqt) not found" in str(exc_info.value)


class TestCopyFile:
    """Test _copy_file helper function"""
    
    def test_copy_file_success(self, temp_project_dir):
        """Test successful file copy"""
        source = temp_project_dir / "source.txt"
        target = temp_project_dir / "target.txt"
        
        source.write_text("test content")
        
        result = _copy_file(source, target, force=False, file_description="test file")
        
        assert result is True
        assert target.exists()
        assert target.read_text() == "test content"
    
    def test_copy_file_source_not_found(self, temp_project_dir):
        """Test file copy with missing source"""
        source = temp_project_dir / "nonexistent.txt"
        target = temp_project_dir / "target.txt"
        
        result = _copy_file(source, target, force=False, file_description="test file")
        
        assert result is False
        assert not target.exists()
    
    def test_copy_file_target_exists_no_force(self, temp_project_dir):
        """Test file copy with existing target and no force"""
        source = temp_project_dir / "source.txt"
        target = temp_project_dir / "target.txt"
        
        source.write_text("new content")
        target.write_text("old content")
        
        result = _copy_file(source, target, force=False, file_description="test file")
        
        assert result is False
        assert target.read_text() == "old content"
    
    def test_copy_file_target_exists_with_force(self, temp_project_dir):
        """Test file copy with existing target and force"""
        source = temp_project_dir / "source.txt"
        target = temp_project_dir / "target.txt"
        
        source.write_text("new content")
        target.write_text("old content")
        
        result = _copy_file(source, target, force=True, file_description="test file")
        
        assert result is True
        assert target.read_text() == "new content"


class TestClaudeCommand:
    """Test claude command function"""
    
    def test_claude_command_success(self, temp_project_dir):
        """Test successful claude command"""
        args = argparse.Namespace(force=False)
        
        # Setup project structure
        src_dir = temp_project_dir / "src"
        src_dir.mkdir()
        addon_json = temp_project_dir / "addon.json"
        addon_json.write_text("{}")
        
        with patch('aadt.cli.validate_cwd', return_value=True):
            with patch('aadt.cli._copy_file', return_value=True) as mock_copy:
                claude(args)
                
                assert mock_copy.call_count == 2
    
    def test_claude_command_invalid_project(self):
        """Test claude command with invalid project"""
        args = argparse.Namespace(force=False)
        
        with patch('aadt.cli.validate_cwd', return_value=False):
            with pytest.raises(CLIError) as exc_info:
                claude(args)
            
            assert "Could not find 'src' or 'addon.json'" in str(exc_info.value)


class TestArgumentParser:
    """Test argument parser construction"""
    
    def test_construct_parser(self):
        """Test parser construction"""
        parser = construct_parser()
        
        assert isinstance(parser, argparse.ArgumentParser)
        
        # Test that all subcommands are present
        subparsers = parser._subparsers._actions[1]
        choices = subparsers.choices
        
        expected_commands = [
            "build", "ui", "manifest", "init", "clean", "link", "test", 
            "claude", "create_dist", "build_dist", "package_dist"
        ]
        
        for cmd in expected_commands:
            assert cmd in choices
    
    def test_parser_logging_options(self):
        """Test parser logging options"""
        parser = construct_parser()
        
        # Test verbose option
        args = parser.parse_args(["--verbose", "ui"])
        assert args.verbose is True
        assert args.quiet is False
        
        # Test quiet option
        args = parser.parse_args(["--quiet", "ui"])
        assert args.verbose is False
        assert args.quiet is True
    
    def test_parser_build_command(self):
        """Test parser build command"""
        parser = construct_parser()
        
        args = parser.parse_args(["build", "-d", "ankiweb", "v1.0.0"])
        assert args.dist == "ankiweb"
        assert args.version == "v1.0.0"
    
    def test_parser_init_command(self):
        """Test parser init command"""
        parser = construct_parser()
        
        args = parser.parse_args(["init", "test_project", "-y"])
        assert args.directory == "test_project"
        assert args.yes is True


class TestMainFunction:
    """Test main function"""
    
    def test_main_success(self):
        """Test successful main execution"""
        test_args = ["aadt", "clean"]
        
        with patch.object(sys, 'argv', test_args):
            with patch('aadt.cli.validate_cwd', return_value=True):
                with patch('aadt.cli.clean_repo') as mock_clean:
                    with patch('aadt.cli.logging'):
                        main()
                        
                        mock_clean.assert_called_once()
    
    def test_main_cli_error(self):
        """Test main with CLI error"""
        test_args = ["aadt", "build"]
        
        with patch.object(sys, 'argv', test_args):
            with patch('aadt.cli.validate_cwd', return_value=False):
                with patch('aadt.cli.logging') as mock_logging:
                    with pytest.raises(SystemExit) as exc_info:
                        main()
                    
                    assert exc_info.value.code == 1
                    mock_logging.error.assert_called()
    
    def test_main_keyboard_interrupt(self):
        """Test main with keyboard interrupt"""
        test_args = ["aadt", "clean"]
        
        with patch.object(sys, 'argv', test_args):
            with patch('aadt.cli.validate_cwd', return_value=True):
                with patch('aadt.cli.clean_repo', side_effect=KeyboardInterrupt()):
                    with patch('aadt.cli.logging') as mock_logging:
                        with pytest.raises(SystemExit) as exc_info:
                            main()
                        
                        assert exc_info.value.code == 1
                        mock_logging.info.assert_called_with("\nOperation cancelled by user.")
    
    def test_main_unexpected_error(self):
        """Test main with unexpected error"""
        test_args = ["aadt", "clean"]
        
        with patch.object(sys, 'argv', test_args):
            with patch('aadt.cli.validate_cwd', return_value=True):
                with patch('aadt.cli.clean_repo', side_effect=Exception("Unexpected error")):
                    with patch('aadt.cli.logging') as mock_logging:
                        with pytest.raises(SystemExit) as exc_info:
                            main()
                        
                        assert exc_info.value.code == 1
                        mock_logging.error.assert_called()
    
    def test_main_logging_configuration(self):
        """Test main logging configuration"""
        test_args = ["aadt", "--verbose", "clean"]
        
        with patch.object(sys, 'argv', test_args):
            with patch('aadt.cli.validate_cwd', return_value=True):
                with patch('aadt.cli.clean_repo'):
                    with patch('aadt.cli.logging.basicConfig') as mock_config:
                        with patch('aadt.cli.logging'):
                            main()
                            
                            mock_config.assert_called_once()
                            call_args = mock_config.call_args
                            assert call_args[1]['level'] == 10  # DEBUG level
    
    def test_main_skip_validation_for_init(self):
        """Test main skips validation for init command"""
        test_args = ["aadt", "init", "-y"]
        
        with patch.object(sys, 'argv', test_args):
            with patch('aadt.cli.validate_cwd', return_value=False) as mock_validate:
                with patch('aadt.cli.ProjectInitializer') as mock_initializer:
                    with patch('aadt.cli.logging'):
                        main()
                        
                        # validate_cwd should not be called for init command
                        mock_validate.assert_not_called()
                        mock_initializer.assert_called_once()