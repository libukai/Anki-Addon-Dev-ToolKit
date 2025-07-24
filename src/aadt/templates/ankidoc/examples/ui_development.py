"""
Qt6 UI开发示例
展示对话框、控件和WebView的使用
"""

from aqt import mw, gui_hooks
from aqt.qt import *
from aqt.utils import showInfo, showWarning
from aqt.webview import AnkiWebView
from aqt.operations import CollectionOp
from anki.collection import Collection, OpChanges
import json


class UIDemo:
    """UI开发演示类"""
    
    def __init__(self):
        self.setup_menu()
    
    def setup_menu(self):
        """设置菜单项"""
        def add_menu():
            menu = QMenu("UI开发演示", mw)
            
            menu.addAction("基础对话框", self.show_basic_dialog)
            menu.addAction("表单对话框", self.show_form_dialog)
            menu.addAction("进度对话框", self.show_progress_dialog)
            menu.addAction("WebView演示", self.show_webview_dialog)
            menu.addAction("自定义控件", self.show_custom_widget)
            
            mw.form.menuTools.addMenu(menu)
        
        gui_hooks.main_window_did_init.append(add_menu)
    
    def show_basic_dialog(self):
        """基础对话框演示"""
        dialog = BasicDialog(mw)
        dialog.exec()
    
    def show_form_dialog(self):
        """表单对话框演示"""
        dialog = FormDialog(mw)
        if dialog.exec():
            data = dialog.get_form_data()
            showInfo(f"表单数据: {data}")
    
    def show_progress_dialog(self):
        """进度对话框演示"""
        dialog = ProgressDemo(mw)
        dialog.start_demo()
    
    def show_webview_dialog(self):
        """WebView演示"""
        dialog = WebViewDialog(mw)
        dialog.exec()
    
    def show_custom_widget(self):
        """自定义控件演示"""
        dialog = CustomWidgetDialog(mw)
        dialog.exec()


class BasicDialog(QDialog):
    """基础对话框示例"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("基础对话框演示")
        self.setModal(True)
        self.resize(400, 300)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 标题
        title = QLabel("这是一个基础对话框")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2e7d32;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # 内容区域
        content = QTextEdit()
        content.setPlainText("""
这个对话框演示了基础的Qt6控件使用：

1. QLabel - 显示文本标签
2. QTextEdit - 多行文本编辑器
3. QPushButton - 按钮
4. QVBoxLayout - 垂直布局
5. QHBoxLayout - 水平布局

