"""
Tests for aadt.git module
"""

import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from aadt.git import VersionManager


class TestVersionManager:
    """Test VersionManager class"""
    
    def test_init(self, temp_project_dir):
        """Test VersionManager initialization"""
        exclude_patterns = ["*.pyc", "__pycache__"]
        
        vm = VersionManager(temp_project_dir, exclude_patterns)
        
        assert vm.project_root == temp_project_dir
        assert vm.exclude_patterns == exclude_patterns
    
    def test_parse_version_explicit_version(self, temp_project_dir):
        """Test parse_version with explicit version"""
        vm = VersionManager(temp_project_dir, [])
        
        result = vm.parse_version("1.2.3")
        
        assert result == "1.2.3"
    
    def test_parse_version_dev_keyword(self, temp_project_dir):
        """Test parse_version with 'dev' keyword"""
        vm = VersionManager(temp_project_dir, [])
        
        result = vm.parse_version("dev")
        
        assert result == "dev"
    
    def test_parse_version_current_keyword(self, temp_project_dir):
        """Test parse_version with 'current' keyword"""
        vm = VersionManager(temp_project_dir, [])
        
        with patch.object(vm, '_get_current_commit', return_value="abc123"):
            result = vm.parse_version("current")
            
            assert result == "abc123"
    
    def test_parse_version_release_keyword(self, temp_project_dir):
        """Test parse_version with 'release' keyword"""
        vm = VersionManager(temp_project_dir, [])
        
        with patch.object(vm, '_get_latest_tag', return_value="v1.0.0"):
            result = vm.parse_version("release")
            
            assert result == "v1.0.0"
    
    def test_parse_version_none_fallback(self, temp_project_dir):
        """Test parse_version with None falls back to latest tag"""
        vm = VersionManager(temp_project_dir, [])
        
        with patch.object(vm, '_get_latest_tag', return_value="v1.0.0"):
            result = vm.parse_version(None)
            
            assert result == "v1.0.0"
    
    def test_parse_version_git_ref(self, temp_project_dir):
        """Test parse_version with git reference"""
        vm = VersionManager(temp_project_dir, [])
        
        with patch.object(vm, '_resolve_git_ref', return_value="def456"):
            result = vm.parse_version("feature/branch")
            
            assert result == "def456"
    
    def test_parse_version_fallback_to_dev(self, temp_project_dir):
        """Test parse_version fallback to dev when all else fails"""
        vm = VersionManager(temp_project_dir, [])
        
        with patch.object(vm, '_get_latest_tag', return_value=None):
            with patch.object(vm, '_resolve_git_ref', return_value=None):
                result = vm.parse_version("nonexistent")
                
                assert result == "dev"
    
    def test_get_current_commit(self, temp_project_dir):
        """Test _get_current_commit method"""
        vm = VersionManager(temp_project_dir, [])
        
        with patch('aadt.git.subprocess.run') as mock_run:
            mock_run.return_value.stdout = "abc123def456"
            mock_run.return_value.returncode = 0
            
            result = vm._get_current_commit()
            
            assert result == "abc123def456"
            mock_run.assert_called_once_with(
                ["git", "rev-parse", "HEAD"],
                cwd=temp_project_dir,
                capture_output=True,
                text=True,
                check=True
            )
    
    def test_get_current_commit_error(self, temp_project_dir):
        """Test _get_current_commit with error"""
        vm = VersionManager(temp_project_dir, [])
        
        with patch('aadt.git.subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "git")
            
            result = vm._get_current_commit()
            
            assert result is None
    
    def test_get_latest_tag(self, temp_project_dir):
        """Test _get_latest_tag method"""
        vm = VersionManager(temp_project_dir, [])
        
        with patch('aadt.git.subprocess.run') as mock_run:
            mock_run.return_value.stdout = "v1.2.3"
            mock_run.return_value.returncode = 0
            
            result = vm._get_latest_tag()
            
            assert result == "v1.2.3"
            mock_run.assert_called_once_with(
                ["git", "describe", "--tags", "--abbrev=0"],
                cwd=temp_project_dir,
                capture_output=True,
                text=True,
                check=True
            )
    
    def test_get_latest_tag_error(self, temp_project_dir):
        """Test _get_latest_tag with error"""
        vm = VersionManager(temp_project_dir, [])
        
        with patch('aadt.git.subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "git")
            
            result = vm._get_latest_tag()
            
            assert result is None
    
    def test_resolve_git_ref(self, temp_project_dir):
        """Test _resolve_git_ref method"""
        vm = VersionManager(temp_project_dir, [])
        
        with patch('aadt.git.subprocess.run') as mock_run:
            mock_run.return_value.stdout = "abc123def456"
            mock_run.return_value.returncode = 0
            
            result = vm._resolve_git_ref("feature/branch")
            
            assert result == "abc123def456"
            mock_run.assert_called_once_with(
                ["git", "rev-parse", "feature/branch"],
                cwd=temp_project_dir,
                capture_output=True,
                text=True,
                check=True
            )
    
    def test_resolve_git_ref_error(self, temp_project_dir):
        """Test _resolve_git_ref with error"""
        vm = VersionManager(temp_project_dir, [])
        
        with patch('aadt.git.subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "git")
            
            result = vm._resolve_git_ref("nonexistent")
            
            assert result is None
    
    def test_modtime(self, temp_project_dir):
        """Test modtime method"""
        vm = VersionManager(temp_project_dir, [])
        
        with patch('aadt.git.subprocess.run') as mock_run:
            mock_run.return_value.stdout = "1234567890"
            mock_run.return_value.returncode = 0
            
            result = vm.modtime("v1.0.0")
            
            assert result == 1234567890
            mock_run.assert_called_once_with(
                ["git", "log", "-1", "--format=%ct", "v1.0.0"],
                cwd=temp_project_dir,
                capture_output=True,
                text=True,
                check=True
            )
    
    def test_modtime_dev_version(self, temp_project_dir):
        """Test modtime with dev version"""
        vm = VersionManager(temp_project_dir, [])
        
        import time
        with patch('time.time', return_value=1234567890.5):
            result = vm.modtime("dev")
            
            assert result == 1234567890
    
    def test_modtime_error(self, temp_project_dir):
        """Test modtime with git error"""
        vm = VersionManager(temp_project_dir, [])
        
        with patch('aadt.git.subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "git")
            
            import time
            with patch('time.time', return_value=1234567890.5):
                result = vm.modtime("v1.0.0")
                
                assert result == 1234567890
    
    def test_archive(self, temp_project_dir):
        """Test archive method"""
        vm = VersionManager(temp_project_dir, [])
        
        target_dir = temp_project_dir / "archive"
        target_dir.mkdir()
        
        with patch('aadt.git.subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            
            vm.archive("v1.0.0", target_dir)
            
            expected_cmd = [
                "git", "archive", "--format=tar",
                "--prefix=", "v1.0.0"
            ]
            
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            assert call_args[0][0][:5] == expected_cmd[:5]  # Check first 5 elements
            assert call_args[1]["cwd"] == temp_project_dir
    
    def test_archive_dev_version(self, temp_project_dir):
        """Test archive with dev version"""
        vm = VersionManager(temp_project_dir, [])
        
        target_dir = temp_project_dir / "archive"
        target_dir.mkdir()
        
        # Create some test files
        test_file = temp_project_dir / "test.py"
        test_file.write_text("# test")
        
        with patch('aadt.git.subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            
            vm.archive("dev", target_dir)
            
            # For dev version, should use copy instead of git archive
            mock_run.assert_not_called()
    
    def test_archive_with_excludes(self, temp_project_dir):
        """Test archive with exclude patterns"""
        exclude_patterns = ["*.pyc", "__pycache__", "node_modules"]
        vm = VersionManager(temp_project_dir, exclude_patterns)
        
        target_dir = temp_project_dir / "archive"
        target_dir.mkdir()
        
        with patch('aadt.git.subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            
            vm.archive("v1.0.0", target_dir)
            
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            cmd = call_args[0][0]
            
            # Should contain exclude patterns
            for pattern in exclude_patterns:
                assert f"--exclude={pattern}" in cmd
    
    def test_archive_error(self, temp_project_dir):
        """Test archive with git error"""
        vm = VersionManager(temp_project_dir, [])
        
        target_dir = temp_project_dir / "archive"
        target_dir.mkdir()
        
        with patch('aadt.git.subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "git")
            
            with pytest.raises(subprocess.CalledProcessError):
                vm.archive("v1.0.0", target_dir)


class TestVersionManagerIntegration:
    """Integration tests for VersionManager"""
    
    def test_full_workflow(self, temp_project_dir):
        """Test complete version manager workflow"""
        exclude_patterns = ["*.pyc", "__pycache__"]
        vm = VersionManager(temp_project_dir, exclude_patterns)
        
        # Setup git repository
        with patch('aadt.git.subprocess.run') as mock_run:
            # Mock git commands
            def mock_git_command(cmd, **kwargs):
                if cmd[1] == "describe":
                    result = MagicMock()
                    result.stdout = "v1.0.0"
                    result.returncode = 0
                    return result
                elif cmd[1] == "log":
                    result = MagicMock()
                    result.stdout = "1234567890"
                    result.returncode = 0
                    return result
                elif cmd[1] == "archive":
                    result = MagicMock()
                    result.returncode = 0
                    return result
                else:
                    result = MagicMock()
                    result.returncode = 0
                    return result
            
            mock_run.side_effect = mock_git_command
            
            # Test version parsing
            version = vm.parse_version("release")
            assert version == "v1.0.0"
            
            # Test modtime
            modtime = vm.modtime(version)
            assert modtime == 1234567890
            
            # Test archive
            target_dir = temp_project_dir / "archive"
            target_dir.mkdir()
            vm.archive(version, target_dir)
            
            # Verify git commands were called
            assert mock_run.call_count >= 3
    
    def test_fallback_behavior(self, temp_project_dir):
        """Test fallback behavior when git operations fail"""
        vm = VersionManager(temp_project_dir, [])
        
        with patch('aadt.git.subprocess.run') as mock_run:
            # All git operations fail
            mock_run.side_effect = subprocess.CalledProcessError(1, "git")
            
            # Version parsing should fall back to 'dev'
            version = vm.parse_version("release")
            assert version == "dev"
            
            # modtime should fall back to current time
            import time
            with patch('time.time', return_value=1234567890.5):
                modtime = vm.modtime(version)
                assert modtime == 1234567890
    
    def test_edge_cases(self, temp_project_dir):
        """Test edge cases and error handling"""
        vm = VersionManager(temp_project_dir, [])
        
        # Test empty version string
        result = vm.parse_version("")
        assert result == "dev"
        
        # Test whitespace-only version
        result = vm.parse_version("   ")
        assert result == "dev"
        
        # Test None version
        with patch.object(vm, '_get_latest_tag', return_value=None):
            result = vm.parse_version(None)
            assert result == "dev"