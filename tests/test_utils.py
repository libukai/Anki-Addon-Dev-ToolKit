"""
Tests for aadt.utils module
"""

import os
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from aadt.utils import copy_recursively, purge, call_shell
from tests.util import list_files


class TestCopyRecursively:
    """Test copy_recursively function"""
    
    def test_copy_file(self, temp_project_dir):
        """Test copying a single file"""
        source_file = temp_project_dir / "source.txt"
        target_file = temp_project_dir / "target.txt"
        
        source_file.write_text("test content")
        
        copy_recursively(source_file, target_file)
        
        assert target_file.exists()
        assert target_file.read_text() == "test content"
    
    def test_copy_directory(self, temp_project_dir):
        """Test copying a directory recursively"""
        source_dir = temp_project_dir / "source"
        target_dir = temp_project_dir / "target"
        
        source_dir.mkdir()
        (source_dir / "file1.txt").write_text("content1")
        (source_dir / "subdir").mkdir()
        (source_dir / "subdir" / "file2.txt").write_text("content2")
        
        copy_recursively(source_dir, target_dir)
        
        assert target_dir.exists()
        assert (target_dir / "file1.txt").exists()
        assert (target_dir / "file1.txt").read_text() == "content1"
        assert (target_dir / "subdir").exists()
        assert (target_dir / "subdir" / "file2.txt").exists()
        assert (target_dir / "subdir" / "file2.txt").read_text() == "content2"
    
    def test_copy_to_existing_directory(self, temp_project_dir):
        """Test copying to an existing directory"""
        source_file = temp_project_dir / "source.txt"
        target_dir = temp_project_dir / "target"
        
        source_file.write_text("test content")
        target_dir.mkdir()
        
        copy_recursively(source_file, target_dir)
        
        assert (target_dir / "source.txt").exists()
        assert (target_dir / "source.txt").read_text() == "test content"
    
    def test_copy_nonexistent_source(self, temp_project_dir):
        """Test copying nonexistent source"""
        source_file = temp_project_dir / "nonexistent.txt"
        target_file = temp_project_dir / "target.txt"
        
        with pytest.raises((OSError, FileNotFoundError)):
            copy_recursively(source_file, target_file)
    
    def test_copy_with_overwrite(self, temp_project_dir):
        """Test copying with overwrite"""
        source_file = temp_project_dir / "source.txt"
        target_file = temp_project_dir / "target.txt"
        
        source_file.write_text("new content")
        target_file.write_text("old content")
        
        copy_recursively(source_file, target_file)
        
        assert target_file.read_text() == "new content"


class TestPurge:
    """Test purge function"""
    
    def test_purge_files_non_recursive(self, temp_project_dir):
        """Test purging files non-recursively"""
        # Create test files
        (temp_project_dir / "test.pyc").write_text("compiled")
        (temp_project_dir / "test.py").write_text("source")
        (temp_project_dir / "other.txt").write_text("text")
        
        subdir = temp_project_dir / "subdir"
        subdir.mkdir()
        (subdir / "nested.pyc").write_text("nested compiled")
        
        patterns = ["*.pyc"]
        
        with patch('os.getcwd', return_value=str(temp_project_dir)):
            purge(".", patterns, recursive=False)
        
        # Only top-level .pyc should be removed
        assert not (temp_project_dir / "test.pyc").exists()
        assert (temp_project_dir / "test.py").exists()
        assert (temp_project_dir / "other.txt").exists()
        assert (subdir / "nested.pyc").exists()  # Should not be removed
    
    def test_purge_files_recursive(self, temp_project_dir):
        """Test purging files recursively"""
        # Create test files
        (temp_project_dir / "test.pyc").write_text("compiled")
        (temp_project_dir / "test.py").write_text("source")
        
        subdir = temp_project_dir / "subdir"
        subdir.mkdir()
        (subdir / "nested.pyc").write_text("nested compiled")
        (subdir / "nested.py").write_text("nested source")
        
        patterns = ["*.pyc"]
        
        with patch('os.getcwd', return_value=str(temp_project_dir)):
            purge(".", patterns, recursive=True)
        
        # All .pyc files should be removed
        assert not (temp_project_dir / "test.pyc").exists()
        assert (temp_project_dir / "test.py").exists()
        assert not (subdir / "nested.pyc").exists()
        assert (subdir / "nested.py").exists()
    
    def test_purge_directories(self, temp_project_dir):
        """Test purging directories"""
        # Create test directories
        cache_dir = temp_project_dir / "__pycache__"
        cache_dir.mkdir()
        (cache_dir / "test.pyc").write_text("compiled")
        
        other_dir = temp_project_dir / "other"
        other_dir.mkdir()
        
        patterns = ["__pycache__"]
        
        with patch('os.getcwd', return_value=str(temp_project_dir)):
            purge(".", patterns, recursive=False)
        
        assert not cache_dir.exists()
        assert other_dir.exists()
    
    def test_purge_multiple_patterns(self, temp_project_dir):
        """Test purging with multiple patterns"""
        # Create test files
        (temp_project_dir / "test.pyc").write_text("compiled")
        (temp_project_dir / "test.pyo").write_text("optimized")
        (temp_project_dir / "test.py").write_text("source")
        (temp_project_dir / "test.txt").write_text("text")
        
        patterns = ["*.pyc", "*.pyo"]
        
        with patch('os.getcwd', return_value=str(temp_project_dir)):
            purge(".", patterns, recursive=False)
        
        assert not (temp_project_dir / "test.pyc").exists()
        assert not (temp_project_dir / "test.pyo").exists()
        assert (temp_project_dir / "test.py").exists()
        assert (temp_project_dir / "test.txt").exists()
    
    def test_purge_no_matches(self, temp_project_dir):
        """Test purging with no matching files"""
        (temp_project_dir / "test.py").write_text("source")
        (temp_project_dir / "test.txt").write_text("text")
        
        patterns = ["*.pyc"]
        
        with patch('os.getcwd', return_value=str(temp_project_dir)):
            # Should not raise any errors
            purge(".", patterns, recursive=False)
        
        assert (temp_project_dir / "test.py").exists()
        assert (temp_project_dir / "test.txt").exists()
    
    def test_purge_permission_error(self, temp_project_dir):
        """Test purging with permission error"""
        test_file = temp_project_dir / "test.pyc"
        test_file.write_text("compiled")
        
        patterns = ["*.pyc"]
        
        with patch('os.getcwd', return_value=str(temp_project_dir)):
            with patch('os.remove', side_effect=PermissionError("Permission denied")):
                # Should not raise error, just continue
                purge(".", patterns, recursive=False)


