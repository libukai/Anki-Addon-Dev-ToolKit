# ⚠️ Anki 插件开发故障排除指南

问题→解决方案映射表。按问题类型分类，快速定位解决方案。

## 🚨 导入和环境问题

### ❌ ModuleNotFoundError: No module named 'PyQt6'
**原因**: 直接导入了PyQt6而不是使用Anki的Qt绑定

**解决方案**:
```python
# ❌ 错误
from PyQt6.QtWidgets import QDialog

# ✅ 正确  
from aqt.qt import QDialog
# 或者
from aqt.qt import *
```

### ❌ AttributeError: 'NoneType' object has no attribute 'col'
**原因**: mw.col在Anki完全启动前可能为None

**解决方案**:
```python
# ❌ 错误
def some_function():
    notes = mw.col.find_notes("deck:学习")

# ✅ 正确
def some_function():
    if not mw.col:
        showWarning("请先打开一个配置文件")
        return
    notes = mw.col.find_notes("deck:学习")

# 或者使用钩子等待Collection加载
def on_collection_loaded(col):
    # 在这里安全使用col
    notes = col.find_notes("deck:学习")

gui_hooks.collection_did_load.append(on_collection_loaded)
```

### ❌ ImportError: cannot import name 'addHook' from 'anki.hooks'
**原因**: 使用了旧版钩子系统（Anki 2.1.20+已废弃）

**解决方案**:
```python
# ❌ 错误（旧版）
from anki.hooks import addHook, runHook
addHook("reviewCleanup", my_function)

# ✅ 正确（新版）
from aqt import gui_hooks
gui_hooks.reviewer_did_show_answer.append(my_function)
```

---

## 💾 数据库操作问题

### ❌ RuntimeError: Cannot execute operation while the collection is being modified
**原因**: 在数据库被锁定时尝试访问

**解决方案**:
```python
# ❌ 错误：在非CollectionOp中修改数据库
def modify_notes():
    for note_id in note_ids:
        note = mw.col.get_note(note_id)
        note["字段"] = "新值"
        mw.col.update_note(note)  # 会导致错误

# ✅ 正确：使用CollectionOp
def modify_notes():
    def op(col: Collection) -> OpChanges:
        for note_id in note_ids:
            note = col.get_note(note_id)
            note["字段"] = "新值"
            col.update_note(note)
        return col.add_custom_undo_entry("修改笔记")
    
    CollectionOp(parent=mw, op=op).run_in_background()
```

### ❌ 撤销功能失效/撤销历史混乱
**原因**: 批量操作时创建了多个撤销点

**解决方案**:
```python
# ❌ 错误：每次更新都创建撤销点
for note_id in note_ids:
    note = col.get_note(note_id)
    note["字段"] = "值"
    col.update_note(note)  # 每次都创建撤销点

# ✅ 正确：单一撤销点
def op(col: Collection) -> OpChanges:
    pos = col.add_custom_undo_entry("批量更新")
    
    for note_id in note_ids:
        note = col.get_note(note_id)
        note["字段"] = "值"
        col.update_note(note, skip_undo_entry=True)
    
    return col.merge_undo_entries(pos)
```

### ❌ NotFoundError: Note not found
**原因**: 笔记ID无效或笔记已被删除

**解决方案**:
```python
# ❌ 错误：不检查笔记是否存在
note = mw.col.get_note(note_id)

# ✅ 正确：处理异常
try:
    note = mw.col.get_note(note_id)
    # 处理笔记
except NotFoundError:
    logger.warning(f"笔记 {note_id} 不存在")
    continue  # 跳过这个笔记

# 或者预先验证
def get_valid_note_ids(col: Collection, note_ids: list) -> list:
    valid_ids = []
    for nid in note_ids:
        try:
            col.get_note(nid)
            valid_ids.append(nid)
        except NotFoundError:
            pass
    return valid_ids
```

---

## 🌐 网络和异步问题

### ❌ NetworkError: Request timeout
**原因**: 网络请求超时或在主线程中执行网络操作

**解决方案**:
```python
# ❌ 错误：在主线程中执行网络请求
def fetch_data():
    import requests
    response = requests.get(url)  # 会阻塞UI

# ✅ 正确：使用TaskManager异步执行
def fetch_data():
    def network_task() -> dict:
        from anki.httpclient import HttpClient
        with HttpClient() as client:
            client.timeout = 30  # 设置超时
            response = client.get(url)
            if response.status_code != 200:
                raise NetworkError(f"HTTP {response.status_code}")
            return json.loads(client.stream_content(response))
    
    mw.taskman.with_progress(
        task=network_task,
        on_done=lambda fut: process_result(fut.result()),
        uses_collection=False  # 关键：网络请求不使用数据库
    )
```

