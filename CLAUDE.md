# Claude AI Assistant Memory - AADT 项目开发

本文档为 Claude Code 提供 Anki Add-on Developer Tools (AADT) 项目的开发指导和上下文信息。

## 项目概述

**AADT** 是一个现代化的 Anki 插件开发工具包，专为 Anki 2025.06+ 版本设计，提供完整的插件开发、构建和分发工具链。

请在开发过程中遵循以下原则：

1. **现代Python优先**: 使用 Python 3.13+ 特性，完整类型注解
2. **Qt6专用**: 仅支持 Qt6，通过 `aqt.qt` 导入
3. **uv工具链**: 所有操作使用 uv 命令，不使用 pip/poetry
4. **类型安全**: 使用 `ty` 进行类型检查，确保代码质量
5. **代码规范**: 使用 `ruff` 进行代码检查和格式化

## 开发决策原则

1. **功能实现** > 技术完美
2. **简单可靠** > 复杂优雅  
3. **易于维护** > 展示技巧
4. **满足需求** > 过度设计

## 技术栈

### 核心工具
- **Python 3.13**: 项目最低要求版本，使用现代语法特性
- **src-layout**: 采用 `src/aadt/` 结构的最佳实践项目布局
- **uv**: 现代 Python 包管理器，替代 pip/poetry
- **ruff**: 快速代码检查和格式化工具 (line-length=120)
- **ty**: 快速类型检查器，替代 mypy

### 核心依赖
- **jsonschema>=4.4.0**: 配置文件验证
- **whichcraft>=0.6.1**: 跨平台命令检测
- **questionary>=2.1.0**: 交互式命令行界面

### 开发依赖 (dev组)
- **anki>=25.6b7**: Anki 核心库
- **aqt>=25.6b7**: Anki Qt 界面库  
- **pytest>=8.3.4**: 测试框架
- **pytest-cov>=6.0.0**: 覆盖率测试
- **pytest-mock>=3.14.0**: Mock 测试工具

## 代码质量标准

### 代码检查命令
```bash
# 代码风格检查和自动修复
uv run ruff check src/aadt/
uv run ruff format src/aadt/

# 类型检查
uv run ty check src/aadt/

# 运行测试
uv run pytest

# 组合检查
uv run ruff check src/aadt/ && uv run ty check src/aadt/
```

### 配置要点
- **行长度**: 120 字符 (pyproject.toml配置)
- **类型覆盖**: 所有函数必须有类型注解
- **测试覆盖**: 最低 20% 覆盖率要求
- **复杂度**: McCabe 复杂度不超过 10

## 项目结构

```
aadt/                           # AADT项目根目录
├── src/aadt/                   # 主包源代码 (src-layout)
│   ├── __init__.py             # 包初始化和版本信息
│   ├── cli.py                  # 命令行接口 (~350 LOC)
│   ├── config.py               # 配置管理 (~166 LOC)
│   ├── builder.py              # 构建系统 (~193 LOC)
│   ├── ui.py                   # UI编译 (~326 LOC)
│   ├── init.py                 # 项目初始化 (~180 LOC)
│   ├── run.py                  # 运行和链接 (~160 LOC)
│   ├── git.py                  # Git集成 (~120 LOC)
│   ├── manifest.py             # 清单生成 (~124 LOC)
│   ├── utils.py                # 工具函数 (~90 LOC)
│   ├── schema.json             # 配置验证架构
│   └── templates/              # 项目模板文件
├── tests/                      # 测试文件
├── pyproject.toml              # 项目配置和依赖
├── .python-version             # Python 3.13
├── uv.lock                     # uv锁定文件
├── README.md                   # 项目文档
└── CLAUDE.md                   # 本文件
```

## 开发工作流

### 环境设置
```bash
# 安装所有依赖
uv sync --group dev

# 激活虚拟环境 (如需要)
source .venv/bin/activate
```

### 开发命令
```bash
# 运行CLI (开发模式)
uv run aadt --help

# 代码质量检查
uv run ruff check src/aadt/ && uv run ty check src/aadt/

# 运行测试
uv run pytest

# 自动格式化代码
uv run ruff format src/aadt/
```

### 发布流程
```bash
# 更新版本 (使用内置uv version命令)
uv version patch    # 1.0.0 → 1.0.1
uv version minor    # 1.0.0 → 1.1.0  
uv version major    # 1.0.0 → 2.0.0

# 构建项目
uv build
```

## 架构特点

### 现代Python特性
- **类型注解**: 所有函数都有完整类型注解
- **dataclass**: 配置使用dataclass而非dict
- **pathlib**: 文件操作使用Path对象
- **现代语法**: `str | None` 而非 `Optional[str]`

### 错误处理
- **异常链**: 使用 `raise ... from e` 保留原始错误
- **自定义异常**: 定义专用异常类型
- **用户友好**: CLI错误信息清晰易懂

### 性能优化
- **并发工具调用**: 支持并行执行多个工具
- **缓存**: 合理使用缓存避免重复计算
- **快速工具**: 使用ty而非mypy提升类型检查速度

## UI开发特点

### 资源管理现代化
- **importlib.resources**: 自动生成支持现代资源管理的 `__init__.py`
- **路径复制**: 从 `ui/resources/` 到 `src/module/gui/resources/`
- **包结构**: 自动创建Python包结构支持.zip分发

### Qt6专用
- **无Qt5遗留**: 仅支持Qt6，代码简洁无历史包袱
- **aqt.qt导入**: 自动转换PyQt6导入为Anki兼容的aqt.qt导入
- **类型注解**: 生成的UI代码包含完整类型注解
