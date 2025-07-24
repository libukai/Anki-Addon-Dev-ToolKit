# 🔍 Anki 插件开发 API 速查表

按功能分组、使用频率排序的完整 API 索引。基于 Anki 25.06+，支持 Qt6。

## 📋 核心对象概览

### mw (MainWindow) 主要属性
```python
mw.col: Collection           # 数据库访问接口
mw.addonManager             # 插件管理器
mw.taskman: TaskManager     # 异步任务管理
mw.reviewer                 # 复习界面控制器
mw.deckBrowser             # 牌组浏览器
mw.state: str              # 当前UI状态 ("startup", "deckBrowser", "overview", "review")
mw.form                    # UI表单对象
```

### Collection 类型定义
```python
from anki.collection import Collection, OpChanges, SearchNode
from anki.notes import Note, NoteId
from anki.cards import Card, CardId
from anki.decks import DeckId
from anki.models import NotetypeId
```

---

## 📝 笔记操作 (高频API)

### 创建笔记
```python
# 获取笔记类型
col.models.by_name(name: str) -> NotetypeDict | None
col.models.all() -> list[NotetypeDict]

# 创建新笔记
col.new_note(notetype: NotetypeDict) -> Note
col.add_note(note: Note, deck_id: DeckId) -> OpChanges

# 示例：创建笔记
def create_note(col: Collection, deck_name: str, fields: dict[str, str]):
    deck_id = col.decks.id(deck_name, create=True)
    notetype = col.models.by_name("Basic")
    note = col.new_note(notetype)
    
    for field, value in fields.items():
        if field in note:
            note[field] = value
    
    return col.add_note(note, deck_id)
```

### 查询笔记
```python
# 获取笔记
col.get_note(note_id: NoteId) -> Note
col.find_notes(search: str) -> Sequence[NoteId]

# 更新笔记
col.update_note(note: Note) -> OpChanges

# 示例：批量更新
def batch_update_notes(col: Collection, note_ids: list[NoteId], field: str, value: str):
    pos = col.add_custom_undo_entry("批量更新")
    
    for nid in note_ids:
        note = col.get_note(nid)
        note[field] = value
        col.update_note(note, skip_undo_entry=True)
    
    return col.merge_undo_entries(pos)
```

### 笔记字段操作
```python
# Note 对象方法
note[field_name]: str          # 获取/设置字段值
note.keys() -> list[str]       # 获取所有字段名
note.items() -> list[tuple]    # 获取字段名值对
note.note_type() -> NotetypeDict  # 获取笔记类型
note.cards() -> list[Card]     # 获取关联卡片
```

---

## 🃏 卡片操作

### 基础卡片API
```python
# 获取卡片
col.get_card(card_id: CardId) -> Card
col.find_cards(search: str) -> Sequence[CardId]

# 卡片属性
card.note() -> Note           # 获取关联笔记
card.question() -> str        # 获取问题面
card.answer() -> str          # 获取答案面
card.deck_id: DeckId         # 所属牌组ID
card.note_id: NoteId         # 关联笔记ID

# 示例：获取卡片信息
def get_card_info(col: Collection, card_id: CardId):
    card = col.get_card(card_id)
    note = card.note()
    return {
        "question": card.question(),
        "answer": card.answer(),
        "deck": col.decks.name(card.deck_id),
        "note_fields": dict(note.items())
    }
```

---

## 📚 牌组管理

### 牌组操作
```python
# 牌组基础操作
col.decks.id(name: str, create: bool = False) -> DeckId
col.decks.name(deck_id: DeckId) -> str
col.decks.all() -> list[DeckDict]
col.decks.all_names() -> list[str]

# 牌组配置
col.decks.get_config(config_id: int) -> DeckConfigDict
col.decks.save(deck: DeckDict) -> None

# 示例：创建牌组层次结构
def create_deck_hierarchy(col: Collection, parent: str, children: list[str]):
    parent_id = col.decks.id(parent, create=True)
    
    for child in children:
        child_name = f"{parent}::{child}"
        col.decks.id(child_name, create=True)
    
    return parent_id
```

---

## 🏷️ 标签操作