### ❌ RuntimeError: Cannot access collection from background thread
**原因**: 在网络线程中直接访问数据库

**解决方案**:
```python
# ❌ 错误：在网络任务中访问数据库
def bad_network_task():
    data = fetch_from_api()
    # 直接在网络线程中访问col会出错
    note = mw.col.new_note(notetype)

# ✅ 正确：分离网络和数据库操作
def good_pattern():
    # 阶段1：网络请求
    def fetch_data() -> dict:
        return fetch_from_api()
    
    # 阶段2：数据库操作
    def update_database(data: dict):
        def op(col: Collection) -> OpChanges:
            # 在这里安全访问数据库
            note = col.new_note(notetype)
            return col.add_note(note, deck_id)
        
        CollectionOp(parent=mw, op=op).run_in_background()
    
    mw.taskman.with_progress(
        task=fetch_data,
        on_done=lambda fut: update_database(fut.result()),
        uses_collection=False
    )
```

### ❌ 网络请求后UI无响应
**原因**: 网络操作完成后在错误的线程中更新UI

**解决方案**:
```python
# ❌ 错误：在后台线程中直接更新UI
def bad_callback(data):
    # 这可能在后台线程中执行
    dialog.update_content(data)  # 可能导致崩溃

# ✅ 正确：确保UI更新在主线程
def good_callback(data):
    def update_ui():
        dialog.update_content(data)
    
    # 使用QTimer确保在主线程中执行
    from aqt.qt import QTimer
    QTimer.singleShot(0, update_ui)
```

---

## 🎨 UI和界面问题

### ❌ QDialog一闪而过/对话框立即关闭
**原因**: 对话框没有正确的父窗口或使用了show()而不是exec()

**解决方案**:
```python
# ❌ 错误
dialog = MyDialog()  # 没有父窗口
dialog.show()  # 非模态显示，可能立即被垃圾回收

# ✅ 正确
dialog = MyDialog(mw)  # 设置父窗口
dialog.exec()  # 模态显示，等待用户操作
```

### ❌ 对话框内容显示不全/布局混乱
**原因**: 没有正确设置布局或窗口大小

**解决方案**:
```python
class FixedDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("对话框")
        self.setMinimumSize(400, 300)  # 设置最小尺寸
        self.resize(600, 500)  # 设置初始尺寸
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 添加内容
        content = QTextEdit()
        layout.addWidget(content)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()  # 推按钮到右边
        button_layout.addWidget(QPushButton("确定"))
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
```

### ❌ WebView显示空白/无法加载内容
**原因**: WebView没有正确设置或内容路径错误

**解决方案**:
```python
from aqt.webview import AnkiWebView

class MyWebView(AnkiWebView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(800, 600)
        
        # 设置桥接命令处理
        self.set_bridge_command(self.on_bridge_cmd, parent)
        
        # 加载内容
        self.load_content()
    
    def load_content(self):
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>测试页面</title>
        </head>
        <body>
            <h1>Hello World</h1>
            <button onclick="pycmd('test:button')">测试按钮</button>
        </body>
        </html>
        """
        self.stdHtml(html)
    
    def on_bridge_cmd(self, cmd: str) -> bool:
        if cmd.startswith("test:"):
            showInfo(f"收到命令: {cmd}")
            return True
        return False
```

---

## 🔧 配置和插件管理问题

### ❌ 配置文件读取失败/配置丢失
**原因**: 配置文件格式错误或读取方式有误

**解决方案**:
```python
class SafeConfigManager:
    def __init__(self, addon_name: str):
        self.addon_name = addon_name
        self.defaults = {
            "enabled": True,
            "api_key": "",
            "batch_size": 50
        }
    
    def get_config(self) -> dict:
        try:
            config = mw.addonManager.getConfig(self.addon_name)
            if config is None:
                # 首次运行，创建默认配置
                config = self.defaults.copy()
                self.save_config(config)
            else:
                # 合并默认配置（处理新增的配置项）
                for key, value in self.defaults.items():
                    if key not in config:
                        config[key] = value
                self.save_config(config)
            
            return config
        except Exception as e:
            logger = mw.addonManager.get_logger(self.addon_name)
            logger.exception("配置读取失败")
            return self.defaults.copy()
    
    def save_config(self, config: dict):
        try:
            mw.addonManager.writeConfig(self.addon_name, config)
        except Exception as e:
            logger = mw.addonManager.get_logger(self.addon_name)
            logger.exception("配置保存失败")
            showWarning("配置保存失败")
```

