# 💡 Anki 插件开发代码模式库

直接可用的代码模板和最佳实践。按开发场景分类，复制即用。

## 🚀 插件初始化模式

### 基础插件模板
```python
# __init__.py
from aqt import mw, gui_hooks
from aqt.qt import *
from aqt.utils import showInfo, showWarning
from aqt.operations import CollectionOp, QueryOp

class MyAddon:
    def __init__(self):
        self.setup_hooks()
        self.setup_menu()
    
    def setup_hooks(self):
        gui_hooks.main_window_did_init.append(self.on_main_window_init)
        gui_hooks.collection_did_load.append(self.on_collection_loaded)
    
    def setup_menu(self):
        def add_menu():
            action = QAction("我的插件", mw)
            action.triggered.connect(self.show_main_dialog)
            mw.form.menuTools.addAction(action)
        
        gui_hooks.main_window_did_init.append(add_menu)
    
    def on_main_window_init(self):
        # 主窗口初始化后执行
        pass
    
    def on_collection_loaded(self, col):
        # 数据库加载后执行
        pass
    
    def show_main_dialog(self):
        dialog = MainDialog(mw)
        dialog.exec()

# 初始化插件
addon = MyAddon()
```

### 配置管理模式
```python
class ConfigManager:
    def __init__(self, addon_name: str):
        self.addon_name = addon_name
        self.defaults = {
            "enabled": True,
            "api_key": "",
            "timeout": 30,
            "batch_size": 100
        }
    
    def get_config(self) -> dict:
        config = mw.addonManager.getConfig(self.addon_name)
        if not config:
            config = self.defaults.copy()
            self.save_config(config)
        return config
    
    def save_config(self, config: dict):
        mw.addonManager.writeConfig(self.addon_name, config)
    
    def get(self, key: str, default=None):
        return self.get_config().get(key, default)
    
    def set(self, key: str, value):
        config = self.get_config()
        config[key] = value
        self.save_config(config)

# 使用方式
config = ConfigManager(__name__)
api_key = config.get("api_key", "default")
```

---

## 🎨 UI 开发模式

### 基础对话框模式
```python
class BaseDialog(QDialog):
    def __init__(self, parent=None, title="对话框"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(500, 400)
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 内容区域
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        layout.addWidget(self.content_widget)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.ok_btn = QPushButton("确定")
        self.cancel_btn = QPushButton("取消")
        button_layout.addWidget(self.ok_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def setup_connections(self):
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
    
    def add_content(self, widget: QWidget):
        self.content_layout.addWidget(widget)

# 使用示例
class MyDialog(BaseDialog):
    def __init__(self, parent=None):
        super().__init__(parent, "我的对话框")
        
        # 添加具体内容
        self.input = QLineEdit()
        self.add_content(QLabel("请输入:"))
        self.add_content(self.input)
    
    def accept(self):
        result = self.input.text()
        if not result:
            showWarning("请输入内容")
            return
        showInfo(f"输入的内容: {result}")
        super().accept()
```

### 表单输入模式
```python
class FormDialog(BaseDialog):
    def __init__(self, parent=None, fields: list[tuple] = None):
        self.fields = fields or []
        self.widgets = {}
        super().__init__(parent, "表单输入")
    
    def setup_ui(self):
        super().setup_ui()
        
        form = QFormLayout()
        for field_name, field_type, default_value in self.fields:
            widget = self.create_widget(field_type, default_value)
            self.widgets[field_name] = widget
            form.addRow(field_name, widget)
        
        self.add_content(QWidget())
        self.content_layout.itemAt(0).widget().setLayout(form)
    
    def create_widget(self, field_type: str, default_value):
        if field_type == "text":
            widget = QLineEdit(str(default_value))
        elif field_type == "number":
            widget = QSpinBox()
            widget.setValue(int(default_value))
        elif field_type == "checkbox":
            widget = QCheckBox()
            widget.setChecked(bool(default_value))
        else:
            widget = QLineEdit(str(default_value))
        return widget
    
    def get_values(self) -> dict:
        values = {}
        for name, widget in self.widgets.items():
            if isinstance(widget, QLineEdit):
                values[name] = widget.text()
            elif isinstance(widget, QSpinBox):
                values[name] = widget.value()
            elif isinstance(widget, QCheckBox):
                values[name] = widget.isChecked()
        return values

# 使用示例
fields = [
    ("姓名", "text", ""),
    ("年龄", "number", 18),
    ("启用", "checkbox", True)
]
dialog = FormDialog(mw, fields)
if dialog.exec():
    values = dialog.get_values()
    print(values)
```