### 标签管理
```python
# 标签操作
col.tags.all() -> list[str]
col.tags.bulk_add(note_ids: list[NoteId], tags: str) -> OpChanges
col.tags.bulk_remove(note_ids: list[NoteId], tags: str) -> OpChanges

# 示例：标签批量管理
def manage_tags(col: Collection, note_ids: list[NoteId], add_tags: list[str], remove_tags: list[str]):
    changes = OpChanges()
    
    if add_tags:
        changes = col.tags.bulk_add(note_ids, " ".join(add_tags))
    
    if remove_tags:
        changes = col.tags.bulk_remove(note_ids, " ".join(remove_tags))
    
    return changes
```

---

## 🔍 搜索功能

### 搜索构建器
```python
# 搜索节点构建
from anki.collection import SearchNode

# 基础搜索
SearchNode(deck="牌组名")
SearchNode(tag="标签名")  
SearchNode(note="笔记内容")
SearchNode(field_name="字段内容")

# 复合搜索
col.build_search_string(*nodes: SearchNode) -> str

# 示例：复合搜索
def complex_search(col: Collection, deck: str, tag: str, content: str) -> list[NoteId]:
    search_string = col.build_search_string(
        SearchNode(deck=deck),
        SearchNode(tag=tag),
        SearchNode(note=content)
    )
    return list(col.find_notes(search_string))
```

### 搜索API
```python
# 查找操作
col.find_notes(search: str) -> Sequence[NoteId]
col.find_cards(search: str) -> Sequence[CardId]

# 统计信息
col.card_count(search: str) -> int
col.note_count(search: str) -> int
```

---

## ⚡ 异步操作

### CollectionOp - 数据库修改
```python
from aqt.operations import CollectionOp

# 基础模式
def perform_collection_op(operation_func, success_msg: str = "操作成功"):
    def op(col: Collection) -> OpChanges:
        return operation_func(col)
    
    CollectionOp(
        parent=mw,
        op=op
    ).success(
        lambda changes: showInfo(success_msg)
    ).failure(
        lambda exc: showWarning(f"操作失败: {exc}")
    ).run_in_background()

# 带进度条
CollectionOp(parent=mw, op=op).with_progress("处理中...").run_in_background()
```

### QueryOp - 只读查询
```python
from aqt.operations import QueryOp

# 查询模式
def perform_query_op(query_func, result_handler):
    def op(col: Collection):
        return query_func(col)
    
    QueryOp(
        parent=mw,
        op=op,
        success=result_handler
    ).with_progress("查询中...").run_in_background()

# 示例：异步搜索
def async_search_notes(search_term: str):
    def search_op(col: Collection) -> list[NoteId]:
        return list(col.find_notes(search_term))
    
    def handle_results(note_ids: list[NoteId]):
        showInfo(f"找到 {len(note_ids)} 个笔记")
    
    QueryOp(parent=mw, op=search_op, success=handle_results).run_in_background()
```

---

## 🪝 GUI钩子系统

### 生命周期钩子
```python
from aqt import gui_hooks

# 应用启动
gui_hooks.main_window_did_init.append(callback)
gui_hooks.collection_did_load.append(callback)
gui_hooks.profile_did_open.append(callback)

# 状态变化
gui_hooks.state_did_change.append(callback)  # (new_state, old_state)
gui_hooks.state_will_change.append(callback)

# 示例：状态监听
def on_state_change(new_state: str, old_state: str):
    if new_state == "review":
        # 进入复习模式
        setup_review_environment()
    elif new_state == "deckBrowser":
        # 返回牌组浏览器
        cleanup_review_environment()

gui_hooks.state_did_change.append(on_state_change)
```

### 复习相关钩子
```python
# 卡片显示
gui_hooks.card_will_show.append(callback)    # (text, card, kind)
gui_hooks.card_did_render.append(callback)   # (output, context)

# 答题处理
gui_hooks.reviewer_did_answer_card.append(callback)  # (reviewer, card, ease)

# 示例：自定义卡片渲染
def enhance_card_display(text: str, card: Card, kind: str) -> str:
    if kind == "reviewQuestion":
        # 在问题中添加自定义内容
        text += "<div id='custom-hint'>提示: 仔细思考</div>"
    return text

gui_hooks.card_will_show.append(enhance_card_display)
```