### ❌ 插件冲突/其他插件影响
**原因**: 钩子注册冲突或全局变量冲突

**解决方案**:
```python
# 使用命名空间避免冲突
class PluginNamespace:
    def __init__(self, plugin_name: str):
        self.plugin_name = plugin_name
        self.hooks = []
    
    def register_hook(self, hook, callback):
        # 为回调函数添加标识
        callback._plugin_name = self.plugin_name
        hook.append(callback)
        self.hooks.append((hook, callback))
    
    def cleanup(self):
        for hook, callback in self.hooks:
            try:
                hook.remove(callback)
            except ValueError:
                pass
        self.hooks.clear()

# 检查其他插件的影响
def check_plugin_conflicts():
    logger = mw.addonManager.get_logger(__name__)
    
    # 检查关键钩子的注册情况
    hook_count = len(gui_hooks.reviewer_did_show_question._handlers)
    if hook_count > 5:  # 假设阈值
        logger.warning(f"检测到大量reviewer钩子注册: {hook_count}")
```

---

## 📝 字段和笔记类型问题

### ❌ KeyError: 'Front' / 字段不存在
**原因**: 字段名不匹配或笔记类型不正确

**解决方案**:
```python
def safe_field_access(note, field_name: str, default: str = "") -> str:
    """安全访问笔记字段"""
    if field_name in note:
        return note[field_name]
    else:
        # 记录警告并返回默认值
        logger = mw.addonManager.get_logger(__name__)
        logger.warning(f"字段 '{field_name}' 不存在于笔记类型中")
        return default

def safe_field_update(note, field_mapping: dict) -> bool:
    """安全更新笔记字段"""
    updated = False
    available_fields = list(note.keys())
    
    for field_name, value in field_mapping.items():
        if field_name in available_fields:
            if note[field_name] != value:
                note[field_name] = value
                updated = True
        else:
            logger.warning(f"跳过不存在的字段: {field_name}")
    
    return updated

# 验证笔记类型是否包含必需字段
def validate_notetype(col: Collection, notetype_name: str, required_fields: list) -> bool:
    notetype = col.models.by_name(notetype_name)
    if not notetype:
        return False
    
    available_fields = [f["name"] for f in notetype["flds"]]
    missing_fields = [f for f in required_fields if f not in available_fields]
    
    if missing_fields:
        showWarning(f"笔记类型 '{notetype_name}' 缺少必需字段: {', '.join(missing_fields)}")
        return False
    
    return True
```

### ❌ 笔记类型不存在
**原因**: 笔记类型名称错误或用户删除了笔记类型

**解决方案**:
```python
def get_or_create_notetype(col: Collection, notetype_name: str, fields: list) -> dict:
    """获取或创建笔记类型"""
    notetype = col.models.by_name(notetype_name)
    
    if notetype:
        return notetype
    
    # 创建新的笔记类型
    mm = col.models
    notetype = mm.new(notetype_name)
    
    # 添加字段
    for field_name in fields:
        field = mm.new_field(field_name)
        mm.add_field(notetype, field)
    
    # 添加卡片模板
    template = mm.new_template("Card 1")
    template['qfmt'] = "{{" + fields[0] + "}}"
    template['afmt'] = "{{FrontSide}}<hr id=\"answer\">{{" + fields[1] + "}}"
    mm.add_template(notetype, template)
    
    # 保存笔记类型
    mm.add(notetype)
    
    return notetype

# 使用示例
def create_note_with_validation(col: Collection, deck_name: str, content: dict):
    required_fields = ["Front", "Back"]
    notetype = get_or_create_notetype(col, "Basic", required_fields)
    
    if validate_notetype(col, "Basic", required_fields):
        deck_id = col.decks.id(deck_name, create=True)
        note = col.new_note(notetype)
        
        if safe_field_update(note, content):
            return col.add_note(note, deck_id)
```

---

## 🔍 搜索和查询问题

### ❌ 搜索结果为空/搜索语法错误  
**原因**: 搜索语法不正确或特殊字符未转义