class TestCallShell:
    """Test call_shell function"""
    
    def test_call_shell_success(self):
        """Test successful shell command"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "success output"
            
            result = call_shell(["echo", "hello"])
            
            assert result == "success output"
            mock_run.assert_called_once_with(
                ["echo", "hello"],
                capture_output=True,
                text=True,
                check=True
            )
    
    def test_call_shell_failure(self):
        """Test failed shell command"""
        with patch('subprocess.run') as mock_run:
            from subprocess import CalledProcessError
            mock_run.side_effect = CalledProcessError(1, ["false"], stderr="error output")
            
            result = call_shell(["false"], error_exit=False)
            
            assert result == ""
    
    def test_call_shell_with_cwd(self, temp_project_dir):
        """Test shell command with working directory"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "/test/path"
            
            result = call_shell(["pwd"], cwd=str(temp_project_dir))
            
            assert result == "/test/path"
            mock_run.assert_called_once_with(
                ["pwd"],
                capture_output=True,
                text=True,
                check=True,
                cwd=str(temp_project_dir)
            )
    
    def test_call_shell_exception(self):
        """Test shell command with exception"""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError("Command not found")
            
            result = call_shell(["invalid_command"], error_exit=False)
            
            assert result == ""  # Should return empty string on exception


class TestListFiles:
    """Test list_files function"""
    
    def test_list_files_simple(self, temp_project_dir):
        """Test listing files in simple directory structure"""
        # Create test structure
        (temp_project_dir / "file1.txt").write_text("content1")
        (temp_project_dir / "file2.py").write_text("content2")
        
        subdir = temp_project_dir / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("content3")
        
        result = list_files(temp_project_dir)
        
        # Check that result contains expected structure
        lines = result.strip().split('\n')
        assert any("file1.txt" in line for line in lines)
        assert any("file2.py" in line for line in lines)
        assert any("subdir/" in line for line in lines)
        assert any("file3.txt" in line for line in lines)
    
    def test_list_files_empty_directory(self, temp_project_dir):
        """Test listing files in empty directory"""
        result = list_files(temp_project_dir)
        
        # Should have root directory entry
        lines = result.strip().split('\n')
        assert len(lines) == 1
        assert temp_project_dir.name + "/" in lines[0]
    
    def test_list_files_nested_structure(self, temp_project_dir):
        """Test listing files with nested directory structure"""
        # Create nested structure
        level1 = temp_project_dir / "level1"
        level1.mkdir()
        (level1 / "file1.txt").write_text("content1")
        
        level2 = level1 / "level2"
        level2.mkdir()
        (level2 / "file2.txt").write_text("content2")
        
        level3 = level2 / "level3"
        level3.mkdir()
        (level3 / "file3.txt").write_text("content3")
        
        result = list_files(temp_project_dir)
        
        lines = result.strip().split('\n')
        
        # Check indentation levels
        assert any("level1/" in line and not line.startswith(' ') for line in lines)
        assert any("file1.txt" in line and line.startswith('    ') for line in lines)
        assert any("level2/" in line and line.startswith('    ') for line in lines)
        assert any("file2.txt" in line and line.startswith('        ') for line in lines)
        assert any("level3/" in line and line.startswith('        ') for line in lines)
        assert any("file3.txt" in line and line.startswith('            ') for line in lines)
    
    def test_list_files_nonexistent_path(self):
        """Test listing files with nonexistent path"""
        nonexistent_path = Path("/nonexistent/path")
        
        # Should handle gracefully, likely returning empty or error
        # The exact behavior depends on implementation
        try:
            result = list_files(nonexistent_path)
            # If it doesn't raise an exception, result should be reasonable
            assert isinstance(result, str)
        except (OSError, FileNotFoundError):
            # This is also acceptable behavior
            pass


