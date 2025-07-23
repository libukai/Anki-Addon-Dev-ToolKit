# Anki Add-on Dev ToolKit (AADT)

<a title="License: GNU AGPLv3" href="https://github.com/glutanimate/anki-addon-builder/blob/master/LICENSE"><img src="https://img.shields.io/badge/license-GNU AGPLv3-green.svg"></a>
<a href="https://pypi.org/project/aadt/"><img src="https://img.shields.io/pypi/v/aadt.svg"></a>
<img src="https://img.shields.io/pypi/status/aadt.svg">

**Modern, AI-driven, focused on Anki new versions (2025.06+) add-on development and build toolkit with complete type safety and modern Python practices.**

English | [中文](#中文版)

## 🚀 Features

- **Python 3.13** Compatible with Anki 2025.06+
- **Qt6 Exclusive Support** Adapted for Anki 2025.06+ versions
- **Elegant Dependency Management** Fully based on uv for environment and dependency management
- **Code Quality Tools** Integrated ruff and mypy for code quality enhancement
- **Comprehensive CLI Commands** Covering the entire workflow from initialization to release
- **Convenient Build and Distribution** Support for AnkiWeb and local distribution

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Command Details](#command-details)
- [CI/CD Support](#cicd-support)
- [UI Development](#ui-development)
- [Code Quality](#code-quality)
- [Unit Testing](#unit-testing)
- [Git Integration](#git-integration)
- [License](#license)

## 🔧 Prerequisites

Install uv locally via `curl -LsSf https://astral.sh/uv/install.sh | sh`.

## ⚡ Quick Start

### 1. Initialize Add-on Project

Use `uvx` to run the latest version of the `init` command to quickly initialize your project:

```bash
# Create directory
mkdir my-addon
cd my-addon

# Interactive setup
uvx aadt init
```

The default initialization creates a basic but complete add-on project, including:

- Interactive collection of add-on information
- Application of template files and generation of project structure
- Development environment configuration and dependency installation via uv
- Git repository creation and initialization

After initialization, the project directory structure is as follows:

```
my_addon/
├── addon.json          # Add-on configuration file
├── src/                # Source code
│   └── my_addon/       # Main module
│       └── __init__.py # Main module initialization file
├── ui/                 # UI design
│   ├── designer/       # Qt Designer .ui files
│   └── resources/      # UI resources (icons, styles)
├── README.md           # Project documentation
├── ANKI.md             # Anki core library documentation
├── pyproject.toml      # Project configuration
├── uv.lock             # uv lock file
├── .python-version     # Specify Python version
├── .git/               # Git repository
└── .gitignore          # Ignore files
```

**💡 Tip**: After initialization, it's recommended to immediately run `uv run aadt claude` to generate the AI assistant memory file, which will provide complete modern Anki development guidance and help Claude AI better assist your add-on development work.

### 2. Development

To improve Add-on development efficiency, it's strongly recommended to use AI-assisted programming during development. AADT provides the `claude` command to generate specialized Claude Code guidance files:

```bash
# Generate CLAUDE.md file
aadt claude
```

This command will generate a CLAUDE.md file in the root directory based on your project configuration, including core guidance for Anki 25.06+ Add-on development, helping Claude AI better understand your project and provide precise development suggestions.

Additionally, there's an ANKI.md file in the root directory containing detailed documentation of modern Anki 25.06+ source code analysis and best practices, helping human programmers better understand Anki's overall architecture and development approach.

### 3. Testing

For convenient testing in the development environment, AADT provides the `test` command for testing add-ons in Anki.

```bash
aadt test
```

Running the `test` command will first create a soft link from the `src/` directory's project folder to Anki's add-on directory, then automatically start Anki and load the add-on.

AADT also provides the `link` command to manage operations for soft linking the project source code folder to Anki's add-on directory.

```bash
# Create soft link
aadt link

# Remove soft link
aadt link --unlink
```

### 4. Build

AADT provides the `build` command for building add-ons.

```bash
aadt build
```

The build command depends on a git repository and will by default find the latest git tag and build the corresponding commit version, making it easy to distinguish between test versions and official versions.

The generated add-on package is stored in the `dist` directory and can be used for direct installation or upload to AnkiWeb for distribution.

## 🔧 Command Details

### `init` - Initialize Add-on Project
```bash
# Initialize in current directory (interactive)
aadt init

# Initialize in specified directory
aadt init my-addon

# Use default values (non-interactive)
aadt init -y
```

**Features:**
- Interactive collection of add-on information (name, author, description, etc.)
- Generate complete project structure and apply template files
- Configure Python environment and dependency management using uv
- Initialize Git repository

### `ui` - Compile User Interface
```bash
# Compile all UI files
aadt ui
```

**Features:**
- Compile `.ui` files from `ui/designer/` to `src/module_name/gui/forms/qt6/`
- Automatically copy resource files from `ui/resources/` to `src/module_name/resources/`
- Support for icons, stylesheets, and various resource files

### `test` - Launch Testing
```bash
# Link add-on and start Anki testing
aadt test
```

**Features:**
- Automatically execute `aadt link` to create soft links
- Start Anki program to load add-on
- One-click testing workflow

### `link` - Development Environment Linking
```bash
# Create soft link to Anki add-on directory
aadt link

# Remove soft link
aadt link --unlink
```

**Features:**
- Soft link the add-on project folder under `src/` to Anki's add-on directory
- Convenient for launching Anki instances for real-time testing during development

### `claude` - Generate Claude AI Assistant Memory File
```bash
# Generate CLAUDE.md file
aadt claude

# Force overwrite existing file
aadt claude --force
```

**Features:**
- Automatically generate `CLAUDE.md` file based on project `addon.json` configuration
- Includes modern Anki 25.06+ development best practices and guidance
- Prevents accidental overwriting of existing CLAUDE.md files, supports `--force` for forced overwriting

### `build` - Build and Package Add-on
```bash
# Build latest tag version (default)
aadt build

# Build specific version
aadt build v1.2.0        # Specific git tag
aadt build dev           # Working directory (including uncommitted changes)
aadt build current       # Latest commit
aadt build release       # Latest tag (default)

# Specify distribution type
aadt build -d local      # Local development version
aadt build -d ankiweb    # AnkiWeb submission version
aadt build -d all        # Build both types simultaneously

# Combined usage
aadt build v1.2.0 -d local
```

**Distribution Type Description:**
- `local`: Suitable for local development, retains debug information
- `ankiweb`: Suitable for AnkiWeb submission, optimized file size
- `all`: Generate both versions simultaneously

**Features:**
- Generate `manifest.json` required by AnkiWeb based on `addon.json` configuration
- Include add-on metadata, dependencies, and other information

### `manifest` - Generate Manifest File
```bash
# Generate manifest.json
aadt manifest
```

### `clean` - Clean Build Files
```bash
# Clean all build artifacts
aadt clean
```

**Features:**
- Delete `dist/` directory and its contents
- Clean temporary files and cache

## 🚀 CI/CD Support

These commands provide finer build control, suitable for automated build pipelines:

### `create_dist` - Prepare Source Code Tree
```bash
aadt create_dist [version]
```

**Features:**
- Prepare source code tree to `dist/build` directory
- Handle version control and file archiving
- Prepare for subsequent build steps

#### `build_dist` - Build Source Code
```bash
aadt build_dist
```

**Features:**
- Process source code in `dist/build`
- Compile UI files, generate manifest files
- Execute all necessary code post-processing

#### `package_dist` - Package Distribution
```bash
aadt package_dist
```

**Features:**
- Package built files into `.ankiaddon` format
- Generate final distribution package

## 🎨 UI Development

### Using Qt Designer

AADT provides seamless integration for Qt Designer UI development with **intelligent PyQt6 to aqt.qt conversion** functionality:

1. **Design UI**: Create `.ui` files in `ui/designer/`
2. **Add Resources**: Place images and icons in `ui/resources/`
3. **Reference Resources**: Reference files in `ui/resources/` in Qt Designer
4. **Build UI**: Run `aadt ui` to automatically compile and copy resources

```bash
# Your project structure
my-addon/
├── ui/
│   ├── designer/
│   │   └── dialog.ui          # References ../resources/icon.png
│   └── resources/
│       └── icon.png           # Your resource file
└── src/my_addon/

# After running 'aadt ui'
my-addon/
├── src/my_addon/
│   ├── gui/forms/qt6/
│   │   └── dialog.py          # Compiled UI, using aqt.qt imports
│   └── resources/
│       └── icon.png           # Automatically copied resource
```

### 🧠 Intelligent PyQt6 to aqt.qt Conversion

During the conversion process, AADT automatically converts pyuic6 output to Anki-compatible format and provides precise type annotations:

**Original Conversion (pyuic6 output):**
```python
from PyQt6 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.label = QtWidgets.QLabel(Dialog)
        # ...
```

**Specialized Conversion (AADT intelligent conversion):**
```python
from aqt.qt import QDialog, QVBoxLayout, QLabel, QMetaObject

class Ui_Dialog(object):
    def setupUi(self, Dialog: QDialog) -> None:
        Dialog.setObjectName("Dialog")
        self.verticalLayout = QVBoxLayout(Dialog)
        self.label = QLabel(Dialog)
        # ...
```

### 🎯 Intelligent Type Inference

AADT analyzes your UI files and provides **precise type annotations** based on aqt.qt's actual type system:

- **`Ui_Dialog`** → `QDialog` type annotation
- **`Ui_MainWindow`** → `QMainWindow` type annotation
- **`Ui_CustomWidget`** → `QWidget` type annotation
- **`Ui_SettingsFrame`** → `QFrame` type annotation

### **Main Advantages:**
- ✅ **Anki Compatible Imports**: Use `from aqt.qt import ...` instead of `from PyQt6 import ...`
- ✅ **Intelligent Type Inference**: Automatically determine correct Qt widget types
- ✅ **mypy Compatible**: Generated code passes strict type checking
- ✅ **Minimized Imports**: Only import classes actually used in UI files
- ✅ **Automatic Resource Copying**: Resource files automatically copied to final package
- ✅ **Clean References**: No need for complex QRC compilation
- ✅ **Direct File Paths**: Use standard file paths in Python code
- ✅ **Development Friendly**: Resources immediately available for testing

## Code Quality

AADT includes modern development tools, strongly recommended for use during development to improve code quality and type safety, providing complete type annotations:

```bash
# Use ruff for code checking
ruff check aadt/
ruff format aadt/

# Use mypy for type checking
mypy aadt/

# Use ty for fast type checking (recommended for development)
./scripts/ty-check.sh
# or manually:
uv run ty check src/ --extra-search-path src/

# Run all checks
ruff check aadt/ && mypy aadt/
```

**Note**: ty is a fast type checker that works well with src-layout projects. Use the provided script for convenience.

## Unit Testing

```bash
# Run tests
pytest

# Include coverage
pytest --cov=aadt
```

## 🚀 Git Integration

AADT is designed to work best in Git repositories, but **Git is not required**:

### When Git is Available (Recommended)
- **Version Detection**: Use Git tags and commits for version control
- **Source Archiving**: Use `git archive` for clean source extraction
- **Modification Time**: Use Git commit timestamps

### Non-Git Environment (Fallback Mode)
- **Version Detection**: Read from `pyproject.toml`, `VERSION` files, or generate timestamp-based versions
- **Source Archiving**: Copy current directory with intelligent exclusion (`.git`, `__pycache__`, etc.)
- **Modification Time**: Use current timestamp

### Usage Examples

```bash
# In Git repository (auto-detection)
aadt build -d local

# In non-Git directory (auto-fallback)
aadt build -d local  # Still works!

# Explicit version specification (works anywhere)
aadt build v1.2.0 -d local
```

The tool automatically detects your environment and chooses the appropriate method.

## 📚 Examples

Check the `tests/` directory for example configurations and usage patterns.

## 🎯 Design Philosophy

AADT follows these principles:

1. **Modern Python First**: Use latest language features (3.12+)
2. **Type Safety**: Complete type annotations and mypy validation
3. **Qt6 Focus**: No legacy Qt5 baggage, designed for current Anki
4. **Fast Build**: uv-based dependency management
5. **Developer Experience**: Clear CLI, good error messages, useful validation

## 📄 License

This project is licensed under the GNU AGPLv3 License. See the [LICENSE](LICENSE) file for details.

---

**Built with ❤️ for the Anki Community**

> This project is inspired by the [aab](https://github.com/glutanimate/anki-addon-builder) project, focusing on providing the best development experience for new version Anki add-on developers who are about to officially launch.

---

# 中文版

**现代化的、AI 驱动的、专注于 Anki 新版本（2025.06+）的插件开发和构建工具包，具备完整类型安全和现代 Python 实践。**

[English](#anki-add-on-dev-toolkit-aadt) | 中文

## 🚀 特性

- **Python 3.13** 与 Anki 2025.06+ 保持一致
- **Qt6 专用支持** 适配 Anki 2025.06+ 版本  
- **优雅依赖管理** 完全基于 uv 管理环境和依赖
- **代码质量工具** 集成 ruff 和 ty 提升代码质量
- **全面的 CLI 命令** 覆盖从初始化到发布的全流程
- **便捷构建和分发** 支持 AnkiWeb 和本地分发

## 📋 目录

- [前置要求](#前置要求)
- [快速开始](#快速开始)
- [命令详解](#命令详解)
- [CI/CD支持](#CI/CD支持)
- [UI开发](#UI开发)
- [代码质量](#代码质量)
- [单元测试](#单元测试)
- [Git 集成](#Git集成)
- [更新日志](#更新日志)
- [协议](#协议)

## 🔧 前置要求

通过 `curl -LsSf https://astral.sh/uv/install.sh | sh` 在本地安装 uv。

## ⚡ 快速开始

### 1. 初始化插件项目

使用 `uvx` 方式使用最新版本运行 `init` 命令快速初始化项目：

```bash
# 创建目录
mkdir my-addon
cd my-addon

# 交互式设置
uvx aadt init
```

默认的初始化会创建一个基础但完整的插件项目，包括：

- 通过交互方式搜集插件信息
- 应用模板文件，生成项目结构
- 通过 uv 配置开发环境并安装依赖
- 创建 git 仓库并初始化

初始化完成之后，项目的目录结构如下：

```
my_addon/
├── addon.json          # Addon 配置文件
├── src/                # 源代码
│   └── my_addon/       # 主模块
│       └── __init__.py # 主模块初始化文件
├── ui/                 # UI 设计
│   ├── designer/       # Qt Designer .ui 文件
│   └── resources/      # UI 资源（图标、样式）
├── README.md           # 项目说明
├── ANKI.md             # Anki 核心库详解
├── pyproject.toml      # 项目配置
├── uv.lock             # uv 锁定文件
├── .python-version     # 指定Python版本
├── .git/               # Git仓库
└── .gitignore          # 忽略文件

```

### 2. 开发

为提升 Addon 开发效率，强烈建议在开发过程中使用 AI 辅助编程。AADT 提供了 `claude` 命令来生成专门的 Claude Code 指引文件：

```bash
# 生成 CLAUDE.md 文件
aadt claude
```

这个命令会根据你的项目配置，在根目录下生成一个 CLAUDE.md 文件，其中包括了 Anki 25.06+ Addon 开发的核心指引，能帮助 Claude AI 更好地理解你的项目并提供精准的开发建议。

此外，还会在根目录下生成一个 ANKI.md 文件，其中包含现代 Anki 25.06+ 的源代码详细分析和最佳实践的详细文档，帮助 AI 和人类程序员更好地理解 Anki 的整体架构和开发方式。

### 3. 测试

为了方便开发环境下的测试，AADT 提供了 `test` 命令，用于在 Anki 中进行插件的测试。

```bash
aadt test
```

运行 `test` 命令会先将 `src/` 目录下的项目文件夹软链接到 Anki 的插件目录，然后自动启动 Anki 并加载插件。

同时，AADT 还提供了 `link` 命令，用于手动管理项目源代码文件夹软链接到 Anki 插件目录的操作。

```bash
# 创建软链接
aadt link

# 删除软链接
aadt link --unlink
```

### 4. 构建

AADT 提供了 `build` 命令，用于构建插件。

```bash
aadt build
```

构建命令依赖于 git 仓库，默认会查找最新的 git tag 并构建对应的 commit 版本，便于将测试版本和正式版本区分。

生成的插件包会存储在 `dist` 目录下，可以用于直接安装或者上传到 AnkiWeb 进行分发。

## 🔧 命令详解

### `init` - 初始化插件项目
```bash
# 在当前目录初始化（交互式）
aadt init

# 在指定目录初始化
aadt init my-addon

# 使用默认值（非交互式）
aadt init -y
```

**功能：**
- 交互式收集插件信息（名称、作者、描述等）
- 生成完整的项目结构和应用模板生成文件
- 使用 uv配置 Python 环境和依赖管理
- 初始化 Git 仓库

### `ui` - 编译用户界面
```bash
# 编译所有 UI 文件
aadt ui
```

**功能：**
- 编译 `ui/designer/` 中的 `.ui` 文件到 `src/模块名/gui/forms/qt6/`
- 自动复制 `ui/resources/` 中的资源文件到 `src/模块名/gui/resources/`
- 支持图标、样式表等各种资源文件

### `test` - 启动测试
```bash
# 链接插件并启动 Anki 测试
aadt test
```

**功能：**
- 自动执行 `aadt link` 创建软链接
- 启动 Anki 程序加载插件
- 一键测试工作流

### `link` - 开发环境链接
```bash
# 创建软链接到 Anki 插件目录
aadt link

# 删除软链接
aadt link --unlink
```

**功能：**
- 将 `src/` 下的插件项目文件夹软链接到 Anki 插件目录
- 方便开发期间启动 Anki 实例进行实时测试

### `claude` - 生成 Claude AI 助手记忆文件
```bash
# 生成 CLAUDE.md 文件
aadt claude

# 强制覆盖现有 CLAUDE.md 文件
aadt claude --force
```

**功能：**
- 根据项目 `addon.json` 配置自动生成 `CLAUDE.md` 文件
- 包含现代 Anki 25.06+ 开发最佳实践和指导
- 防止意外覆盖现有文件，支持 `--force` 强制覆盖

### `build` - 构建和打包插件
```bash
# 构建最新标签版本（默认）
aadt build

# 构建特定版本
aadt build v1.2.0        # 特定 git 标签
aadt build dev           # 工作目录（包含未提交更改）
aadt build current       # 最新提交
aadt build release       # 最新标签（默认）

# 指定分发类型
aadt build -d local      # 本地开发版本
aadt build -d ankiweb    # AnkiWeb 提交版本
aadt build -d all        # 同时构建两种类型

# 组合使用
aadt build v1.2.0 -d local
```

**分发类型说明：**
- `local`: 适用于本地开发，保留调试信息
- `ankiweb`: 适用于 AnkiWeb 提交，优化文件大小
- `all`: 同时生成两种版本

**功能：**
- 根据 `addon.json` 配置生成 AnkiWeb 所需的 `manifest.json`
- 包含插件元数据、依赖关系等信息

### `manifest` - 生成清单文件
```bash
# 生成 manifest.json
aadt manifest
```

### `clean` - 清理构建文件
```bash
# 清理所有构建产物
aadt clean
```

**功能：**
- 删除 `dist/` 目录及其内容
- 清理临时文件和缓存

## 🚀 CI/CD 支持

这些命令提供更精细的构建控制，适用于自动化构建流水线：

### `create_dist` - 准备源代码树
```bash
aadt create_dist [version]
```

**功能：**
- 准备源代码树到 `dist/build` 目录
- 处理版本控制和文件归档
- 为后续构建步骤做准备

#### `build_dist` - 构建源代码
```bash
aadt build_dist
```

**功能：**
- 处理 `dist/build` 中的源代码
- 编译 UI 文件，生成清单文件
- 执行所有必要的代码后处理

#### `package_dist` - 打包分发
```bash
aadt package_dist
```

**功能：**
- 将构建好的文件打包成 `.ankiaddon` 格式
- 生成最终的分发包

## 🎨 UI 开发

### 使用 Qt Designer

AADT 为 Qt Designer UI 开发提供无缝集成，具备**智能 PyQt6 到 aqt.qt 转换**功能：

1. **设计UI**: 在 `ui/designer/` 中创建 `.ui` 文件
2. **添加资源**: 将图片、图标放在 `ui/resources/` 中
3. **引用资源**: 在 Qt Designer 中引用 `ui/resources/` 中的文件
4. **构建UI**: 运行 `aadt ui` 自动编译并复制资源

```bash
# 你的项目结构
my-addon/
├── ui/
│   ├── designer/
│   │   └── dialog.ui          # 引用 ../resources/icon.png
│   └── resources/
│       └── icon.png           # 你的资源文件
└── src/my_addon/

# 运行 'aadt ui' 后
my-addon/
├── src/my_addon/
│   ├── gui/forms/qt6/
│   │   └── dialog.py          # 编译后的UI，使用aqt.qt导入
│   └── resources/
│       └── icon.png           # 自动复制的资源
```

### 🧠 智能 PyQt6 到 aqt.qt 转换

在转化的过程中，AADT 自动将 pyuic6 输出转换为 Anki 兼容格式，并提供精确的类型注解：

**原始转化 (pyuic6 输出):**
```python
from PyQt6 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.label = QtWidgets.QLabel(Dialog)
        # ...
```

**专用转化 (AADT 智能转换):**
```python
from aqt.qt import QDialog, QVBoxLayout, QLabel, QMetaObject

class Ui_Dialog(object):
    def setupUi(self, Dialog: QDialog) -> None:
        Dialog.setObjectName("Dialog")
        self.verticalLayout = QVBoxLayout(Dialog)
        self.label = QLabel(Dialog)
        # ...
```

### 🎯 智能类型推断

AADT 分析你的 UI 文件，基于 aqt.qt 的实际类型系统提供**精确的类型注解**：

- **`Ui_Dialog`** → `QDialog` 类型注解
- **`Ui_MainWindow`** → `QMainWindow` 类型注解  
- **`Ui_CustomWidget`** → `QWidget` 类型注解
- **`Ui_SettingsFrame`** → `QFrame` 类型注解

### **主要优势：**
- ✅ **Anki 兼容导入**: 使用 `from aqt.qt import ...` 替代 `from PyQt6 import ...`
- ✅ **智能类型推断**: 自动确定正确的 Qt 控件类型
- ✅ **mypy 兼容**: 生成的代码通过严格类型检查
- ✅ **最小化导入**: 只导入 UI 文件中实际使用的类
- ✅ **自动资源复制**: 资源文件自动复制到最终包中
- ✅ **清洁引用**: 无需复杂的QRC编译
- ✅ **直接文件路径**: 在Python代码中使用标准文件路径
- ✅ **开发友好**: 资源立即可用于测试

## 代码质量

AADT 包含现代开发工具，强烈建议在开发过程中使用，提升代码质量和类型安全，并提供完整的类型注解：

```bash
# 使用ruff进行代码检查
ruff check aadt/
ruff format aadt/

# 使用mypy进行类型检查  
mypy aadt/

# 运行所有检查
ruff check aadt/ && mypy aadt/
```

## 单元测试

```bash
# 运行测试
pytest

# 包含覆盖率
pytest --cov=aadt
```

## 🚀 Git 集成

AADT 设计为在 Git 仓库中工作最佳，但**不需要 Git**：

### Git 可用时（推荐）
- **版本检测**: 使用 Git 标签和提交进行版本控制
- **源码归档**: 使用 `git archive` 进行干净的源码提取
- **修改时间**: 使用 Git 提交时间戳

### 非Git环境（降级模式）
- **版本检测**: 从 `pyproject.toml`、`VERSION` 文件读取，或生成基于时间戳的版本
- **源码归档**: 复制当前目录并智能排除（`.git`、`__pycache__` 等）
- **修改时间**: 使用当前时间戳

### 使用示例

```bash
# 在 Git 仓库中（自动检测）
aadt build -d local

# 在非 Git 目录中（自动降级）
aadt build -d local  # 仍然可以工作！

# 显式版本指定（任何地方都可以工作）
aadt build v1.2.0 -d local
```

工具会自动检测你的环境并选择适当的方法。

## 📚 示例

查看 `tests/` 目录获取示例配置和使用模式。

## 📄 协议

本项目基于GNU AGPLv3协议。详见[LICENSE](LICENSE)文件。

---

**为Anki社区用❤️构建**

> 本项目受 [aab](https://github.com/glutanimate/anki-addon-builder) 项目启发，专注于为即将正式上线的新版 Anki 插件开发者提供最佳的开发体验。