### UI相关钩子
```python
# 菜单和工具栏
gui_hooks.browser_menus_did_init.append(callback)
gui_hooks.deck_browser_did_render.append(callback)

# WebView相关
gui_hooks.webview_did_receive_js_message.append(callback)
```

---

## 🌐 网络请求

### HttpClient 使用
```python
from anki.httpclient import HttpClient
import json

# 基础网络请求模式
def make_http_request(url: str, data: dict = None, timeout: int = 30) -> dict:
    with HttpClient() as client:
        client.timeout = timeout
        
        if data:
            response = client.post(
                url, 
                json.dumps(data).encode(),
                headers={"Content-Type": "application/json"}
            )
        else:
            response = client.get(url)
            
        if response.status_code != 200:
            from anki.errors import NetworkError
            raise NetworkError(f"HTTP {response.status_code}")
            
        return json.loads(client.stream_content(response))

# 网络+数据库分离模式
def network_then_database_pattern(api_url: str, process_data_func):
    # 阶段1: 网络请求
    def fetch_data() -> dict:
        return make_http_request(api_url)
    
    # 阶段2: 数据库更新
    def update_database(data: dict):
        def op(col: Collection) -> OpChanges:
            return process_data_func(col, data)
        
        CollectionOp(parent=mw, op=op).run_in_background()
    
    # 执行分离操作
    mw.taskman.with_progress(
        task=fetch_data,
        on_done=lambda fut: update_database(fut.result()),
        uses_collection=False  # 关键参数
    )
```

### TaskManager API
```python
# 任务管理器
mw.taskman.with_progress(
    task=callable,              # 要执行的函数
    on_done=callback,           # 完成回调
    label="加载中...",          # 进度条文本
    uses_collection=False       # 是否使用数据库
)

# 示例：带错误处理的任务
def run_background_task(task_func, success_callback):
    def handle_completion(future):
        try:
            result = future.result()
            success_callback(result)
        except Exception as e:
            logger = mw.addonManager.get_logger(__name__)
            logger.exception("后台任务失败")
            showWarning(f"操作失败: {e}")
    
    mw.taskman.with_progress(
        task=task_func,
        on_done=handle_completion,
        label="处理中..."
    )
```

---

## 🔧 配置管理

### AddonManager 配置API
```python
# 配置操作
mw.addonManager.getConfig(__name__) -> dict | None
mw.addonManager.writeConfig(__name__, config: dict) -> None

# 配置管理器
class ConfigManager:
    def __init__(self, addon_name: str):
        self.addon_name = addon_name
        self.default_config = {
            "api_key": "",
            "timeout": 30,
            "auto_sync": True
        }
    
    def get_config(self) -> dict:
        config = mw.addonManager.getConfig(self.addon_name)
        if config is None:
            config = self.default_config.copy()
            self.save_config(config)
        return config
    
    def save_config(self, config: dict) -> None:
        mw.addonManager.writeConfig(self.addon_name, config)
    
    def get_setting(self, key: str, default=None):
        return self.get_config().get(key, default)
    
    def set_setting(self, key: str, value) -> None:
        config = self.get_config()
        config[key] = value
        self.save_config(config)

# 使用示例
config_manager = ConfigManager(__name__)
api_key = config_manager.get_setting("api_key", "default_key")
```

---

## 🎨 UI组件

### 对话框基础
```python
from aqt.qt import *

class BaseDialog(QDialog):
    def __init__(self, parent=None, title="对话框"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 内容区域
        self.content_layout = QVBoxLayout()
        layout.addLayout(self.content_layout)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        self.ok_btn = QPushButton("确定")
        self.cancel_btn = QPushButton("取消")
        
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def add_widget(self, widget: QWidget):
        self.content_layout.addWidget(widget)
```

