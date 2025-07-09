#!/usr/bin/env python

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
# This program is subject to certain additional terms pursuant to
# Section 7 of the GNU Affero General Public License.  You should have
# received a copy of these additional terms immediately following the
# terms and conditions of the GNU Affero General Public License that
# accompanied this program.
#
# If not, please request a copy through one of the means of contact
# listed here: <https://glutanimate.com/contact/>.
#
# Any modifications to this file must keep this entire header intact.

import argparse
import logging
import sys
from collections.abc import Callable
from typing import Any

from aadt import COPYRIGHT_MSG, DIST_TYPES, PATH_PACKAGE, PATH_PROJECT_ROOT
from aadt.builder import AddonBuilder, VersionError, clean_repo
from aadt.config import PATH_CONFIG, Config
from aadt.git import VersionManager
from aadt.init import ProjectInitializationError, ProjectInitializer
from aadt.manifest import ManifestUtils
from aadt.ui import UIBuilder


class CLIError(Exception):
    """Exception raised for CLI-specific errors"""

    pass


# Checks
##############################################################################


def validate_cwd() -> bool:
    """Checks if CWD is a valid project root."""
    return (PATH_PROJECT_ROOT / "src").exists() and PATH_CONFIG.exists()


# Helpers
##############################################################################


def _get_dist_list(dist_arg: str) -> list[str]:
    """Get list of distributions to build based on argument"""
    return [dist_arg] if dist_arg != "all" else DIST_TYPES


def _execute_multi_dist_task(
    task_name: str,
    dists: list[str],
    task_func: Callable[..., Any],
    version: str | None = None,
    **kwargs: Any,
) -> None:
    """Execute a task across multiple distribution types"""
    try:
        builder = AddonBuilder(version=version)
    except VersionError as e:
        raise CLIError(f"Failed to initialize builder: {e}") from e

    total = len(dists)
    for cnt, dist in enumerate(dists, 1):
        logging.info("\n=== %s task %s/%s ===", task_name.title(), cnt, total)
        task_func(builder, dist, **kwargs)


# Entry points
##############################################################################


def build(args: argparse.Namespace) -> None:
    """Build and package add-on for distribution"""
    _execute_multi_dist_task(
        task_name="build",
        dists=_get_dist_list(args.dist),
        task_func=lambda builder, dist, **kwargs: builder.build(disttype=dist, **kwargs),
        version=args.version,
    )


def ui(args: argparse.Namespace) -> None:
    """Compile add-on user interface files"""
    builder = UIBuilder(dist=PATH_PROJECT_ROOT, config=Config())

    logging.info("\n=== Building Qt6 UI ===\n")
    should_create_shim = builder.build()

    if should_create_shim:
        logging.info("\n=== Writing Qt compatibility shim ===")
        builder.create_qt_shim()

    logging.info("Done.")


def manifest(args: argparse.Namespace) -> None:
    """Generate manifest file from add-on properties"""
    try:
        dists = DIST_TYPES if args.dist == "all" else [args.dist]

        config = Config()
        addon_config = config.as_dataclass()
        exclude_patterns = addon_config.build_config.archive_exclude_patterns

        version_manager = VersionManager(PATH_PROJECT_ROOT, exclude_patterns)
        version = version_manager.parse_version(vstring=args.version)
        target_dir = PATH_PROJECT_ROOT / "src" / addon_config.module_name

        for dist_type in dists:
            logging.info(f"Generating manifest for {dist_type} distribution")
            mod_time = version_manager.modtime(version)
            ManifestUtils.generate_and_write_manifest(
                addon_properties=config,
                version=version,
                dist_type=dist_type,  # type: ignore
                target_dir=target_dir,
                mod_time=mod_time,
            )
    except Exception as e:
        raise CLIError(f"Failed to generate manifest: {e}") from e


def create_dist(args: argparse.Namespace) -> None:
    """Prepare source tree distribution for building"""
    try:
        builder = AddonBuilder(version=args.version)
        builder.create_dist()
    except VersionError as e:
        raise CLIError(f"Failed to create distribution: {e}") from e


def build_dist(args: argparse.Namespace) -> None:
    """Build add-on files from prepared source tree"""
    _execute_multi_dist_task(
        task_name="build_dist",
        dists=_get_dist_list(args.dist),
        task_func=lambda builder, dist, **kwargs: builder.build_dist(disttype=dist, **kwargs),
        version=args.version,
    )


def package_dist(args: argparse.Namespace) -> None:
    """Package pre-built distribution into distributable package"""
    _execute_multi_dist_task(
        task_name="package_dist",
        dists=_get_dist_list(args.dist),
        task_func=lambda builder, dist: builder.package_dist(disttype=dist),
        version=args.version,
    )