### 进度对话框模式
```python
class ProgressDialog(QDialog):
    def __init__(self, parent=None, title="处理中"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        self.label = QLabel("准备中...")
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        
        layout.addWidget(self.label)
        layout.addWidget(self.progress)
        self.setLayout(layout)
    
    def update_progress(self, value: int, text: str = ""):
        self.progress.setValue(value)
        if text:
            self.label.setText(text)
        QApplication.processEvents()

# 使用示例
def long_running_task():
    dialog = ProgressDialog(mw, "处理笔记")
    dialog.show()
    
    try:
        for i in range(100):
            # 执行任务
            time.sleep(0.01)
            dialog.update_progress(i + 1, f"处理第 {i+1} 项")
        
        showInfo("处理完成")
    finally:
        dialog.close()
```

---

## 📝 数据处理模式

### 笔记批量处理模式
```python
def batch_process_notes(note_ids: list, process_func, batch_size: int = 50):
    """批量处理笔记的通用模式"""
    def op(col: Collection) -> OpChanges:
        pos = col.add_custom_undo_entry("批量处理笔记")
        
        processed = 0
        for i in range(0, len(note_ids), batch_size):
            batch = note_ids[i:i + batch_size]
            
            for note_id in batch:
                try:
                    note = col.get_note(note_id)
                    if process_func(note):  # 如果需要更新
                        col.update_note(note, skip_undo_entry=True)
                        processed += 1
                except Exception as e:
                    logger = mw.addonManager.get_logger(__name__)
                    logger.warning(f"处理笔记 {note_id} 失败: {e}")
        
        return col.merge_undo_entries(pos)
    
    CollectionOp(
        parent=mw,
        op=op
    ).success(
        lambda changes: showInfo(f"批量处理完成，更新了 {processed} 个笔记")
    ).with_progress(f"处理 {len(note_ids)} 个笔记").run_in_background()

# 使用示例：批量添加标签
def add_tag_to_notes(note_ids: list, tag: str):
    def process_note(note):
        current_tags = note.tags
        if tag not in current_tags:
            note.tags = current_tags + [tag]
            return True  # 需要更新
        return False  # 不需要更新
    
    batch_process_notes(note_ids, process_note)
```

### 搜索和过滤模式
```python
def search_and_process(search_params: dict, process_func):
    """搜索笔记并处理的通用模式"""
    def search_op(col: Collection) -> list:
        # 构建搜索条件
        search_nodes = []
        if search_params.get("deck"):
            search_nodes.append(SearchNode(deck=search_params["deck"]))
        if search_params.get("tag"):
            search_nodes.append(SearchNode(tag=search_params["tag"]))
        if search_params.get("field"):
            for field, value in search_params["field"].items():
                search_nodes.append(SearchNode(**{field: value}))
        
        if search_nodes:
            search_string = col.build_search_string(*search_nodes)
            note_ids = list(col.find_notes(search_string))
        else:
            note_ids = []
        
        return note_ids
    
    def handle_results(note_ids: list):
        if not note_ids:
            showInfo("未找到匹配的笔记")
            return
        
        # 处理找到的笔记
        process_func(note_ids)
    
    QueryOp(
        parent=mw,
        op=search_op,
        success=handle_results
    ).with_progress("搜索中...").run_in_background()

# 使用示例
search_params = {
    "deck": "学习",
    "tag": "重要",
    "field": {"Front": "单词"}
}
search_and_process(search_params, lambda ids: showInfo(f"找到 {len(ids)} 个笔记"))
```