样式可以通过setStyleSheet()方法设置。
        """)
        content.setReadOnly(True)
        layout.addWidget(content)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        info_btn = QPushButton("显示信息")
        info_btn.clicked.connect(lambda: showInfo("这是一个信息提示"))
        
        warning_btn = QPushButton("显示警告")  
        warning_btn.clicked.connect(lambda: showWarning("这是一个警告提示"))
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(info_btn)
        button_layout.addWidget(warning_btn)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)


class FormDialog(QDialog):
    """表单对话框示例"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("表单对话框演示")
        self.setModal(True)
        self.resize(500, 400)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 表单区域
        form_layout = QFormLayout()
        
        # 文本输入
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("请输入姓名")
        form_layout.addRow("姓名:", self.name_edit)
        
        # 数字输入
        self.age_spin = QSpinBox()
        self.age_spin.setMinimum(1)
        self.age_spin.setMaximum(150)
        self.age_spin.setValue(25)
        form_layout.addRow("年龄:", self.age_spin)
        
        # 下拉选择
        self.city_combo = QComboBox()
        self.city_combo.addItems(["北京", "上海", "广州", "深圳", "杭州"])
        form_layout.addRow("城市:", self.city_combo)
        
        # 多选框
        self.hobby_group = QGroupBox("爱好")
        hobby_layout = QVBoxLayout()
        
        self.reading_check = QCheckBox("阅读")
        self.music_check = QCheckBox("音乐")
        self.sports_check = QCheckBox("运动")
        self.travel_check = QCheckBox("旅行")
        
        hobby_layout.addWidget(self.reading_check)
        hobby_layout.addWidget(self.music_check)
        hobby_layout.addWidget(self.sports_check)
        hobby_layout.addWidget(self.travel_check)
        self.hobby_group.setLayout(hobby_layout)
        
        # 单选框
        self.gender_group = QGroupBox("性别")
        gender_layout = QHBoxLayout()
        
        self.male_radio = QRadioButton("男")
        self.female_radio = QRadioButton("女")
        self.male_radio.setChecked(True)
        
        gender_layout.addWidget(self.male_radio)
        gender_layout.addWidget(self.female_radio)
        self.gender_group.setLayout(gender_layout)
        
        # 多行文本
        self.comment_edit = QTextEdit()
        self.comment_edit.setPlaceholderText("请输入备注信息...")
        self.comment_edit.setMaximumHeight(80)
        
        # 组装表单
        layout.addLayout(form_layout)
        layout.addWidget(self.hobby_group)
        layout.addWidget(self.gender_group)
        layout.addWidget(QLabel("备注:"))
        layout.addWidget(self.comment_edit)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        reset_btn = QPushButton("重置")
        reset_btn.clicked.connect(self.reset_form)
        
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(reset_btn)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def reset_form(self):
        """重置表单"""
        self.name_edit.clear()
        self.age_spin.setValue(25)
        self.city_combo.setCurrentIndex(0)
        
        self.reading_check.setChecked(False)
        self.music_check.setChecked(False)
        self.sports_check.setChecked(False)
        self.travel_check.setChecked(False)
        
        self.male_radio.setChecked(True)
        self.comment_edit.clear()
    
    def get_form_data(self) -> dict:
        """获取表单数据"""
        hobbies = []
        if self.reading_check.isChecked():
            hobbies.append("阅读")
        if self.music_check.isChecked():
            hobbies.append("音乐")
        if self.sports_check.isChecked():
            hobbies.append("运动")
        if self.travel_check.isChecked():
            hobbies.append("旅行")
        
        return {
            "name": self.name_edit.text(),
            "age": self.age_spin.value(),
            "city": self.city_combo.currentText(),
            "hobbies": hobbies,
            "gender": "男" if self.male_radio.isChecked() else "女",
            "comment": self.comment_edit.toPlainText()
        }


