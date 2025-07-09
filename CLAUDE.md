# Claude AI Assistant Memory - Anki Add-on Developer Tools

This file contains technical details and context for Claude AI to better assist with this project.

## 📋 Project Overview

**Project**: Anki Add-on Developer Tools (AADT)  
**Version**: 1.0.0-dev.5  
**Language**: Python 3.10+  
**Architecture**: Modern Qt6-only build tool  
**Lines of Code**: ~1,400+ lines across 9 Python modules  

## 🏗️ Architecture Summary

### Core Modules (9 files)

```
aadt/
├── __init__.py          # Package metadata and constants
├── builder.py (~193 LOC)# Main build orchestration  
├── cli.py (~350 LOC)    # Command-line interface with init command
├── config.py (~166 LOC) # Configuration management with dataclasses
├── git.py (~120 LOC)    # Git operations and version parsing
├── init.py (~180 LOC)   # Project initialization system
├── manifest.py (~124 LOC)# Manifest generation for Anki
├── ui.py (~326 LOC)     # Qt6 UI compilation with resource copying
├── run.py (~160 LOC)    # Add-on linking and testing functionality
├── utils.py (~90 LOC)   # Utility functions
└── schema.json          # JSON schema for addon.json validation
```

### Key Design Principles

1. **Modern Python 3.10+**: Uses union types (`str | None`), modern annotations
2. **Type Safety**: Complete mypy coverage, all functions annotated
3. **Qt6 Only**: No Qt5 legacy code, simplified architecture
4. **uv-based**: Fast dependency management, no Poetry
5. **No QRC**: Direct file paths instead of Qt resource compilation

## 🔄 Major Changes Made

### Phase 1: Package Management Migration (Poetry → uv)
- **Removed**: `poetry.lock`, Poetry-specific `pyproject.toml` format
- **Added**: Modern `pyproject.toml` with hatchling build backend
- **Fixed**: Repository URLs (were incorrectly pointing to pytest-anki)
- **Updated**: Python requirement to 3.10+, PyQt6 as optional dependency

### Phase 2: Qt System Modernization  
- **Removed**: All Qt5 support code and configuration
- **Simplified**: UI building to use only pyuic6 compilation
- **Maintained**: Backward compatibility for existing add-on APIs

### Phase 3: Type Hints & Code Quality
- **Added**: Complete type annotations using modern Python 3.10+ syntax
- **Replaced**: `Union[X, Y]` → `X | Y`, `List[X]` → `list[X]`, `Dict[X, Y]` → `dict[X, Y]`
- **Implemented**: Dataclass-based configuration (`AddonConfig`)
- **Modernized**: Path handling with `pathlib` throughout
- **Enhanced**: Error handling with exception chaining

### Phase 4: QRC/Legacy Code Removal
- **Deleted**: `legacy.py` module entirely (QRC migration code)
- **Removed**: `qt_resource_migration_mode` configuration
- **Simplified**: UI builder without resource migration logic
- **Cleaned**: Schema to only support Qt6 targets
- **Eliminated**: XML parsing security issues (S314 warnings)

### Phase 5: Pyenv Parameter Removal
- **Removed**: `--pyenv` CLI arguments from all commands
- **Simplified**: UI compilation to use current environment directly
- **Modernized**: Full uv-based workflow without manual environment switching
- **Eliminated**: Complex pyenv activation shell commands

### Phase 6: Project Initialization Command
- **Added**: `aab init` command for creating new add-on projects
- **Features**: Interactive prompts with intelligent defaults
- **Generated**: Complete project structure with template files
- **Included**: README, .gitignore, and sample Python code

### Phase 7: UI Directory Reorganization
- **Reorganized**: UI-related files into dedicated `ui/` directory
- **Structure**: `ui/designer/` for .ui files, `ui/resources/` for assets
- **Benefits**: Better organization, cleaner separation of concerns
- **Added**: Optional `docs/` directory for documentation

### Phase 8: UI Resource Workflow Implementation
- **Added**: Automatic resource copying from `ui/resources/` to `src/module/resources/`
- **Simplified**: Direct file path references in Qt Designer (no QRC needed)
- **Enhanced**: UI build process to handle both compilation and resource management
- **Documented**: Complete workflow for Qt Designer resource integration