### 字段验证和清理模式
```python
class FieldValidator:
    @staticmethod
    def clean_html(text: str) -> str:
        """清理HTML标签"""
        import re
        return re.sub(r'<[^>]+>', '', text).strip()
    
    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """规范化空白字符"""
        import re
        return re.sub(r'\s+', ' ', text).strip()
    
    @staticmethod
    def validate_required(text: str) -> bool:
        """验证必填字段"""
        return bool(text and text.strip())
    
    @staticmethod
    def validate_length(text: str, max_length: int) -> bool:
        """验证长度限制"""
        return len(text) <= max_length

def clean_note_fields(note_ids: list):
    """清理笔记字段的示例"""
    def process_note(note):
        updated = False
        for field in note.keys():
            original = note[field]
            cleaned = FieldValidator.normalize_whitespace(
                FieldValidator.clean_html(original)
            )
            
            if cleaned != original:
                note[field] = cleaned
                updated = True
        
        return updated
    
    batch_process_notes(note_ids, process_note)
```

---

## 🌐 网络操作模式

### 异步网络请求模式
```python
def async_http_request(url: str, data: dict = None, callback = None):
    """异步HTTP请求的标准模式"""
    def fetch_data() -> dict:
        from anki.httpclient import HttpClient
        import json
        
        with HttpClient() as client:
            client.timeout = 30
            
            try:
                if data:
                    response = client.post(
                        url,
                        json.dumps(data).encode(),
                        headers={"Content-Type": "application/json"}
                    )
                else:
                    response = client.get(url)
                
                if response.status_code != 200:
                    raise NetworkError(f"HTTP {response.status_code}")
                
                return json.loads(client.stream_content(response))
                
            except Exception as e:
                raise NetworkError(f"网络请求失败: {e}")
    
    def handle_response(future):
        try:
            result = future.result()
            if callback:
                callback(result)
        except NetworkError as e:
            showWarning(str(e))
        except Exception as e:
            logger = mw.addonManager.get_logger(__name__)
            logger.exception("网络请求异常")
            showWarning(f"请求失败: {e}")
    
    mw.taskman.with_progress(
        task=fetch_data,
        on_done=handle_response,
        label="网络请求中...",
        uses_collection=False
    )

# 使用示例
def api_callback(data):
    showInfo(f"收到数据: {len(data)} 项")

async_http_request("https://api.example.com/data", {"query": "test"}, api_callback)
```

### 网络数据同步模式
```python
def sync_data_from_api(api_url: str, process_data_func):
    """从API同步数据到Anki的完整模式"""
    
    # 步骤1: 获取网络数据
    def fetch_from_api() -> dict:
        from anki.httpclient import HttpClient
        import json
        
        with HttpClient() as client:
            response = client.get(api_url)
            if response.status_code != 200:
                raise NetworkError(f"API请求失败: {response.status_code}")
            return json.loads(client.stream_content(response))
    
    # 步骤2: 处理数据并更新数据库
    def update_collection(data: dict):
        def op(col: Collection) -> OpChanges:
            return process_data_func(col, data)
        
        CollectionOp(
            parent=mw,
            op=op
        ).success(
            lambda changes: showInfo("同步完成")
        ).failure(
            lambda exc: showWarning(f"数据处理失败: {exc}")
        ).with_progress("更新数据库...").run_in_background()
    
    # 步骤3: 执行网络请求
    def handle_api_response(future):
        try:
            data = future.result()
            update_collection(data)
        except Exception as e:
            showWarning(f"同步失败: {e}")
    
    mw.taskman.with_progress(
        task=fetch_from_api,
        on_done=handle_api_response,
        label="获取数据...",
        uses_collection=False
    )

# 使用示例
def process_api_data(col: Collection, data: dict) -> OpChanges:
    """处理API数据并创建笔记"""
    deck_id = col.decks.id("API数据", create=True)
    notetype = col.models.by_name("Basic")
    
    for item in data.get("items", []):
        note = col.new_note(notetype)
        note["Front"] = item.get("question", "")
        note["Back"] = item.get("answer", "")
        col.add_note(note, deck_id)
    
    return col.add_custom_undo_entry("API同步")

sync_data_from_api("https://api.example.com/flashcards", process_api_data)
```