class ProgressDemo(QDialog):
    """进度对话框演示"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("进度演示")
        self.setModal(True)
        self.setFixedSize(400, 150)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        self.status_label = QLabel("准备开始...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)
        
        self.detail_label = QLabel("")
        self.detail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detail_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(self.detail_label)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        layout.addWidget(self.cancel_btn)
        
        self.setLayout(layout)
        
        # 进度定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.current_progress = 0
    
    def start_demo(self):
        """开始演示"""
        self.show()
        self.timer.start(100)  # 每100ms更新一次
    
    def update_progress(self):
        """更新进度"""
        self.current_progress += 2
        
        if self.current_progress <= 100:
            self.progress_bar.setValue(self.current_progress)
            
            # 更新状态文本
            if self.current_progress < 30:
                self.status_label.setText("初始化中...")
                self.detail_label.setText("正在加载配置文件")
            elif self.current_progress < 60:
                self.status_label.setText("处理数据中...")
                self.detail_label.setText(f"已处理 {self.current_progress//2}/50 项")
            elif self.current_progress < 90:
                self.status_label.setText("保存结果中...")
                self.detail_label.setText("正在写入数据库")
            else:
                self.status_label.setText("即将完成...")
                self.detail_label.setText("正在清理临时文件")
        else:
            self.timer.stop()
            self.status_label.setText("完成！")
            self.detail_label.setText("所有操作已成功完成")
            self.cancel_btn.setText("关闭")
            showInfo("进度演示完成")


class WebViewDialog(QDialog):
    """WebView演示对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("WebView演示")
        self.setModal(True)
        self.resize(800, 600)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        self.url_edit = QLineEdit("file://example.html")
        load_btn = QPushButton("加载HTML")
        load_btn.clicked.connect(self.load_custom_html)
        
        js_btn = QPushButton("执行JS")
        js_btn.clicked.connect(self.execute_js)
        
        toolbar.addWidget(QLabel("内容:"))
        toolbar.addWidget(self.url_edit)
        toolbar.addWidget(load_btn)
        toolbar.addWidget(js_btn)
        layout.addLayout(toolbar)
        
        # WebView
        self.webview = CustomWebView()
        layout.addWidget(self.webview)
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
        
        # 加载默认内容
        self.load_default_content()
    
    def load_default_content(self):
        """加载默认内容"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Anki WebView 演示</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .demo-section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
                button { padding: 10px 20px; margin: 5px; cursor: pointer; }
                .highlight { background-color: #ffeb3b; padding: 2px 4px; }
                #output { background-color: #f5f5f5; padding: 10px; margin: 10px 0; min-height: 50px; }
            </style>
        </head>
        <body>
            <h1>Anki WebView 演示</h1>
            
            <div class="demo-section">
                <h3>与Python交互</h3>
                <button onclick="pycmd('hello:world')">发送Hello命令</button>
                <button onclick="pycmd('time:now')">获取当前时间</button>
                <button onclick="pycmd('note:create')">创建测试笔记</button>
            </div>
            
            <div class="demo-section">
                <h3>JavaScript功能</h3>
                <button onclick="changeBackground()">改变背景色</button>
                <button onclick="showAlert()">显示警告</button>
                <button onclick="updateContent()">更新内容</button>
            </div>
            
            <div class="demo-section">
                <h3>输出区域</h3>
                <div id="output">点击上面的按钮查看结果...</div>
            </div>
            
            <script>
                function changeBackground() {
                    const colors = ['#ffebee', '#e8f5e8', '#e3f2fd', '#fce4ec', '#f3e5f5'];
                    const randomColor = colors[Math.floor(Math.random() * colors.length)];
                    document.body.style.backgroundColor = randomColor;
                    updateOutput('背景色已更改为: ' + randomColor);
                }
                
                function showAlert() {
                    alert('这是一个JavaScript警告框！');
                    updateOutput('显示了JavaScript警告框');
                }
                
                function updateContent() {
                    const now = new Date().toLocaleString();
                    updateOutput('内容更新时间: ' + now);
                }
                
                function updateOutput(message) {
                    const output = document.getElementById('output');
                    output.innerHTML += '<div>' + message + '</div>';
                    output.scrollTop = output.scrollHeight;
                }
                
                // 从Python接收消息的函数
                function receiveFromPython(data) {
                    updateOutput('从Python收到: ' + JSON.stringify(data));
                }
            </script>
        </body>
        </html>
        """
        self.webview.stdHtml(html_content)
    
    def load_custom_html(self):
        """加载自定义HTML"""
        content = self.url_edit.text()
        if content.startswith('http'):
            showWarning("出于安全考虑，不支持加载外部URL")
        else:
            self.webview.stdHtml(f"<html><body><h1>自定义内容</h1><p>{content}</p></body></html>")
    
    def execute_js(self):
        """执行JavaScript"""
        js_code = """
            receiveFromPython({
                message: "Hello from Python!",
                timestamp: new Date().toISOString(),
                random: Math.random()
            });
        """
        self.webview.eval(js_code)


