# 🎯 Anki 插件开发 - AI 导航中心

专为 Claude Code 优化的 Anki 插件开发文档体系。基于 Anki 25.06+，采用 Qt6 + Python 3.13。

## 📍 按需求快速定位

### 🆕 我是新开项目 → @ankidoc/ANKI_CORE.md
- Anki 插件架构概览
- 必知的导入规则和基础概念
- CollectionOp/QueryOp 操作模式
- 5分钟上手代码片段

### 🔍 我要查API → @ankidoc/ANKI_API.md  
- 按功能分组的完整 API 索引
- 每个API的参数、返回值、示例代码
- 高频使用的API优先排序

### 💡 我要写代码 → @ankidoc/ANKI_PATTERNS.md
- 常用代码模式和模板
- 直接可复制的代码片段
- UI开发、数据库操作、配置管理等场景

### ⚠️ 我遇到问题 → @ankidoc/ANKI_TROUBLESHOOTING.md
- 问题→解决方案映射表
- 常见错误和修复方法
- 调试技巧和性能优化

### 📂 我要看示例 → @ankidoc/examples/
- `basic_operations.py` - 基础插件操作
- `ui_development.py` - Qt6 UI开发
- `advanced_features.py` - 高级功能实现

## 🚀 开发工作流

```
1. 新功能开发: ANKI_CORE.md → ANKI_PATTERNS.md → examples/
2. API查询: ANKI_API.md (按功能快速定位)
3. 问题解决: ANKI_TROUBLESHOOTING.md (错误→方案)
4. 代码审查: ANKI_PATTERNS.md (检查最佳实践)
```

## 🔧 关键技术要点

- **导入**: 始终从 `aqt.qt` 导入 Qt 组件
- **数据库**: 使用 `CollectionOp` 进行所有数据库操作  
- **异步**: 网络请求与数据库操作分离
- **日志**: `mw.addonManager.get_logger(__name__)`
- **配置**: 创建 `config.json` 并使用 `mw.addonManager.getConfig()`