def clean(args: argparse.Namespace) -> None:
    """Clean leftover build files"""
    clean_repo()


def init(args: argparse.Namespace) -> None:
    """Initialize a new add-on project"""
    from pathlib import Path

    target_dir = Path(args.directory).resolve() if args.directory else Path.cwd()

    initializer = ProjectInitializer(target_dir)
    try:
        initializer.init_project(interactive=not args.yes)
    except ProjectInitializationError as e:
        raise CLIError(f"Failed to initialize project: {e}") from e


def link(args: argparse.Namespace) -> None:
    """Link add-on to Anki's addon directory for development"""
    from aadt.run import AddonLinker

    try:
        config = Config(PATH_CONFIG)
        addon_config = config.as_dataclass()

        linker = AddonLinker(addon_config)

        if args.unlink:
            success = linker.unlink_addon()
            if success:
                print("✅ Add-on unlinked successfully!")
            else:
                raise CLIError("Failed to unlink add-on")
        else:
            success = linker.link_addon()
            if success:
                print("✅ Add-on linked successfully!")
                print("🎯 You can now test changes directly in Anki")
            else:
                raise CLIError("Failed to link add-on")

    except Exception as e:
        raise CLIError(f"Link operation failed: {e}") from e


def test(args: argparse.Namespace) -> None:
    """Link add-on and launch Anki for testing"""
    from aadt.run import AddonLinker

    try:
        print("🚀 Setting up add-on development environment...")

        # Set up linking
        config = Config(PATH_CONFIG)
        addon_config = config.as_dataclass()
        linker = AddonLinker(addon_config)

        success = linker.link_addon()
        if not success:
            raise CLIError("Failed to link add-on for testing")

        print("🎯 Launching Anki for testing...")

        # Import and launch Anki
        try:
            import aqt

            aqt.run()
        except ImportError as e:
            raise CLIError("Anki (aqt) not found. Make sure it's installed: uv sync --group dev") from e
        except Exception as e:
            raise CLIError(f"Failed to launch Anki: {e}") from e

    except Exception as e:
        raise CLIError(f"Test setup failed: {e}") from e


def claude(args: argparse.Namespace) -> None:
    """Generate Claude AI assistant memory file and ANKI reference for better development assistance"""

    try:
        # Check if we're in a valid add-on project
        if not validate_cwd():
            raise CLIError("Could not find 'src' or 'addon.json'. Please run this from the add-on project root.")

        templates_dir = PATH_PACKAGE / "templates"
        files_created = []

        # Copy CLAUDE.md file
        claude_success = _copy_file(
            templates_dir / "CLAUDE.md",
            PATH_PROJECT_ROOT / "CLAUDE.md",
            args.force,
            "CLAUDE.md",
        )
        if claude_success:
            files_created.append("CLAUDE.md")

        # Copy ANKI.md file
        anki_success = _copy_file(
            templates_dir / "ANKI.md",
            PATH_PROJECT_ROOT / "ANKI.md",
            args.force,
            "ANKI.md",
        )
        if anki_success:
            files_created.append("ANKI.md")

        # Show summary
        if files_created:
            print("✅ Successfully generated:")
            for file_name in files_created:
                print(f"   📄 {file_name}")
            print()
            print("💡 These files will help Claude AI better understand your project:")
            print("   🤖 CLAUDE.md - Claude AI assistant memory and development guidelines")
            print("   📚 ANKI.md - Complete Anki 25.06+ API reference and best practices")
            print("🔍 Consider adding these to your repository for better AI assistance")
        else:
            print("ℹ️  No files were created (they may already exist - use --force to overwrite)")

    except Exception as e:
        raise CLIError(f"Claude command failed: {e}") from e