---

## 🚨 错误处理模式

### 安全操作包装器
```python
def safe_operation(operation_func, error_message: str = "操作失败"):
    """安全执行操作的包装器"""
    def wrapper(*args, **kwargs):
        logger = mw.addonManager.get_logger(__name__)
        
        try:
            return operation_func(*args, **kwargs)
        except NotFoundError as e:
            showWarning(f"未找到资源: {e}")
            logger.warning(f"NotFoundError: {e}")
        except InvalidInput as e:
            showWarning(f"输入错误: {e}")
            logger.warning(f"InvalidInput: {e}")
        except NetworkError as e:
            showWarning(f"网络错误: {e}")
            logger.error(f"NetworkError: {e}")
        except Exception as e:
            showWarning(f"{error_message}: {e}")
            logger.exception(f"Unexpected error in {operation_func.__name__}")
            return None
    
    return wrapper

# 使用示例
@safe_operation
def risky_operation(note_id):
    note = mw.col.get_note(note_id)
    # 可能出错的操作
    return note

# 或者装饰器使用
def create_note_safely(deck_name: str, fields: dict):
    @safe_operation
    def _create():
        def op(col: Collection) -> OpChanges:
            deck_id = col.decks.id(deck_name, create=True)
            notetype = col.models.by_name("Basic")
            note = col.new_note(notetype)
            
            for field, value in fields.items():
                if field in note:
                    note[field] = value
            
            return col.add_note(note, deck_id)
        
        CollectionOp(parent=mw, op=op).run_in_background()
    
    return _create()
```

### 输入验证模式
```python
class InputValidator:
    @staticmethod
    def validate_deck_name(name: str) -> str:
        """验证牌组名称"""
        if not name or not name.strip():
            raise InvalidInput("牌组名称不能为空")
        
        # 移除无效字符
        import re
        cleaned = re.sub(r'[<>:"/\\|?*]', '', name.strip())
        if not cleaned:
            raise InvalidInput("牌组名称包含无效字符")
        
        return cleaned
    
    @staticmethod
    def validate_field_content(content: str, max_length: int = 10000) -> str:
        """验证字段内容"""
        if len(content) > max_length:
            raise InvalidInput(f"内容长度超过限制 ({max_length} 字符)")
        return content
    
    @staticmethod
    def validate_note_fields(fields: dict, required_fields: list = None) -> dict:
        """验证笔记字段"""
        if not fields:
            raise InvalidInput("字段不能为空")
        
        validated = {}
        for field, value in fields.items():
            if not isinstance(value, str):
                value = str(value)
            validated[field] = InputValidator.validate_field_content(value)
        
        if required_fields:
            missing = [f for f in required_fields if f not in validated or not validated[f].strip()]
            if missing:
                raise InvalidInput(f"必填字段缺失: {', '.join(missing)}")
        
        return validated

# 使用示例
def create_validated_note(deck_name: str, fields: dict):
    try:
        deck_name = InputValidator.validate_deck_name(deck_name)
        fields = InputValidator.validate_note_fields(fields, ["Front"])
        
        # 创建笔记的安全操作
        create_note_safely(deck_name, fields)
        
    except InvalidInput as e:
        showWarning(str(e))
```

---

## 🔄 生命周期管理模式