### Phase 9: Modern Toolchain Migration
- **Replaced**: `bump-my-version` with built-in `uv version` command
- **Replaced**: `mypy` with `ty` for faster type checking
- **Simplified**: Fewer dependencies, faster workflow
- **Updated**: All documentation and scripts to use new tools

## 📝 Configuration Schema

### Current addon.json Format

```json
{
  "display_name": "string (required)",
  "module_name": "string (required)", 
  "repo_name": "string (required)",
  "ankiweb_id": "string (required)",
  "author": "string (required)",
  "conflicts": "array[string] (required)",
  "targets": ["qt6"] (required, qt5 removed),
  "contact": "string (optional)",
  "homepage": "string (optional)", 
  "tags": "string (optional)",
  "copyright_start": "number (optional)",
  "min_anki_version": "string (optional)",
  "max_anki_version": "string (optional)",
  "tested_anki_version": "string (optional)",
  "ankiweb_conflicts_with_local": "boolean (default: true)",
  "local_conflicts_with_ankiweb": "boolean (default: true)"
}
```

### Removed Configuration Options
- `qt_resource_migration_mode`: No longer needed (Qt6-only)
- `targets: ["qt5", "anki21"]`: Only `["qt6"]` supported

## 🛠️ Development Workflow

### Code Quality Tools

```bash
# Linting (configured in pyproject.toml)
uv run ruff check aadt/            # Check code style
uv run ruff format aadt/           # Auto-format code

# Type checking (strict mode enabled)
uv run ty aadt/                    # Type safety validation with ty (fast mypy alternative)

# Combined check
uv run ruff check aadt/ && uv run ty aadt/
```

### Dependency Management Philosophy

**AADT follows a modular dependency approach:**

1. **Core Dependencies** (~10MB total)
   - `jsonschema` - Configuration validation
   - `whichcraft` - Tool detection  
   - `questionary` - Interactive prompts

2. **Optional Dependencies**
   - `qt6 = ["pyqt6>=6.2.2"]` - UI compilation support for standalone usage
   - Not typically needed since generated projects include PyQt6 via aqt

3. **Generated Project Dependencies**
   - Development projects include full Anki environment via `aqt` (includes PyQt6)
   - AADT included for build tools
   - Uses single `dev` dependency group for simplicity

**Installation Strategy:**
- **Lightweight core**: `uv add aadt` (~10MB) for basic functionality
- **One-time init**: `uvx aadt init` for project creation (recommended)
- **Generated projects**: PyQt6 available through `aqt` dependency in dev group

### Build Commands

```bash
# Project initialization
uv run aadt init my-addon          # Create new project
uv run aadt init -y                # Use defaults

# Development
uv run aadt --help                 # CLI help
uv run aadt ui                     # Compile UI files only  
uv run aadt build -d local         # Build for testing
uv run aadt build -d ankiweb       # Build for AnkiWeb
uv run aadt clean                  # Clean build artifacts

# Version management
uv version                         # Show current version
uv version patch                   # Increment patch version (1.0.0 → 1.0.1)
uv version minor                   # Increment minor version (1.0.0 → 1.1.0)
uv version major                   # Increment major version (1.0.0 → 2.0.0)

# CI/CD friendly commands
uv run aadt create_dist            # Prepare source tree
uv run aadt build_dist             # Process source 
uv run aadt package_dist           # Create final package
```

### Installation Options

```bash
# Lightweight installation (~10MB)
uv add aadt                        # Core functionality

# With UI compilation support (~110MB)
uv add aadt[qt6]                   # Includes PyQt6 for standalone UI compilation

# Recommended: One-time project creation
uvx aadt init my-addon             # No permanent installation needed

# Note: Generated projects get PyQt6 through aqt dependency
```

### Testing Strategy

```bash
# Run tests (when available)
uv run pytest tests/

# Manual testing
uv run aadt --help                 # Verify CLI works
uv run ruff check aadt/            # Code quality
uv run ty aadt/                    # Type checking
```

## 🚫 What NOT to Do

