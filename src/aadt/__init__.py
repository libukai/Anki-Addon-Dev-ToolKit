"""
Anki Addon Dev ToolKit (AADT)

A modern build system for Anki add-ons that supports Qt6,
automated dependency management, and streamlined development workflows.

This package provides tools for:
- Initializing new add-on projects with modern Python standards
- Building and packaging add-ons for AnkiWeb distribution
- Compiling Qt UI files and managing resources
- Managing development environments with uv

Public API:
    - CLI commands: init, build, ui, test, link, manifest, clean, claude
    - Core classes: AddonBuilder, Config, ProjectInitializer, UIBuilder
    - Utilities: clean_repo, copy_recursively, purge

Example usage:
    >>> from aadt import AddonBuilder, Config
    >>> config = Config()
    >>> builder = AddonBuilder()
    >>> builder.build(disttype="local")

For CLI usage, see: aadt --help
"""

import tomllib
from email.message import Message
from importlib import metadata as pkg_metadata
from pathlib import Path
from typing import Any, cast


def _get_project_metadata() -> dict[str, Any]:
    """
    Read project metadata from installed package or pyproject.toml.

    Priority:
    1. Try to read from installed package metadata (for PyPI installations)
    2. Fall back to pyproject.toml (for development)
    3. Use hardcoded fallback values
    """
    try:
        # First try to read from installed package metadata
        # PackageMetadata is actually a Message subclass with .get() method
        package_metadata = cast(Message, pkg_metadata.metadata("aadt"))

        # Extract author info
        author_name = "Libukai"
        if package_metadata.get("Author"):
            author_name = package_metadata["Author"]
        elif package_metadata.get("Author-Email"):
            # Parse "Name <email>" format
            author_email = package_metadata["Author-Email"]
            if "<" in author_email:
                author_name = author_email.split("<")[0].strip()

        return {
            "name": package_metadata.get("Name", "aadt"),
            "version": package_metadata.get("Version", "1.0.0"),
            "description": package_metadata.get("Summary", "Anki Addon Dev ToolKit"),
            "authors": [{"name": author_name}],
            "urls": {"Homepage": package_metadata.get("Home-Page", "https://github.com/libukai/aadt")},
        }
    except (pkg_metadata.PackageNotFoundError, Exception):
        # Fall back to reading pyproject.toml (development mode)
        try:
            pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
            project = data.get("project")
            if isinstance(project, dict):
                return project
        except (FileNotFoundError, tomllib.TOMLDecodeError):
            pass

        # Final fallback values
        return {
            "name": "aadt",
            "version": "1.0.0",
            "description": "Anki Addon Dev ToolKit",
            "authors": [{"name": "Libukai"}],
            "urls": {"Homepage": "https://github.com/libukai/aadt"},
        }


# Project metadata - dynamically loaded from pyproject.toml
_metadata = _get_project_metadata()

__version__ = _metadata.get("version", "1.0.0")
__author__ = _metadata.get("authors", [{}])[0].get("name", "Libukai")
__title__ = _metadata.get("description", "Anki Addon Dev ToolKit")
__homepage__ = _metadata.get("urls", {}).get("Homepage", "https://github.com/libukai/aadt")

COPYRIGHT_MSG = f"""\
{__title__} v{__version__}

Copyright (C) 2025  {__author__}  <{__homepage__}>

"""

# Global constants and paths
PATH_PROJECT_ROOT = Path.cwd()  # Project root directory (current working directory)
PATH_DIST = PATH_PROJECT_ROOT / "dist" / "build"  # Build output directory
PATH_PACKAGE = Path(__file__).resolve().parent  # AADT package directory

# Supported distribution types
DIST_TYPES = ["local", "ankiweb"]

# Public API exports
__all__ = [
    # Constants
    "COPYRIGHT_MSG",
    "DIST_TYPES",
    "PATH_DIST",
    "PATH_PACKAGE",
    "PATH_PROJECT_ROOT",
    # Core classes
    "AddonBuilder",
    # Exceptions
    "BuildError",
    "CLIError",
    "Config",
    "ManifestUtils",
    "ProjectInitializationError",
    "ProjectInitializer",
    "UIBuilder",
    "VersionError",
    "VersionManager",
    "__author__",
    "__homepage__",
    "__title__",
    # Metadata
    "__version__",
    # Utilities
    "clean_repo",
    "copy_recursively",
    "purge",
]