### 钩子管理器
```python
class HookManager:
    def __init__(self):
        self.registered_hooks = []
    
    def register(self, hook, callback):
        """注册钩子"""
        hook.append(callback)
        self.registered_hooks.append((hook, callback))
    
    def unregister_all(self):
        """注销所有钩子"""
        for hook, callback in self.registered_hooks:
            try:
                hook.remove(callback)
            except ValueError:
                pass  # 已经被移除
        self.registered_hooks.clear()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.unregister_all()

# 使用示例
class MyAddon:
    def __init__(self):
        self.hook_manager = HookManager()
        self.setup_hooks()
    
    def setup_hooks(self):
        self.hook_manager.register(
            gui_hooks.reviewer_did_show_question,
            self.on_question_shown
        )
        self.hook_manager.register(
            gui_hooks.reviewer_did_show_answer,
            self.on_answer_shown
        )
    
    def on_question_shown(self, card):
        # 处理问题显示
        pass
    
    def on_answer_shown(self, card):
        # 处理答案显示
        pass
    
    def cleanup(self):
        """清理资源"""
        self.hook_manager.unregister_all()
```

### 状态管理模式
```python
class StateManager:
    def __init__(self):
        self.current_state = None
        self.state_handlers = {}
        self.setup_state_tracking()
    
    def setup_state_tracking(self):
        gui_hooks.state_did_change.append(self.on_state_change)
    
    def on_state_change(self, new_state: str, old_state: str):
        self.current_state = new_state
        
        # 执行状态退出处理
        if old_state in self.state_handlers:
            exit_handler = self.state_handlers[old_state].get("exit")
            if exit_handler:
                exit_handler()
        
        # 执行状态进入处理
        if new_state in self.state_handlers:
            enter_handler = self.state_handlers[new_state].get("enter")
            if enter_handler:
                enter_handler()
    
    def register_state_handler(self, state: str, enter_func=None, exit_func=None):
        """注册状态处理器"""
        self.state_handlers[state] = {
            "enter": enter_func,
            "exit": exit_func
        }

# 使用示例
state_manager = StateManager()

def on_enter_review():
    print("进入复习模式")

def on_exit_review():
    print("退出复习模式")

state_manager.register_state_handler("review", on_enter_review, on_exit_review)
```

---

## 📊 调试和日志模式

### 调试日志记录器
```python
class DebugLogger:
    def __init__(self, addon_name: str):
        self.logger = mw.addonManager.get_logger(addon_name)
        self.debug_enabled = self.is_debug_mode()
    
    def is_debug_mode(self) -> bool:
        """检查是否启用调试模式"""
        import os
        return os.environ.get("ANKI_DEBUG") == "1"
    
    def debug(self, message: str, extra_data: dict = None):
        """调试信息"""
        if self.debug_enabled:
            if extra_data:
                message += f" | Data: {extra_data}"
            self.logger.debug(message)
    
    def info(self, message: str):
        """普通信息"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """警告信息"""
        self.logger.warning(message)
    
    def error(self, message: str, exc_info: bool = False):
        """错误信息"""
        if exc_info:
            self.logger.exception(message)
        else:
            self.logger.error(message)
    
    def performance(self, func_name: str, duration: float):
        """性能记录"""
        self.debug(f"Performance: {func_name} took {duration:.3f}s")

# 性能监控装饰器
def monitor_performance(logger: DebugLogger):
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.performance(func.__name__, duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"{func.__name__} failed after {duration:.3f}s: {e}", exc_info=True)
                raise
        return wrapper
    return decorator

# 使用示例
logger = DebugLogger(__name__)

@monitor_performance(logger)
def expensive_operation():
    import time
    time.sleep(1)  # 模拟耗时操作
    return "完成"
```

这个代码模式库提供了 Anki 插件开发中最常用的代码模板，按场景分类，可以直接复制使用。每个模式都包含了最佳实践和错误处理，大大提高开发效率。