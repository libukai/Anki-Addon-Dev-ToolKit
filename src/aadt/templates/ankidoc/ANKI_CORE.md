# 📖 Anki 插件开发核心概念

本文档提供 Anki 25.06+ 插件开发的核心概念和基础代码模式。

## 1. Anki 插件架构概览

### 基本组件
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   插件代码   │ ──► │  aqt (GUI)  │ ──► │ anki (Core) │
│  (Python)   │     │   (Qt6)     │     │   (Rust)    │
└─────────────┘     └─────────────┘     └─────────────┘
```

### 工作原理
- **anki 包**: 核心数据库操作，提供 Collection 类和 139+ 个方法
- **aqt 包**: Qt6 GUI 层，提供用户界面和事件处理
- **插件层**: Python 代码，通过 aqt 与 anki 核心交互

### 核心对象
- `mw` - 主窗口对象，所有操作的入口点
- `mw.col` - Collection 对象，数据库访问接口
- `gui_hooks` - 事件钩子系统
- `mw.addonManager` - 插件管理器

## 2. 导入规则和基础概念

### 标准导入模式
```python
# 基础导入 - 所有插件必须包含
from aqt import mw, gui_hooks
from aqt.qt import *  # Qt6兼容层 - 永远不要直接导入PyQt6
from aqt.utils import showInfo, showWarning, askUser, tooltip
from aqt.operations import CollectionOp, QueryOp

# 数据类型导入
from anki.collection import Collection, OpChanges, SearchNode
from anki.notes import Note, NoteId
from anki.cards import Card, CardId
from anki.decks import DeckId
from anki.errors import NotFoundError, InvalidInput, NetworkError
```

### 禁止使用的导入
```python
# ❌ 直接 PyQt6 导入（会导致兼容性问题）
from PyQt6.QtWidgets import QDialog, QPushButton

# ❌ 旧版钩子系统（已废弃）
from anki.hooks import addHook, runHook

# ❌ 手动线程管理（使用 CollectionOp/QueryOp 替代）
import threading
```

### mw 对象核心属性
```python
mw.col              # Collection 数据库对象
mw.reviewer         # 复习界面控制器
mw.deckBrowser      # 牌组浏览器
mw.addonManager     # 插件管理器
mw.taskman          # 异步任务管理器
mw.state            # 当前 UI 状态
```

## 3. CollectionOp/QueryOp 操作模式

### CollectionOp - 数据库修改操作
用于任何会改变数据库状态的操作，确保撤销功能正常。

```python
def database_modification_pattern():
    def op(col: Collection) -> OpChanges:
        # 数据库修改操作
        note = col.get_note(note_id)
        note["字段"] = "新值"
        return col.update_note(note)
    
    CollectionOp(
        parent=mw,  # 父窗口对象
        op=op       # 操作函数
    ).success(
        lambda changes: showInfo("操作成功")
    ).failure(
        lambda exc: showWarning(f"操作失败: {exc}")
    ).run_in_background()
```

### QueryOp - 只读查询操作
用于不修改数据库的查询操作，可以并行执行。

```python
def read_only_query_pattern():
    def op(col: Collection) -> list[NoteId]:
        # 只读查询操作
        search = col.build_search_string(SearchNode(deck="目标牌组"))
        return list(col.find_notes(search))
    
    QueryOp(
        parent=mw,
        op=op,
        success=lambda note_ids: process_results(note_ids)
    ).with_progress("搜索中...").run_in_background()
```

### 网络与数据库分离模式
网络请求和数据库操作必须分离，避免阻塞数据库访问。

```python
def network_database_separation_pattern():
    # 阶段1: 网络请求（uses_collection=False）
    def fetch_data() -> dict:
        from anki.httpclient import HttpClient
        with HttpClient() as client:
            response = client.get(api_url)
            return json.loads(client.stream_content(response))
    
    # 阶段2: 数据库更新
    def update_database(data: dict):
        def op(col: Collection) -> OpChanges:
            # 使用网络数据更新数据库
            return col.update_note(note)
        CollectionOp(parent=mw, op=op).run_in_background()
    
    # 执行分离模式
    mw.taskman.with_progress(
        task=fetch_data,
        on_done=lambda fut: update_database(fut.result()),
        uses_collection=False  # 关键：网络阶段不使用数据库
    )
```

## 4. 基础代码片段

### 1. 菜单项添加
```python
def add_menu_item():
    def on_main_window_ready():
        action = QAction("我的插件", mw)
        action.triggered.connect(show_plugin_dialog)
        mw.form.menuTools.addAction(action)
    
    gui_hooks.main_window_did_init.append(on_main_window_ready)
```

### 2. 创建笔记
```python
def create_note_pattern(deck_name: str, fields: dict[str, str]):
    def op(col: Collection) -> OpChanges:
        deck_id = col.decks.id(deck_name, create=True)
        model = col.models.by_name("Basic")
        if not model:
            raise NotFoundError("Basic 笔记类型未找到")
        
        note = col.new_note(model)
        for field, value in fields.items():
            if field in note:
                note[field] = value
        
        return col.add_note(note, deck_id)
    
    CollectionOp(parent=mw, op=op).success(
        lambda _: showInfo("笔记创建成功")
    ).run_in_background()