def _copy_file(source_path, output_path, force, file_description):
    """Helper function to copy a file"""
    try:
        # Check if source exists
        if not source_path.exists():
            print(f"⚠️  Source file not found: {source_path}")
            return False

        # Check if output file already exists
        if output_path.exists() and not force:
            print(f"ℹ️  {file_description} already exists, skipping (use --force to overwrite)")  # noqa: RUF001
            return False

        # Read and copy file
        try:
            with source_path.open("r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError as e:
            print(f"❌ Failed to read source file {source_path}: {e}")
            return False

        # Write file
        try:
            output_path.write_text(content, encoding="utf-8")
            return True
        except OSError as e:
            print(f"❌ Failed to write {file_description}: {e}")
            return False

    except Exception as e:
        print(f"❌ Error copying {file_description}: {e}")
        return False


# Argument parsing
##############################################################################


def construct_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.set_defaults(func=lambda x: parser.print_usage())
    subparsers = parser.add_subparsers()

    # Logging options (mutually exclusive)
    log_group = parser.add_mutually_exclusive_group()
    log_group.add_argument(
        "-v",
        "--verbose",
        help="Enable verbose output (debug level)",
        action="store_true",
    )
    log_group.add_argument(
        "-q",
        "--quiet",
        help="Quiet mode (errors only)",
        action="store_true",
    )

    dist_parent = argparse.ArgumentParser(add_help=False)
    dist_parent.add_argument(
        "-d",
        "--dist",
        help="Distribution channel to build for",
        type=str,
        default="local",
        choices=["local", "ankiweb", "all"],
    )

    build_parent = argparse.ArgumentParser(add_help=False)
    build_parent.add_argument(
        "version",
        nargs="?",
        help="Version to (pre-)build as a git reference "
        "(e.g. 'v1.2.0' or 'd338f6405'). "
        "Special keywords: 'dev' - working directory, "
        "'current' - latest commit, 'release' - latest tag. "
        "Leave empty to build latest tag.",
    )

    build_group = subparsers.add_parser(
        "build",
        parents=[build_parent, dist_parent],
        help="Build and package add-on for distribution",
    )
    build_group.set_defaults(func=build)

    ui_group = subparsers.add_parser("ui", parents=[], help="Compile add-on user interface files")
    ui_group.set_defaults(func=ui)

    manifest_group = subparsers.add_parser(
        "manifest",
        parents=[build_parent, dist_parent],
        help="Generate manifest file from add-on properties",
    )
    manifest_group.set_defaults(func=manifest)

    init_group = subparsers.add_parser("init", help="Initialize a new add-on project")
    init_group.add_argument(
        "directory",
        nargs="?",
        help="Target directory for the new project (default: current directory)",
    )
    init_group.add_argument(
        "-y",
        "--yes",
        help="Use default values without prompting",
        action="store_true",
    )
    init_group.set_defaults(func=init)

    clean_group = subparsers.add_parser("clean", help="Clean leftover build files")
    clean_group.set_defaults(func=clean)

    link_group = subparsers.add_parser("link", help="Link add-on to Anki's addon directory for development")
    link_group.add_argument(
        "--unlink",
        help="Remove existing symbolic link instead of creating one",
        action="store_true",
    )
    link_group.set_defaults(func=link)

    test_group = subparsers.add_parser("test", help="Link add-on and launch Anki for testing")
    test_group.set_defaults(func=test)

    claude_group = subparsers.add_parser(
        "claude", help="Generate Claude AI assistant memory file for better assistance"
    )
    claude_group.add_argument(
        "--force",
        help="Overwrite existing CLAUDE.md file",
        action="store_true",
    )
    claude_group.set_defaults(func=claude)

    create_dist_group = subparsers.add_parser(
        "create_dist",
        parents=[build_parent, dist_parent],
        help="Prepare source tree distribution for building under dist/build. "
        "This is intended to be used in build scripts and should be run before "
        "`build_dist` and `package_dist`.",
    )
    create_dist_group.set_defaults(func=create_dist)

    build_dist_group = subparsers.add_parser(
        "build_dist",
        parents=[build_parent, dist_parent],
        help="Build add-on files from prepared source tree under dist/build. "
        "This step performs all source code post-processing handled by "
        "aab itself (e.g. building the Qt UI and writing the add-on manifest). "
        "As with `create_dist` and `package_dist`, this command is meant to be "
        "used in build scripts where it can provide an avenue for performing "
        "additional processing ahead of packaging the add-on.",
    )
    build_dist_group.set_defaults(func=build_dist)

    package_dist_group = subparsers.add_parser(
        "package_dist",
        parents=[build_parent, dist_parent],
        help="Package pre-built distribution of add-on files under dist/build into a "
        "distributable .ankiaddon package. This is inteded to be used in build "
        "scripts and called after both `create_dist` and `build_dist` have been "
        "run.",
    )
    package_dist_group.set_defaults(func=package_dist)

    return parser


# Main
##############################################################################


def main() -> None:
    parser = construct_parser()
    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        log_level = logging.DEBUG
    elif args.quiet:
        log_level = logging.ERROR
    else:
        log_level = logging.INFO

    logging.basicConfig(
        level=log_level,
        format="%(message)s",
    )

    # Show copyright message unless in quiet mode
    if not args.quiet:
        logging.info(COPYRIGHT_MSG)

    try:
        # Skip validation for init command as it creates the project structure
        if hasattr(args, "func") and args.func != init and not validate_cwd():
            raise CLIError("Could not find 'src' or 'addon.json'. Please run this from the project root.")

        args.func(args)

    except CLIError as e:
        logging.error("Error: %s", e)
        sys.exit(1)
    except KeyboardInterrupt:
        logging.info("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        logging.error("Unexpected error: %s", e)
        logging.debug("Full traceback:", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
