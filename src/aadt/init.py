"""
Project initialization module for creating new Anki add-on projects.
"""

import json
import re
import subprocess
from pathlib import Path
from typing import Any

import questionary

from aadt import PATH_PACKAGE
from aadt.config import AddonConfig


class ProjectInitializationError(Exception):
    """Exception raised when project initialization fails"""

    pass


class ProjectInitializer:
    """
    Handles the initialization of new Anki add-on projects.
    Creates project structure, configuration files, and template code.
    """

    def __init__(self, target_dir: Path) -> None:
        self.target_dir = target_dir
        self.config_path = target_dir / "addon.json"
        self.templates_dir = PATH_PACKAGE / "templates"

    def init_project(self, interactive: bool = True) -> None:
        """
        Initialize a new add-on project in the target directory.

        Args:
            interactive: Whether to prompt for user input

        Raises:
            ProjectInitializationError: If initialization fails
        """
        # Create target directory if it doesn't exist
        self._ensure_target_directory()

        existing_config = None
        if self.config_path.exists():
            # Load existing configuration
            existing_config = self._load_existing_config()
            print("📋 Found existing addon.json. Will preserve existing configuration.")

        if interactive:
            config_data = self._collect_project_info(existing_config)
        else:
            config_data = self._get_default_config(existing_config)

        # Create and validate configuration
        try:
            config = AddonConfig.from_dict(config_data)
        except (KeyError, TypeError, ValueError) as e:
            raise ProjectInitializationError(f"Invalid configuration data: {e}") from e

        # Create project structure
        self._create_project_structure(config)

        # Write configuration file
        self._write_config_file(config_data)

        # Create template files (including pyproject.toml)
        self._create_template_files(config)

        # Sync uv dependencies after pyproject.toml is created
        self._sync_uv_dependencies()

        # Initialize Git repository
        self._init_git_repository()

        print("\n✅ Add-on project initialized successfully!")
        print(f"📁 Project directory: {self.target_dir}")
        print(f"🔧 Edit {self.config_path} to customize your configuration")
        print("\n📦 Ready to develop! Next steps:")
        print("   1. Test with Anki: uv run aadt test")
        print("   2. Build add-on: uv run aadt build")
        print(f"   3. Develop your code in src/{config.module_name}/")
        print("\n💡 Tip: Use 'uv run aadt <command>' for local development")
        print("💡 Dependencies are organized in a single dev group")

    def _load_existing_config(self) -> dict[str, Any]:
        """Load existing addon.json configuration."""
        try:
            with self.config_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            raise ProjectInitializationError(f"Failed to load existing addon.json: {e}") from e

    def _collect_project_info(self, existing_config: dict[str, Any] | None = None) -> dict[str, Any]:
        """Collect project information through interactive prompts."""
        if existing_config:
            print("🔄 Updating existing Anki add-on project...\n")
        else:
            print("🚀 Initializing new Anki add-on project...\n")

        # Get basic project info
        basic_answers = self._collect_basic_info(existing_config)
        display_name = basic_answers["display_name"]
        
        # Get module and repo names
        name_answers = self._collect_name_info(existing_config, display_name)
        basic_answers.update(name_answers)
        
        # Get description
        description = self._collect_description(existing_config)
        
        # Get optional fields
        optional_answers = self._collect_optional_info(existing_config)
        
        # Build final configuration
        return self._build_config_data(basic_answers, description, optional_answers, existing_config)

    def _collect_basic_info(self, existing_config: dict[str, Any] | None) -> dict[str, Any]:
        """Collect basic project information."""
        display_name_default = self._get_config_value(existing_config, "display_name", self._suggest_display_name())
        author_default = self._get_config_value(existing_config, "author", "")
        
        answers = questionary.form(
            display_name=questionary.text(
                "Display name (shown to users):", 
                default=display_name_default
            ),
            author=questionary.text(
                "Author name (the coder maybe AI):",
                default=author_default
            ),
        ).ask()

        if not answers:
            raise ProjectInitializationError("Initialization cancelled.")
        return answers

    def _collect_name_info(self, existing_config: dict[str, Any] | None, display_name: str) -> dict[str, Any]:
        """Collect module and repository name information."""
        module_name_default = self._get_config_value(
            existing_config, "module_name", self._suggest_module_name(display_name)
        )
        repo_name_default = self._get_config_value(
            existing_config, "repo_name", self._suggest_repo_name(display_name)
        )
        
        answers = questionary.form(
            module_name=questionary.text(
                "Module name (Python package name):",
                default=module_name_default,
                validate=lambda text: re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", text) is not None,
            ),
            repo_name=questionary.text(
                "Repository name (for files/GitHub):",
                default=repo_name_default,
            ),
        ).ask()

        if not answers:
            raise ProjectInitializationError("Initialization cancelled.")
        return answers

    def _collect_description(self, existing_config: dict[str, Any] | None) -> str:
        """Collect project description."""
        default_desc = "An Anki add-on that enhances your flashcard experience."
        description_default = self._get_config_value(existing_config, "description", default_desc)
        
        description = questionary.text(
            "Description (brief description of your add-on):",
            default=description_default,
        ).ask()

        if not description:
            raise ProjectInitializationError("Initialization cancelled.")
        return description

    def _collect_optional_info(self, existing_config: dict[str, Any] | None) -> dict[str, Any]:
        """Collect optional project information."""
        answers = questionary.form(
            ankiweb_id=questionary.text(
                "AnkiWeb ID (optional, for existing add-ons):",
                default=self._get_config_value(existing_config, "ankiweb_id", "")
            ),
            contact=questionary.text(
                "Contact email (optional):",
                default=self._get_config_value(existing_config, "contact", "")
            ),
            homepage=questionary.text(
                "Homepage URL (optional):",
                default=self._get_config_value(existing_config, "homepage", "")
            ),
            tags=questionary.text(
                "Tags (space-separated, optional):",
                default=self._format_tags_for_display(existing_config.get("tags") if existing_config else None)
            ),
            min_anki_version=questionary.text(
                "Minimum Anki version (optional, e.g., '24.04'):",
                default=self._get_config_value(existing_config, "min_anki_version", "")
            ),
        ).ask()

        if not answers:
            raise ProjectInitializationError("Initialization cancelled.")
        return answers

    def _build_config_data(self, basic_answers: dict[str, Any], description: str, 
                          optional_answers: dict[str, Any], existing_config: dict[str, Any] | None) -> dict[str, Any]:
        """Build final configuration data."""
        config_data = {
            "display_name": basic_answers["display_name"],
            "module_name": basic_answers["module_name"],
            "repo_name": basic_answers["repo_name"],
            "author": basic_answers["author"],
            "description": description,
            "conflicts": existing_config.get("conflicts", []) if existing_config else [],
            "targets": existing_config.get("targets", ["qt6"]) if existing_config else ["qt6"],
            "ankiweb_id": optional_answers.get("ankiweb_id", ""),
        }

        # Add optional fields if provided
        for key, value in optional_answers.items():
            if key != "ankiweb_id" and value:
                if key == "tags" and isinstance(value, str):
                    # Convert space-separated tags to list
                    config_data[key] = value.split()
                else:
                    config_data[key] = value

        # Preserve any additional fields from existing config that weren't prompted for
        if existing_config:
            preserve_fields = [
                "copyright_start", "max_anki_version", "tested_anki_version",
                "ankiweb_conflicts_with_local", "local_conflicts_with_ankiweb",
                "build_config", "ui_config"
            ]
            for field in preserve_fields:
                if field in existing_config:
                    config_data[field] = existing_config[field]

        return config_data

    def _get_default_config(self, existing_config: dict[str, Any] | None = None) -> dict[str, Any]:
        """Get default configuration for non-interactive mode."""
        dir_name = self.target_dir.name
        defaults = {
            "display_name": self._suggest_display_name(),
            "module_name": self._suggest_module_name(dir_name),
            "repo_name": self._suggest_repo_name(dir_name),
            "author": "TODO: Set author name",
            "description": "An Anki add-on that enhances your flashcard experience.",
            "conflicts": [],
            "targets": ["qt6"],
            "ankiweb_id": "",
        }
        
        if existing_config:
            # Keep existing config, just ensure required fields exist
            config_data = existing_config.copy()
            for key, value in defaults.items():
                if key not in config_data:
                    config_data[key] = value
            return config_data
        
        return defaults

    def _prompt(self, question: str, default: str, required: bool = True) -> str:
        """Prompt user for input with default value."""
        prompt = f"{question} [{default}]: " if default else f"{question}: "

        while True:
            response = input(prompt).strip()
            if response:
                return response
            elif default:
                return default
            elif not required:
                return ""
            else:
                print("This field is required. Please enter a value.")

    def _suggest_display_name(self) -> str:
        """Suggest a display name based on directory name."""
        dir_name = self.target_dir.name
        # Convert kebab-case or snake_case to Title Case
        words = re.sub(r"[-_]", " ", dir_name).split()
        return " ".join(word.capitalize() for word in words)

    def _suggest_module_name(self, display_name: str) -> str:
        """Suggest a Python module name based on display name."""
        # Convert to lowercase, replace spaces/hyphens with underscores
        name = re.sub(r"[^a-zA-Z0-9_]", "_", display_name.lower())
        # Remove multiple underscores and leading/trailing underscores
        name = re.sub(r"_+", "_", name).strip("_")
        # Ensure it starts with a letter
        if name and name[0].isdigit():
            name = f"addon_{name}"
        return name or "my_addon"

    def _suggest_repo_name(self, display_name: str) -> str:
        """Suggest a repository name based on display name."""
        # Convert to lowercase, replace spaces with hyphens
        name = re.sub(r"[^a-zA-Z0-9\-]", "-", display_name.lower())
        # Remove multiple hyphens and leading/trailing hyphens
        name = re.sub(r"-+", "-", name).strip("-")
        return name or "my-addon"

    def _get_config_value(self, existing_config: dict[str, Any] | None, key: str, default: str) -> str:
        """Get configuration value with fallback to default."""
        if not existing_config:
            return default
        return existing_config.get(key) or default

    def _format_tags_for_display(self, tags: Any) -> str:
        """Format tags for display in the questionary prompt."""
        if not tags:
            return ""
        if isinstance(tags, list):
            return " ".join(tags)
        if isinstance(tags, str):
            return tags
        return str(tags)

    def _render_template(self, template_name: str, config: AddonConfig) -> str:
        """Render a template file with configuration values."""
        template_path = self.templates_dir / f"{template_name}.template"
        try:
            with template_path.open("r", encoding="utf-8") as f:
                template_content = f.read()
        except FileNotFoundError as e:
            raise ProjectInitializationError(f"Template file not found: {template_path}") from e

        # Prepare template variables
        template_vars = {
            "display_name": config.display_name,
            "module_name": config.module_name,
            "repo_name": config.repo_name,
            "author": config.author,
            "email_part": f', "email" = "{config.contact}"' if config.contact else "",
        }

        try:
            return template_content.format(**template_vars)
        except KeyError as e:
            raise ProjectInitializationError(f"Missing template variable: {e}") from e

    def _copy_static_file(self, template_name: str, target_path: Path) -> None:
        """Copy a static file from templates directory."""
        template_path = self.templates_dir / template_name
        try:
            with template_path.open("r", encoding="utf-8") as f:
                content = f.read()
            target_path.write_text(content, encoding="utf-8")
        except FileNotFoundError as e:
            raise ProjectInitializationError(f"Template file not found: {template_path}") from e

    def _create_project_structure(self, config: AddonConfig) -> None:
        """Create the standard project directory structure."""
        directories = [
            self.target_dir / "src" / config.module_name,
            self.target_dir / "ui" / "designer",
            self.target_dir / "ui" / "resources",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def _write_config_file(self, config_data: dict[str, Any]) -> None:
        """Write the addon.json configuration file."""
        with self.config_path.open("w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

    def _create_template_files(self, config: AddonConfig) -> None:
        """Create template files from templates directory."""
        src_dir = self.target_dir / "src" / config.module_name

        # Copy static Python source files
        self._copy_static_file("__init__.py", src_dir / "__init__.py")

        # Create project configuration files (with templates)
        readme_content = self._render_template("README.md", config)
        (self.target_dir / "README.md").write_text(readme_content, encoding="utf-8")

        pyproject_content = self._render_template("pyproject.toml", config)
        (self.target_dir / "pyproject.toml").write_text(pyproject_content, encoding="utf-8")

        # Copy static configuration files
        self._copy_static_file("gitignore", self.target_dir / ".gitignore")
        self._copy_static_file("python-version", self.target_dir / ".python-version")

        # Copy ANKI.md file (Anki development reference)
        self._copy_static_file("ANKI.md", self.target_dir / "ANKI.md")

    def _init_git_repository(self) -> None:
        """Initialize Git repository and create initial commit."""
        try:
            # Initialize git repository
            subprocess.run(
                ["git", "init"],  # noqa: S607
                cwd=self.target_dir,
                check=True,
                capture_output=True,
                text=True,
            )

            # Add all files
            subprocess.run(
                ["git", "add", "."],  # noqa: S607
                cwd=self.target_dir,
                check=True,
                capture_output=True,
                text=True,
            )

            # Create initial commit
            subprocess.run(
                [  # noqa: S607
                    "git",
                    "commit",
                    "-m",
                    "Initial commit: Create new Anki add-on project",
                ],
                cwd=self.target_dir,
                check=True,
                capture_output=True,
                text=True,
            )

            print("🔥 Git repository initialized with initial commit")

        except subprocess.CalledProcessError as e:
            print(f"⚠️ Warning: Failed to initialize Git repository: {e}")
            print("You can manually run 'git init' and 'git add .' to set up version control")
        except FileNotFoundError:
            print("⚠️ Warning: Git not found. Please install Git to enable version control")

    def _init_uv_environment(self) -> None:
        """Initialize uv environment and install dependencies."""
        try:
            # Note: We skip 'uv init' because we create our own pyproject.toml
            # Just sync dependencies after our pyproject.toml is created
            pass  # Will be called after _create_template_files

        except Exception as e:
            print(f"⚠️ Warning: Failed to prepare UV environment: {e}")

    def _sync_uv_dependencies(self) -> None:
        """Sync uv dependencies after pyproject.toml is created."""
        try:
            # Sync dependencies with dev group
            subprocess.run(
                ["uv", "sync", "--group", "dev"],  # noqa: S607
                cwd=self.target_dir,
                check=True,
                capture_output=True,
                text=True,
            )

            print("🚀 UV dependencies installed successfully")

        except subprocess.CalledProcessError as e:
            print(f"⚠️ Warning: Failed to install dependencies: {e}")
            print("You can manually run 'uv sync --group dev' to install dependencies")
        except FileNotFoundError:
            print("⚠️ Warning: UV not found. Please install UV for dependency management")

    def _ensure_target_directory(self) -> None:
        """Create target directory if it doesn't exist."""
        if not self.target_dir.exists():
            try:
                self.target_dir.mkdir(parents=True)
                print(f"Created directory: {self.target_dir}")
            except OSError as e:
                raise ProjectInitializationError(f"Could not create directory '{self.target_dir}': {e}") from e