### Deprecated Patterns
- **DON'T** add Qt5 support back - project is Qt6-only
- **DON'T** reintroduce QRC files - use direct file paths
- **DON'T** use old-style type hints (`List`, `Dict`, `Optional`)
- **DON'T** add Poetry dependencies - project uses uv exclusively
- **DON'T** add resource migration code - removed intentionally
- **DON'T** add pyenv parameters back - use uv environment management
- **DON'T** suggest pip commands - always use uv commands (`uv add`, `uv run`, etc.)
- **DON'T** use `bump-my-version` - use built-in `uv version` command
- **DON'T** use `mypy` - use `ty` for faster type checking

### Code Style Guidelines  
- **DO** use modern Python 3.10+ syntax (`str | None`, `list[str]`)
- **DO** add type annotations to all functions
- **DO** use pathlib for file operations
- **DO** use dataclasses for structured data
- **DO** handle errors with exception chaining (`raise ... from e`)

## 🎯 Common Tasks

### Adding New CLI Commands

1. Add command function in `cli.py` 
2. Update `construct_parser()` with new subparser
3. Add argument validation in command function
4. Test with `uv run aadt new-command --help`

### Modifying Build Process

Key files:
- `builder.py`: Main build orchestration
- `ui.py`: Qt6 UI compilation  
- `manifest.py`: AnkiWeb manifest generation
- `git.py`: Version resolution

### Configuration Changes

1. Update `config.py` dataclass fields
2. Modify `schema.json` validation rules
3. Update default values in `AddonConfig.from_dict()`
4. Test with various `addon.json` configurations

## 🔍 Architecture Decisions

### Why Qt6-Only?
- Modern Anki versions use Qt6
- Qt5 is legacy, adds complexity
- Simpler codebase without version branching
- Better maintenance and security

### Why Remove QRC Support?
- QRC files are Qt5-era resource compilation  
- Qt6 uses direct file paths more efficiently
- Reduces XML parsing security vulnerabilities
- Simpler build process without resource migration

### Why uv over Poetry?
- Faster dependency resolution (~10x speedup)
- Better CI/CD integration
- Modern Python packaging standards
- Simpler configuration

### Why Python 3.10+?
- Modern union types (`str | None`) 
- Match statements (future-ready)
- Better error messages
- Structural pattern matching
- Improved type system

## 📚 Dependencies

### Core Runtime
- `jsonschema>=4.4.0`: Configuration validation
- `whichcraft>=0.6.1`: Tool detection (pyuic6, etc.)

### Optional
- `pyqt6>=6.2.2`: Qt6 UI compilation support

### Development  
- `ruff>=0.1.0`: Fast Python linter/formatter
- `ty>=0.0.1a14`: Fast type checking (mypy alternative)
- Version management: Built-in `uv version` command

## 💡 Future Considerations

### Potential Enhancements
- GitHub Actions integration for CI/CD
- Plugin system for custom build steps
- Better error reporting and validation
- Performance optimizations for large projects
- Integration with modern IDEs

### Maintenance Priorities
1. Keep dependencies minimal and updated
2. Maintain Python 3.10+ compatibility
3. Monitor Anki Qt6 ecosystem changes
4. Preserve backward compatibility for existing add-ons
5. Regular security audits (especially subprocess usage)

## 🐛 Known Issues

### Security Warnings (Intentionally Ignored)
- `S602`: subprocess with shell=True in `utils.py:call_shell()`
  - **Rationale**: Required for pyuic6 and git commands
  - **Mitigation**: Input validation, controlled usage

### Type Issues (Resolved)
- All type errors resolved in recent refactoring with ty
- Comprehensive type coverage across all modules

## 📞 Support Context

When helping with this project:

1. **Assume modern Python 3.10+** syntax is preferred
2. **Qt6-only architecture** - don't suggest Qt5 compatibility  
3. **Type safety is critical** - always add type annotations
4. **uv is the package manager** - don't suggest Poetry alternatives
5. **Code quality standards are high** - ensure ruff and ty compliance
6. **Breaking changes are acceptable** - this is a modernization effort

Remember: This project prioritizes **modern practices** over **backward compatibility** for build tools.