### 常用控件
```python
# 输入控件
line_edit = QLineEdit()
text_edit = QTextEdit()
combo_box = QComboBox()
spin_box = QSpinBox()
check_box = QCheckBox("选项")

# 布局管理
vbox = QVBoxLayout()      # 垂直布局
hbox = QHBoxLayout()      # 水平布局
grid = QGridLayout()      # 网格布局
form = QFormLayout()      # 表单布局

# WebView组件
from aqt.webview import AnkiWebView

class CustomWebView(AnkiWebView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.set_bridge_command(self.on_bridge_cmd, parent=parent)
    
    def on_bridge_cmd(self, cmd: str) -> bool:
        if cmd.startswith("custom:"):
            # 处理自定义命令
            return True
        return False
```

---

## 🚨 异常处理

### Anki 异常类型
```python
from anki.errors import (
    NotFoundError,      # 未找到资源
    InvalidInput,       # 无效输入
    NetworkError,       # 网络错误
    Interrupted,        # 操作被中断
    DBError            # 数据库错误
)

# 标准异常处理模式
def safe_operation(operation_func):
    try:
        return operation_func()
    except NotFoundError as e:
        showWarning(f"未找到: {e}")
    except InvalidInput as e:
        showWarning(f"输入错误: {e}")
    except NetworkError as e:
        showWarning(f"网络错误: {e}")
    except Exception as e:
        logger = mw.addonManager.get_logger(__name__)
        logger.exception("未预期的错误")
        showWarning(f"操作失败: {e}")
```

### 日志系统
```python
# 获取日志器
logger = mw.addonManager.get_logger(__name__)

# 日志级别
logger.debug("调试信息")
logger.info("普通信息")
logger.warning("警告信息")
logger.error("错误信息")
logger.exception("异常信息")  # 自动包含堆栈跟踪
```

---

## 🔄 生命周期管理

### 插件初始化和清理
```python
# __init__.py 模板
from aqt import mw, gui_hooks
from aqt.qt import *

class PluginManager:
    def __init__(self):
        self.hooks_registered = False
        self.register_hooks()
    
    def register_hooks(self):
        if not self.hooks_registered:
            gui_hooks.main_window_did_init.append(self.on_main_window_init)
            gui_hooks.collection_did_load.append(self.on_collection_loaded)
            self.hooks_registered = True
    
    def unregister_hooks(self):
        if self.hooks_registered:
            gui_hooks.main_window_did_init.remove(self.on_main_window_init)
            gui_hooks.collection_did_load.remove(self.on_collection_loaded)
            self.hooks_registered = False
    
    def on_main_window_init(self):
        # 主窗口初始化后的设置
        self.setup_menu()
    
    def on_collection_loaded(self, col):
        # 集合加载后的初始化
        pass
    
    def setup_menu(self):
        action = QAction("我的插件", mw)
        action.triggered.connect(self.show_main_dialog)
        mw.form.menuTools.addAction(action)
    
    def show_main_dialog(self):
        # 显示主对话框
        pass

# 初始化插件
plugin_manager = PluginManager()
```

---

## 📈 性能优化提示

### 批量操作优化
```python
# ✅ 正确：单一撤销点
def batch_operation(col: Collection, note_ids: list[NoteId]):
    pos = col.add_custom_undo_entry("批量操作")
    
    for nid in note_ids:
        note = col.get_note(nid)
        # 处理笔记...
        col.update_note(note, skip_undo_entry=True)
    
    return col.merge_undo_entries(pos)

# ❌ 错误：多个撤销点
def inefficient_batch(col: Collection, note_ids: list[NoteId]):
    for nid in note_ids:
        note = col.get_note(nid)
        col.update_note(note)  # 每次都创建撤销点
```

### 查询优化
```python
# ✅ 正确：使用SearchNode构建复杂查询
search = col.build_search_string(
    SearchNode(deck="目标牌组"),
    SearchNode(tag="重要")
)
note_ids = list(col.find_notes(search))

# ❌ 错误：手动构建查询字符串
search = 'deck:"目标牌组" tag:重要'  # 容易出错，不支持特殊字符
```

这个 API 速查表涵盖了 Anki 插件开发的所有核心功能，按使用频率和功能分组，提供了完整的方法签名、参数说明和实用的代码示例。开发者可以快速查找所需的 API 并直接复制使用示例代码。