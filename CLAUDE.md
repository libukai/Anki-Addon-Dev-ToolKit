# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AADT (Anki Add-on Developer Tools)** is a modern toolkit for developing Anki add-ons targeting Anki 2025.06+. The project focuses on Qt6-only support, type safety, and modern Python 3.13+ development practices.

## Core Architecture

### Package Structure (src-layout)
```
src/aadt/
├── __init__.py         # Package metadata and exports
├── cli.py              # Command-line interface (~350 LOC)
├── config.py           # Configuration management with JSON schema validation
├── builder.py          # Core build system and packaging
├── ui.py               # Qt Designer UI compilation with PyQt6→aqt.qt conversion
├── init.py             # Project scaffolding and template application
├── run.py              # Development environment linking and Anki integration
├── git.py              # Git operations and version management
├── manifest.py         # AnkiWeb manifest generation
├── utils.py            # Shared utilities
├── schema.json         # JSON schema for addon.json validation
└── templates/          # Project templates and Anki documentation
```

### Key Design Patterns

1. **CLI-First Architecture**: All functionality exposed through `aadt` CLI commands
2. **Type-Safe Configuration**: Uses dataclasses with JSON schema validation instead of plain dictionaries
3. **Modern Resource Management**: Auto-generates `__init__.py` files supporting `importlib.resources`
4. **Intelligent UI Compilation**: Converts PyQt6 imports to Anki-compatible `aqt.qt` imports with precise type inference

## Common Development Commands

### Environment Setup
```bash
# Install dependencies (including dev tools)
uv sync --group dev

# Run CLI in development mode
uv run aadt --help
```

### Code Quality & Testing
```bash
# Code style check and formatting
uv run ruff check src/aadt/
uv run ruff format src/aadt/

# Type checking (uses ty instead of mypy for speed)
uv run ty check src/aadt/

# Run tests with coverage
uv run pytest

# Combined quality checks
uv run ruff check src/aadt/ && uv run ty check src/aadt/
```

### Building & Distribution
```bash
# Build package
uv build

# Version management
uv version patch    # 1.0.0 → 1.0.1
uv version minor    # 1.0.0 → 1.1.0
uv version major    # 1.0.0 → 2.0.0
```

## Development Principles

1. **Function over Form**: Prioritize working features over technical elegance
2. **Simplicity over Complexity**: Choose straightforward solutions over complex ones
3. **Maintainability**: Code should be easy to understand and modify
4. **Modern Python**: Use Python 3.13+ features, complete type annotations, `str | None` syntax
5. **uv-First**: All dependency management through uv, not pip/poetry

## Key Technical Decisions

### UI Development System
- **Qt6 Exclusive**: No Qt5 compatibility layer
- **Smart Import Conversion**: Automatically converts `from PyQt6 import` to `from aqt.qt import`
- **Type Inference**: Analyzes UI files to provide correct widget type annotations (QDialog, QMainWindow, etc.)
- **Resource Management**: Copies resources from `ui/resources/` to final package with proper Python package structure

### Build System
- **Git-Aware**: Prefers git tags for versioning but gracefully degrades for non-git environments
- **Multi-Target**: Supports `local` (development) and `ankiweb` (distribution) build types
- **Manifest Generation**: Auto-generates AnkiWeb-compliant `manifest.json` from `addon.json`

### Configuration Management
- **Schema Validation**: Uses JSON schema to validate `addon.json` structure
- **Dataclass-Based**: Configuration objects use dataclasses for type safety
- **Template System**: Rich template system for project initialization

## Code Quality Standards

- **Line Length**: 120 characters (configured in pyproject.toml)
- **Type Coverage**: All functions must have complete type annotations
- **Test Coverage**: Minimum 20% coverage requirement
- **Complexity**: Maximum McCabe complexity of 10
- **Import Style**: Use modern union syntax (`str | None` not `Optional[str]`)

## Error Handling Patterns

- **Exception Chaining**: Use `raise ... from e` to preserve original errors
- **Custom Exceptions**: Define specific exception types for different error categories
- **User-Friendly Messages**: CLI errors should be clear and actionable

## Testing Strategy

- **pytest-based**: Uses pytest with coverage reporting
- **Test Data**: Sample projects in `tests/data/` for integration testing
- **Mock Testing**: Uses pytest-mock for external dependencies
- **Markers**: Tests categorized as `unit`, `integration`, or `slow`

## Performance Considerations

- **Fast Type Checking**: Uses `ty` instead of `mypy` for better performance
- **Concurrent Operations**: Support for parallel tool execution where possible
- **Smart Caching**: Avoid redundant operations through intelligent caching

## Integration Points

### Anki Integration
- Links development projects to Anki's add-on directory via symlinks
- Launches Anki for testing with `aadt test` command
- Handles Anki 2025.06+ Qt6 requirements specifically

### Git Integration
- Version detection through git tags
- Clean source archiving via `git archive`
- Graceful fallback for non-git environments

### External Tool Dependencies
- **uv**: Modern Python package manager for all operations
- **pyuic6**: Qt UI file compilation
- **ruff**: Code linting and formatting
- **ty**: Fast type checking