class TestUtilsIntegration:
    """Integration tests for utils functions"""
    
    def test_copy_and_purge_workflow(self, temp_project_dir):
        """Test workflow combining copy and purge operations"""
        # Setup source structure
        source_dir = temp_project_dir / "source"
        source_dir.mkdir()
        
        (source_dir / "script.py").write_text("print('hello')")
        (source_dir / "script.pyc").write_text("compiled")
        
        subdir = source_dir / "subdir"
        subdir.mkdir()
        (subdir / "module.py").write_text("# module")
        (subdir / "module.pyc").write_text("compiled module")
        
        # Copy to target
        target_dir = temp_project_dir / "target"
        copy_recursively(source_dir, target_dir)
        
        # Verify copy
        assert (target_dir / "script.py").exists()
        assert (target_dir / "script.pyc").exists()
        assert (target_dir / "subdir" / "module.py").exists()
        assert (target_dir / "subdir" / "module.pyc").exists()
        
        # Purge compiled files
        # Use absolute path instead of current directory to avoid accidents
        purge(str(target_dir), ["*.pyc"], recursive=True)
        
        # Verify purge
        assert (target_dir / "script.py").exists()
        assert not (target_dir / "script.pyc").exists()
        assert (target_dir / "subdir" / "module.py").exists()
        assert not (target_dir / "subdir" / "module.pyc").exists()
    
    def test_full_project_copy_workflow(self, temp_project_dir):
        """Test full project copy workflow with realistic structure"""
        # Create realistic project structure
        project_dir = temp_project_dir / "my_addon"
        project_dir.mkdir()
        
        # Source code
        src_dir = project_dir / "src" / "addon"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("# addon init")
        (src_dir / "main.py").write_text("# main module")
        (src_dir / "utils.py").write_text("# utilities")
        
        # Compiled files
        (src_dir / "__pycache__").mkdir()
        (src_dir / "__pycache__" / "main.cpython-39.pyc").write_text("compiled")
        
        # UI files
        ui_dir = project_dir / "ui"
        ui_dir.mkdir()
        (ui_dir / "dialog.ui").write_text("<ui></ui>")
        
        # Resources
        res_dir = project_dir / "resources"
        res_dir.mkdir()
        (res_dir / "icon.png").write_text("fake png")
        
        # Development files
        (project_dir / ".git").mkdir()
        (project_dir / "addon.json").write_text("{}")
        (project_dir / "README.md").write_text("# Readme")
        
        # Copy to build directory
        build_dir = temp_project_dir / "build"
        copy_recursively(project_dir, build_dir)
        
        # Clean development artifacts
        # Use absolute path instead of current directory to avoid accidents
        purge(str(build_dir), ["__pycache__", ".git", "*.pyc"], recursive=True)
        
        # Verify structure
        assert (build_dir / "src" / "addon" / "main.py").exists()
        assert (build_dir / "ui" / "dialog.ui").exists()
        assert (build_dir / "resources" / "icon.png").exists()
        assert (build_dir / "addon.json").exists()
        assert (build_dir / "README.md").exists()
        
        # Verify cleanup
        assert not (build_dir / ".git").exists()
        assert not (build_dir / "src" / "addon" / "__pycache__").exists()
    
    def test_error_handling_workflow(self, temp_project_dir):
        """Test error handling in combined workflows"""
        # Setup problematic structure
        source_dir = temp_project_dir / "source"
        source_dir.mkdir()
        (source_dir / "file.txt").write_text("content")
        
        # Test copy with permission error
        target_dir = temp_project_dir / "target"
        
        with patch('shutil.copy2', side_effect=PermissionError("Access denied")):
            with pytest.raises(PermissionError):
                copy_recursively(source_dir / "file.txt", target_dir / "file.txt")
        
        # Test purge with permission error (should not raise)
        (target_dir / "file.pyc").write_text("compiled")
        target_dir.mkdir(exist_ok=True)
        
        with patch('os.getcwd', return_value=str(target_dir)):
            with patch('os.remove', side_effect=PermissionError("Access denied")):
                # Should not raise exception
                purge(".", ["*.pyc"], recursive=False)