**解决方案**:
```python
def build_safe_search(col: Collection, **criteria) -> str:
    """构建安全的搜索字符串"""
    search_nodes = []
    
    for key, value in criteria.items():
        if not value:  # 跳过空值
            continue
            
        if key == "deck":
            search_nodes.append(SearchNode(deck=value))
        elif key == "tag":
            search_nodes.append(SearchNode(tag=value))
        elif key == "note":
            search_nodes.append(SearchNode(note=value))
        elif key.startswith("field_"):
            field_name = key[6:]  # 移除 "field_" 前缀
            search_nodes.append(SearchNode(**{field_name: value}))
    
    if not search_nodes:
        return ""
    
    return col.build_search_string(*search_nodes)

# 使用示例
def search_notes_safely(col: Collection, deck=None, tag=None, content=None):
    try:
        search_string = build_safe_search(
            col, 
            deck=deck, 
            tag=tag, 
            note=content
        )
        
        if not search_string:
            return []
        
        return list(col.find_notes(search_string))
    
    except Exception as e:
        logger = mw.addonManager.get_logger(__name__)
        logger.exception("搜索失败")
        showWarning(f"搜索失败: {e}")
        return []
```

---

## 🔧 性能和内存问题

### ❌ 插件运行缓慢/内存占用过高
**原因**: 批量操作不当或内存泄漏

**解决方案**:
```python
def process_large_dataset(note_ids: list, process_func, batch_size: int = 100):
    """分批处理大量数据"""
    total = len(note_ids)
    processed = 0
    
    def op(col: Collection) -> OpChanges:
        nonlocal processed
        pos = col.add_custom_undo_entry(f"批量处理 {total} 个笔记")
        
        for i in range(0, total, batch_size):
            batch = note_ids[i:i + batch_size]
            
            for note_id in batch:
                try:
                    note = col.get_note(note_id)
                    if process_func(note):
                        col.update_note(note, skip_undo_entry=True)
                        processed += 1
                except Exception as e:
                    logger.warning(f"处理笔记 {note_id} 失败: {e}")
            
            # 每批次后检查是否需要中断
            if processed % (batch_size * 10) == 0:
                QApplication.processEvents()  # 允许UI响应
        
        return col.merge_undo_entries(pos)
    
    CollectionOp(
        parent=mw, 
        op=op
    ).with_progress(f"处理 {total} 个笔记").run_in_background()

# 内存管理
def cleanup_resources():
    """清理资源"""
    import gc
    
    # 清理全局变量
    global cached_data
    cached_data = None
    
    # 强制垃圾回收
    gc.collect()
```

### ❌ UI阻塞/Anki无响应
**原因**: 在主线程中执行耗时操作

**解决方案**:
```python
# ❌ 错误：阻塞主线程
def bad_long_operation():
    for i in range(10000):
        # 耗时操作
        complex_calculation()
    showInfo("完成")

# ✅ 正确：使用异步操作
def good_long_operation():
    def background_task() -> str:
        results = []
        for i in range(10000):
            results.append(complex_calculation())
        return f"处理了 {len(results)} 项"
    
    def on_complete(future):
        try:
            result = future.result()
            showInfo(result)
        except Exception as e:
            showWarning(f"操作失败: {e}")
    
    mw.taskman.with_progress(
        task=background_task,
        on_done=on_complete,
        label="处理中..."
    )
```

---

## 🛠️ 调试技巧

### 启用详细日志
```python
# 在插件初始化时添加
import os
os.environ["ANKI_DEBUG"] = "1"

# 获取日志器
logger = mw.addonManager.get_logger(__name__)

# 记录详细信息
logger.debug(f"处理笔记: {note_id}")
logger.info(f"操作完成: {result}")
logger.exception("发生异常")  # 自动记录堆栈信息
```

### 使用调试控制台
```python
# 在调试控制台中运行
def debug_info():
    print(f"当前状态: {mw.state}")
    print(f"Collection: {mw.col}")
    print(f"当前牌组: {mw.col.decks.current()}")
    print(f"笔记数量: {mw.col.note_count()}")

debug_info()
```

### 错误报告模板
```python
def create_error_report(error: Exception, context: dict = None):
    """创建详细的错误报告"""
    import traceback
    import platform
    
    report = f"""
=== 错误报告 ===
时间: {datetime.now()}
Anki版本: {mw.app.version}
系统: {platform.system()} {platform.release()}
插件: {__name__}

错误类型: {type(error).__name__}
错误信息: {str(error)}

上下文信息:
{context if context else "无"}

堆栈跟踪:
{traceback.format_exc()}
"""
    
    logger = mw.addonManager.get_logger(__name__)
    logger.error(report)
    return report
```

这个故障排除指南按问题类型分类，提供了常见错误的快速解决方案。每个问题都包含了错误原因分析和完整的修复代码，帮助开发者快速定位和解决问题。