```

### 3. 搜索笔记
```python
def search_notes_pattern(deck_name: str, tag: str):
    def op(col: Collection) -> list[NoteId]:
        search = col.build_search_string(
            SearchNode(deck=deck_name),
            SearchNode(tag=tag)
        )
        return list(col.find_notes(search))
    
    QueryOp(
        parent=mw,
        op=op,
        success=lambda ids: showInfo(f"找到 {len(ids)} 个笔记")
    ).run_in_background()
```

### 4. 批量操作（单一撤销点）
```python
def batch_operation_pattern(note_ids: list[NoteId]):
    def op(col: Collection) -> OpChanges:
        # 创建单一撤销点
        pos = col.add_custom_undo_entry("批量操作")
        
        for nid in note_ids:
            note = col.get_note(nid)
            # 处理笔记...
            note["字段"] = "新值"
            col.update_note(note, skip_undo_entry=True)
        
        # 合并撤销记录
        return col.merge_undo_entries(pos)
    
    CollectionOp(parent=mw, op=op).with_progress().run_in_background()
```

### 5. 对话框显示
```python
def dialog_pattern():
    class MyDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("插件对话框")
            self.setModal(True)
            self.setup_ui()
        
        def setup_ui(self):
            layout = QVBoxLayout()
            self.input = QLineEdit()
            btn = QPushButton("确定")
            btn.clicked.connect(self.accept)
            
            layout.addWidget(QLabel("请输入:"))
            layout.addWidget(self.input)
            layout.addWidget(btn)
            self.setLayout(layout)
    
    dialog = MyDialog(mw)
    if dialog.exec():  # 使用 exec() 而非 show()
        result = dialog.input.text()
```

### 6. 网络请求
```python
def network_request_pattern(url: str, data: dict):
    def fetch() -> dict:
        from anki.httpclient import HttpClient
        with HttpClient() as client:
            client.timeout = 30
            response = client.post(url, json.dumps(data).encode(), headers)
            if response.status_code != 200:
                raise NetworkError(f"HTTP {response.status_code}")
            return json.loads(client.stream_content(response))
    
    mw.taskman.with_progress(
        task=fetch,
        on_done=lambda fut: process_response(fut.result()),
        label="请求中...",
        uses_collection=False
    )
```

### 7. 配置管理
```python
def config_management_pattern():
    # 读取配置
    def get_config() -> dict:
        return mw.addonManager.getConfig(__name__) or {}
    
    # 保存配置
    def save_config(config: dict):
        mw.addonManager.writeConfig(__name__, config)
    
    # 使用配置
    config = get_config()
    setting_value = config.get("my_setting", "default_value")
```

### 8. 钩子管理
```python
def hook_management_pattern():
    def on_collection_loaded(col: Collection):
        # 集合加载后的初始化
        pass
    
    def on_state_change(new_state: str, old_state: str):
        if new_state == "review":
            # 进入复习模式
            pass
    
    # 注册钩子
    gui_hooks.collection_did_load.append(on_collection_loaded)
    gui_hooks.state_did_change.append(on_state_change)
    
    # 清理钩子（插件卸载时）
    def cleanup():
        gui_hooks.collection_did_load.remove(on_collection_loaded)
        gui_hooks.state_did_change.remove(on_state_change)
```

### 9. 错误处理
```python
def error_handling_pattern():
    try:
        # 可能失败的操作
        if not mw.col:
            raise RuntimeError("Collection 未加载")
        
        note = mw.col.get_note(note_id)
        
    except NotFoundError:
        showWarning("笔记未找到")
    except InvalidInput as e:
        showWarning(f"输入错误: {e}")
    except NetworkError as e:
        showWarning(f"网络错误: {e}")
    except Exception as e:
        logger = mw.addonManager.get_logger(__name__)
        logger.exception("未预期的错误")
        showWarning(f"操作失败: {e}")
```

### 10. 日志记录
```python
def logging_pattern():
    # 获取插件专用日志器
    logger = mw.addonManager.get_logger(__name__)
    
    # 不同级别的日志
    logger.debug("调试信息")
    logger.info("普通信息")
    logger.warning("警告信息")
    logger.error("错误信息")
    logger.exception("异常信息", exc_info=True)
    
    # 用户提示（与日志分离）
    showInfo("操作成功")      # 成功提示
    showWarning("警告信息")   # 警告提示
    tooltip("快速提示", 2000) # 临时提示
```

---

## 核心原则总结

1. **始终从 aqt.qt 导入** Qt 组件，保证兼容性
2. **使用 CollectionOp** 处理数据库修改，确保撤销功能
3. **使用 QueryOp** 处理只读查询，提高性能
4. **网络与数据库分离**，`uses_collection=False` 用于网络请求
5. **单一撤销点** 用于批量操作，提供良好的用户体验
6. **错误处理** 使用 Anki 特定异常类型
7. **配置管理** 使用 AddonManager 的标准API
8. **生命周期管理** 正确注册和清理钩子
9. **UI 最佳实践** 模态对话框使用 exec()，管理对象生命周期
10. **日志系统** 使用 Anki 内置日志，避免自定义 Qt 信号连接

这些核心概念和代码模式涵盖了 Anki 插件开发的 90% 常见场景，为开发者提供了可直接使用的模板和最佳实践。