class CustomWebView(AnkiWebView):
    """自定义WebView"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.set_bridge_command(self.on_bridge_cmd, parent)
    
    def on_bridge_cmd(self, cmd: str) -> bool:
        """处理来自JavaScript的命令"""
        if cmd.startswith("hello:"):
            message = cmd.split(":", 1)[1]
            showInfo(f"收到Hello命令: {message}")
            
            # 向JavaScript发送响应
            js_response = f"""
                receiveFromPython({{
                    type: "hello_response",
                    original: "{message}",
                    response: "Hello from Python!"
                }});
            """
            self.eval(js_response)
            return True
            
        elif cmd.startswith("time:"):
            from datetime import datetime
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            js_response = f"""
                receiveFromPython({{
                    type: "time_response",
                    time: "{current_time}"
                }});
            """
            self.eval(js_response)
            return True
            
        elif cmd.startswith("note:"):
            self.create_test_note()
            return True
        
        return False
    
    def create_test_note(self):
        """创建测试笔记"""
        def op(col: Collection) -> OpChanges:
            deck_id = col.decks.id("WebView测试", create=True)
            notetype = col.models.by_name("Basic")
            
            note = col.new_note(notetype)
            note["Front"] = "这是通过WebView创建的笔记"
            note["Back"] = f"创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            return col.add_note(note, deck_id)
        
        def on_success(changes):
            js_response = """
                receiveFromPython({
                    type: "note_created",
                    success: true,
                    message: "测试笔记创建成功！"
                });
            """
            self.eval(js_response)
        
        CollectionOp(parent=mw, op=op).success(on_success).run_in_background()


class CustomWidgetDialog(QDialog):
    """自定义控件演示"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("自定义控件演示")
        self.setModal(True)
        self.resize(600, 500)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 标签页控件
        tab_widget = QTabWidget()
        
        # 第一个标签页 - 列表控件
        list_tab = QWidget()
        list_layout = QVBoxLayout()
        
        # 列表控件
        self.list_widget = QListWidget()
        items = ["项目1", "项目2", "项目3", "项目4", "项目5"]
        for item in items:
            self.list_widget.addItem(item)
        
        list_control_layout = QHBoxLayout()
        add_btn = QPushButton("添加")
        add_btn.clicked.connect(self.add_list_item)
        remove_btn = QPushButton("删除")
        remove_btn.clicked.connect(self.remove_list_item)
        
        list_control_layout.addWidget(add_btn)
        list_control_layout.addWidget(remove_btn)
        list_control_layout.addStretch()
        
        list_layout.addWidget(self.list_widget)
        list_layout.addLayout(list_control_layout)
        list_tab.setLayout(list_layout)
        
        # 第二个标签页 - 树形控件
        tree_tab = QWidget()
        tree_layout = QVBoxLayout()
        
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["名称", "类型", "大小"])
        
        # 添加树形数据
        root1 = QTreeWidgetItem(["文档", "文件夹", "-"])
        root1.addChild(QTreeWidgetItem(["readme.txt", "文本文件", "1KB"]))
        root1.addChild(QTreeWidgetItem(["manual.pdf", "PDF文件", "2MB"]))
        
        root2 = QTreeWidgetItem(["图片", "文件夹", "-"])
        root2.addChild(QTreeWidgetItem(["photo1.jpg", "图片文件", "500KB"]))
        root2.addChild(QTreeWidgetItem(["photo2.png", "图片文件", "300KB"]))
        
        self.tree_widget.addTopLevelItem(root1)
        self.tree_widget.addTopLevelItem(root2)
        self.tree_widget.expandAll()
        
        tree_layout.addWidget(self.tree_widget)
        tree_tab.setLayout(tree_layout)
        
        # 第三个标签页 - 表格控件
        table_tab = QWidget()
        table_layout = QVBoxLayout()
        
        self.table_widget = QTableWidget(5, 3)
        self.table_widget.setHorizontalHeaderLabels(["姓名", "年龄", "城市"])
        
        # 填充表格数据
        data = [
            ["张三", "25", "北京"],
            ["李四", "30", "上海"],
            ["王五", "28", "广州"],
            ["赵六", "32", "深圳"],
            ["钱七", "26", "杭州"]
        ]
        
        for row, row_data in enumerate(data):
            for col, value in enumerate(row_data):
                self.table_widget.setItem(row, col, QTableWidgetItem(value))
        
        table_layout.addWidget(self.table_widget)
        table_tab.setLayout(table_layout)
        
        # 添加标签页
        tab_widget.addTab(list_tab, "列表控件")
        tab_widget.addTab(tree_tab, "树形控件")
        tab_widget.addTab(table_tab, "表格控件")
        
        layout.addWidget(tab_widget)
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
    
    def add_list_item(self):
        """添加列表项"""
        text, ok = QInputDialog.getText(self, "添加项目", "请输入项目名称:")
        if ok and text:
            self.list_widget.addItem(text)
    
    def remove_list_item(self):
        """删除列表项"""
        current_row = self.list_widget.currentRow()
        if current_row >= 0:
            item = self.list_widget.takeItem(current_row)
            del item


# 初始化UI演示
ui_demo = UIDemo()