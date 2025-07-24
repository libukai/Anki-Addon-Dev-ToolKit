"""
高级功能实现示例
展示网络请求、钩子管理、性能优化等高级特性
"""

from aqt import mw, gui_hooks
from aqt.qt import *
from aqt.utils import showInfo, showWarning, askUser
from aqt.operations import CollectionOp, QueryOp
from aqt.webview import AnkiWebView
from anki.collection import Collection, OpChanges, SearchNode
from anki.notes import Note, NoteId
from anki.errors import NotFoundError, NetworkError
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Callable


class AdvancedFeaturesDemo:
    """高级功能演示类"""
    
    def __init__(self):
        self.hook_manager = HookManager()
        self.performance_monitor = PerformanceMonitor()
        self.setup_menu()
        self.setup_hooks()
    
    def setup_menu(self):
        """设置菜单项"""
        def add_menu():
            menu = QMenu("高级功能演示", mw)
            
            # 网络操作
            network_menu = menu.addMenu("网络操作")
            network_menu.addAction("API数据同步", self.demo_api_sync)
            network_menu.addAction("批量下载", self.demo_batch_download)
            
            # 钩子管理
            hook_menu = menu.addMenu("钩子管理")
            hook_menu.addAction("注册复习钩子", self.register_review_hooks)
            hook_menu.addAction("注销所有钩子", self.unregister_all_hooks)
            hook_menu.addAction("钩子状态", self.show_hook_status)
            
            # 性能优化
            perf_menu = menu.addMenu("性能优化")
            perf_menu.addAction("批量处理演示", self.demo_batch_processing)
            perf_menu.addAction("内存优化", self.demo_memory_optimization)
            perf_menu.addAction("性能报告", self.show_performance_report)
            
            # 数据分析
            analysis_menu = menu.addMenu("数据分析")
            analysis_menu.addAction("学习统计", self.show_study_statistics)
            analysis_menu.addAction("数据导出", self.export_data)
            analysis_menu.addAction("可视化报告", self.show_visualization)
            
            mw.form.menuTools.addMenu(menu)
        
        gui_hooks.main_window_did_init.append(add_menu)
    
    def setup_hooks(self):
        """设置基础钩子"""
        self.hook_manager.register(
            gui_hooks.state_did_change,
            self.on_state_change
        )
    
    def on_state_change(self, new_state: str, old_state: str):
        """状态变化处理"""
        logger = mw.addonManager.get_logger(__name__)
        logger.info(f"状态变化: {old_state} -> {new_state}")
    
    def demo_api_sync(self):
        """API数据同步演示"""
        dialog = ApiSyncDialog(mw)
        dialog.exec()
    
    def demo_batch_download(self):
        """批量下载演示"""
        urls = [
            "https://httpbin.org/json",
            "https://httpbin.org/uuid",
            "https://httpbin.org/ip"
        ]
        downloader = BatchDownloader(urls)
        downloader.start_download()
    
    def register_review_hooks(self):
        """注册复习相关钩子"""
        def on_card_shown(card):
            showInfo(f"显示卡片: {card.id}", timeout=1000)
        
        def on_card_answered(reviewer, card, ease):
            showInfo(f"回答卡片: {card.id}, 难度: {ease}", timeout=1000)
        
        self.hook_manager.register(gui_hooks.reviewer_did_show_question, on_card_shown)
        self.hook_manager.register(gui_hooks.reviewer_did_answer_card, on_card_answered)
        
        showInfo("复习钩子已注册")
    
    def unregister_all_hooks(self):
        """注销所有钩子"""
        count = len(self.hook_manager.registered_hooks)
        self.hook_manager.unregister_all()
        showInfo(f"已注销 {count} 个钩子")
    
    def show_hook_status(self):
        """显示钩子状态"""
        status = f"当前注册的钩子数量: {len(self.hook_manager.registered_hooks)}\\n\\n"
        for i, (hook, callback) in enumerate(self.hook_manager.registered_hooks, 1):
            hook_name = getattr(hook, '_name', str(hook))
            callback_name = getattr(callback, '__name__', str(callback))
            status += f"{i}. {hook_name} -> {callback_name}\\n"
        
        showInfo(status)
    
    @PerformanceMonitor.monitor_performance
    def demo_batch_processing(self):
        """批量处理演示"""
        processor = BatchProcessor()
        processor.start_processing()
    
    def demo_memory_optimization(self):
        """内存优化演示"""
        optimizer = MemoryOptimizer()
        optimizer.demonstrate_optimization()
    
    def show_performance_report(self):
        """显示性能报告"""
        report = self.performance_monitor.get_report()
        dialog = PerformanceReportDialog(mw, report)
        dialog.exec()
    
    def show_study_statistics(self):
        """显示学习统计"""
        analyzer = StudyAnalyzer()
        analyzer.show_statistics()
    
    def export_data(self):
        """数据导出"""
        exporter = DataExporter()
        exporter.export_to_json()
    
    def show_visualization(self):
        """显示可视化报告"""
        dialog = VisualizationDialog(mw)
        dialog.exec()


class HookManager:
    """钩子管理器 - 统一管理钩子的注册和注销"""
    
    def __init__(self):
        self.registered_hooks: List[tuple] = []
    
    def register(self, hook, callback: Callable):
        """注册钩子"""
        hook.append(callback)
        self.registered_hooks.append((hook, callback))
    
    def unregister(self, hook, callback: Callable):
        """注销单个钩子"""
        try:
            hook.remove(callback)
            self.registered_hooks.remove((hook, callback))
        except ValueError:
            pass  # 钩子已经被移除
    
    def unregister_all(self):
        """注销所有钩子"""
        for hook, callback in self.registered_hooks.copy():
            try:
                hook.remove(callback)
            except ValueError:
                pass
        self.registered_hooks.clear()


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.performance_data: Dict[str, List[float]] = {}
    
    @staticmethod
    def monitor_performance(func):
        """性能监控装饰器"""
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # 记录性能数据
                if hasattr(args[0], 'performance_monitor'):
                    monitor = args[0].performance_monitor
                    if func.__name__ not in monitor.performance_data:
                        monitor.performance_data[func.__name__] = []
                    monitor.performance_data[func.__name__].append(duration)
                
                logger = mw.addonManager.get_logger(__name__)
                logger.info(f"Performance: {func.__name__} took {duration:.3f}s")
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger = mw.addonManager.get_logger(__name__)
                logger.error(f"{func.__name__} failed after {duration:.3f}s: {e}")
                raise
        return wrapper
    
    def get_report(self) -> Dict:
        """获取性能报告"""
        report = {}
        for func_name, durations in self.performance_data.items():
            report[func_name] = {
                'count': len(durations),
                'total': sum(durations),
                'average': sum(durations) / len(durations),
                'min': min(durations),
                'max': max(durations)
            }
        return report


class ApiSyncDialog(QDialog):
    """API同步对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("API数据同步")
        self.setModal(True)
        self.resize(600, 400)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # API配置
        config_group = QGroupBox("API配置")
        config_layout = QFormLayout()
        
        self.api_url_edit = QLineEdit("https://jsonplaceholder.typicode.com/posts")
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 300)
        self.timeout_spin.setValue(30)
        self.timeout_spin.setSuffix(" 秒")
        
        config_layout.addRow("API地址:", self.api_url_edit)
        config_layout.addRow("超时时间:", self.timeout_spin)
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # 同步选项
        options_group = QGroupBox("同步选项")
        options_layout = QVBoxLayout()
        
        self.create_deck_check = QCheckBox("创建新牌组")
        self.create_deck_check.setChecked(True)
        self.overwrite_check = QCheckBox("覆盖现有笔记")
        self.add_tags_check = QCheckBox("添加同步标签")
        self.add_tags_check.setChecked(True)
        
        options_layout.addWidget(self.create_deck_check)
        options_layout.addWidget(self.overwrite_check)
        options_layout.addWidget(self.add_tags_check)
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # 进度显示
        self.progress_label = QLabel("准备同步...")
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        layout.addWidget(self.progress_label)
        layout.addWidget(self.progress_bar)
        
        # 日志显示
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(100)
        self.log_text.setReadOnly(True)
        layout.addWidget(QLabel("同步日志:"))
        layout.addWidget(self.log_text)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        self.sync_btn = QPushButton("开始同步")
        self.sync_btn.clicked.connect(self.start_sync)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(self.sync_btn)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def log_message(self, message: str):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
    
    def start_sync(self):
        """开始同步"""
        self.sync_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 不确定进度
        
        self.log_message("开始API同步...")
        
        # 网络请求阶段
        def fetch_api_data() -> List[Dict]:
            from anki.httpclient import HttpClient
            import json
            
            url = self.api_url_edit.text()
            timeout = self.timeout_spin.value()
            
            with HttpClient() as client:
                client.timeout = timeout
                response = client.get(url)
                
                if response.status_code != 200:
                    raise NetworkError(f"HTTP {response.status_code}")
                
                data = json.loads(client.stream_content(response))
                
                # 模拟处理时间
                time.sleep(1)
                
                return data[:5]  # 只取前5条数据作为演示
        
        # 数据库更新阶段
        def update_database(data: List[Dict]):
            def op(col: Collection) -> OpChanges:
                deck_name = "API同步数据"
                deck_id = col.decks.id(deck_name, create=True)
                notetype = col.models.by_name("Basic")
                
                created_count = 0
                for item in data:
                    note = col.new_note(notetype)
                    note["Front"] = f"标题: {item.get('title', 'N/A')}"
                    note["Back"] = f"内容: {item.get('body', 'N/A')[:100]}..."
                    
                    if self.add_tags_check.isChecked():
                        note.tags = ["api-sync", f"post-{item.get('id', 0)}"]
                    
                    col.add_note(note, deck_id)
                    created_count += 1
                
                return col.add_custom_undo_entry(f"API同步: 创建{created_count}个笔记")
            
            CollectionOp(
                parent=self,
                op=op
            ).success(
                lambda changes: self.sync_completed(len(data))
            ).failure(
                lambda exc: self.sync_failed(str(exc))
            ).run_in_background()
        
        # 处理网络响应
        def handle_api_response(future):
            try:
                data = future.result()
                self.log_message(f"成功获取 {len(data)} 条数据")
                self.progress_label.setText("更新数据库...")
                update_database(data)
            except Exception as e:
                self.sync_failed(str(e))
        
        # 执行网络请求
        self.progress_label.setText("正在获取API数据...")
        mw.taskman.with_progress(
            task=fetch_api_data,
            on_done=handle_api_response,
            uses_collection=False
        )
    
    def sync_completed(self, count: int):
        """同步完成"""
        self.progress_bar.setVisible(False)
        self.progress_label.setText(f"同步完成！创建了 {count} 个笔记")
        self.log_message(f"同步成功完成，共创建 {count} 个笔记")
        self.sync_btn.setEnabled(True)
    
    def sync_failed(self, error: str):
        """同步失败"""
        self.progress_bar.setVisible(False)
        self.progress_label.setText("同步失败")
        self.log_message(f"同步失败: {error}")
        self.sync_btn.setEnabled(True)
        showWarning(f"同步失败: {error}")


class BatchDownloader:
    """批量下载器"""
    
    def __init__(self, urls: List[str]):
        self.urls = urls
        self.results = []
    
    def start_download(self):
        """开始下载"""
        dialog = QProgressDialog("准备下载...", "取消", 0, len(self.urls), mw)
        dialog.setWindowTitle("批量下载")
        dialog.setModal(True)
        dialog.show()
        
        def download_single_url(url: str) -> Dict:
            from anki.httpclient import HttpClient
            import json
            
            try:
                with HttpClient() as client:
                    client.timeout = 10
                    response = client.get(url)
                    
                    if response.status_code == 200:
                        content = client.stream_content(response)
                        try:
                            data = json.loads(content)
                        except:
                            data = content[:100]  # 如果不是JSON，只取前100字符
                        
                        return {"url": url, "success": True, "data": data}
                    else:
                        return {"url": url, "success": False, "error": f"HTTP {response.status_code}"}
            except Exception as e:
                return {"url": url, "success": False, "error": str(e)}
        
        def process_downloads():
            for i, url in enumerate(self.urls):
                if dialog.wasCanceled():
                    break
                
                dialog.setLabelText(f"下载: {url}")
                dialog.setValue(i)
                QApplication.processEvents()
                
                result = download_single_url(url)
                self.results.append(result)
                
                time.sleep(0.5)  # 模拟下载时间
            
            dialog.setValue(len(self.urls))
            self.show_results()
        
        # 在后台线程中执行下载
        mw.taskman.with_progress(
            task=process_downloads,
            on_done=lambda fut: None,
            uses_collection=False
        )
    
    def show_results(self):
        """显示下载结果"""
        successful = sum(1 for r in self.results if r["success"])
        failed = len(self.results) - successful
        
        message = f"下载完成!\\n成功: {successful}\\n失败: {failed}\\n\\n"
        
        for result in self.results:
            status = "✓" if result["success"] else "✗"
            message += f"{status} {result['url']}\\n"
            if not result["success"]:
                message += f"  错误: {result.get('error', 'Unknown')}\\n"
        
        showInfo(message)


class BatchProcessor:
    """批量处理器 - 演示高效的批量操作"""
    
    def start_processing(self):
        """开始批量处理"""
        def search_and_process():
            def search_op(col: Collection) -> List[NoteId]:
                # 获取所有笔记ID（限制在1000个以内）
                all_notes = list(col.find_notes(""))
                return all_notes[:1000]
            
            def handle_processing(note_ids: List[NoteId]):
                if not note_ids:
                    showInfo("没有找到笔记")
                    return
                
                # 批量处理
                batch_size = 50
                total_batches = (len(note_ids) + batch_size - 1) // batch_size
                
                dialog = QProgressDialog(f"处理 {len(note_ids)} 个笔记", "取消", 0, total_batches, mw)
                dialog.setWindowTitle("批量处理")
                dialog.show()
                
                def process_op(col: Collection) -> OpChanges:
                    pos = col.add_custom_undo_entry("批量处理演示")
                    processed = 0
                    
                    for batch_num in range(total_batches):
                        if dialog.wasCanceled():
                            break
                        
                        start_idx = batch_num * batch_size
                        end_idx = min(start_idx + batch_size, len(note_ids))
                        batch = note_ids[start_idx:end_idx]
                        
                        for nid in batch:
                            try:
                                note = col.get_note(nid)
                                # 模拟处理：在笔记中添加处理标记
                                if not note.has_tag("processed"):
                                    note.tags = note.tags + ["processed"]
                                    col.update_note(note, skip_undo_entry=True)
                                    processed += 1
                            except NotFoundError:
                                continue
                        
                        # 更新进度
                        dialog.setValue(batch_num + 1)
                        dialog.setLabelText(f"处理批次 {batch_num + 1}/{total_batches}")
                        QApplication.processEvents()
                    
                    return col.merge_undo_entries(pos)
                
                CollectionOp(
                    parent=mw,
                    op=process_op
                ).success(
                    lambda changes: showInfo(f"批量处理完成！")
                ).run_in_background()
            
            QueryOp(
                parent=mw,
                op=search_op,
                success=handle_processing
            ).run_in_background()
        
        search_and_process()


class MemoryOptimizer:
    """内存优化器"""
    
    def demonstrate_optimization(self):
        """演示内存优化技术"""
        import gc
        import sys
        
        # 获取当前内存使用情况
        def get_memory_usage():
            # 简化的内存使用检查
            return len(gc.get_objects())
        
        before_objects = get_memory_usage()
        
        # 创建大量临时对象（模拟内存密集操作）
        temp_data = []
        for i in range(10000):
            temp_data.append(f"临时数据_{i}")
        
        during_objects = get_memory_usage()
        
        # 清理临时数据
        temp_data.clear()
        temp_data = None
        
        # 强制垃圾回收
        collected = gc.collect()
        
        after_objects = get_memory_usage()
        
        # 显示结果
        report = f"""内存优化演示结果:

开始时对象数量: {before_objects:,}
创建临时数据后: {during_objects:,}
清理后对象数量: {after_objects:,}

垃圾回收释放对象: {collected}
内存优化效果: {during_objects - after_objects:,} 个对象被释放

优化建议:
1. 及时清理不需要的大型数据结构
2. 使用 gc.collect() 强制垃圾回收
3. 避免循环引用
4. 使用生成器代替列表处理大数据集
"""
        
        showInfo(report)


class StudyAnalyzer:
    """学习分析器"""
    
    def show_statistics(self):
        """显示学习统计"""
        def analyze_op(col: Collection) -> Dict:
            stats = {}
            
            # 基本统计
            stats['total_notes'] = col.note_count()
            stats['total_cards'] = col.card_count()
            stats['total_decks'] = len(col.decks.all())
            
            # 今日统计
            today_stats = col.stats().today()
            stats['cards_studied_today'] = today_stats[0]  # 今日学习卡片数
            stats['time_studied_today'] = today_stats[1]   # 今日学习时间（秒）
            
            # 牌组统计
            deck_stats = {}
            for deck in col.decks.all():
                deck_name = deck['name']
                deck_search = col.build_search_string(SearchNode(deck=deck_name))
                deck_note_count = len(list(col.find_notes(deck_search)))
                deck_stats[deck_name] = deck_note_count
            
            stats['deck_breakdown'] = deck_stats
            
            return stats
        
        def show_analysis(stats: Dict):
            message = f"""学习统计分析:

📊 总体统计:
• 笔记总数: {stats['total_notes']:,}
• 卡片总数: {stats['total_cards']:,}  
• 牌组总数: {stats['total_decks']}

📅 今日统计:
• 已学习卡片: {stats['cards_studied_today']}
• 学习时间: {stats['time_studied_today'] // 60} 分钟

📚 牌组分布:"""
            
            # 按笔记数量排序牌组
            sorted_decks = sorted(
                stats['deck_breakdown'].items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            
            for deck_name, note_count in sorted_decks[:10]:  # 只显示前10个
                message += f"\\n• {deck_name}: {note_count} 个笔记"
            
            if len(sorted_decks) > 10:
                message += f"\\n• ... 还有 {len(sorted_decks) - 10} 个牌组"
            
            showInfo(message)
        
        QueryOp(
            parent=mw,
            op=analyze_op,
            success=show_analysis
        ).with_progress("分析学习数据").run_in_background()


class DataExporter:
    """数据导出器"""
    
    def export_to_json(self):
        """导出数据到JSON"""
        def export_op(col: Collection) -> Dict:
            export_data = {
                "export_time": datetime.now().isoformat(),
                "anki_version": mw.app.version,
                "collection_info": {
                    "note_count": col.note_count(),
                    "card_count": col.card_count(),
                    "deck_count": len(col.decks.all())
                },
                "decks": [],
                "sample_notes": []
            }
            
            # 导出牌组信息
            for deck in col.decks.all():
                deck_info = {
                    "id": deck["id"],
                    "name": deck["name"],
                    "note_count": len(list(col.find_notes(f'deck:"{deck["name"]}"')))
                }
                export_data["decks"].append(deck_info)
            
            # 导出样本笔记（前10个）
            sample_note_ids = list(col.find_notes(""))[:10]
            for nid in sample_note_ids:
                try:
                    note = col.get_note(nid)
                    note_data = {
                        "id": nid,
                        "notetype": note.note_type()["name"],
                        "fields": dict(note.items()),
                        "tags": note.tags
                    }
                    export_data["sample_notes"].append(note_data)
                except NotFoundError:
                    continue
            
            return export_data
        
        def save_export(data: Dict):
            filename = f"anki_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(os.path.expanduser("~"), "Desktop", filename)
            
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                showInfo(f"数据已导出到: {filepath}")
            except Exception as e:
                showWarning(f"导出失败: {e}")
        
        QueryOp(
            parent=mw,
            op=export_op,
            success=save_export
        ).with_progress("导出数据").run_in_background()


class VisualizationDialog(QDialog):
    """可视化报告对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("数据可视化")
        self.setModal(True)
        self.resize(800, 600)
        self.setup_ui()
        self.load_visualization()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # WebView用于显示图表
        self.webview = AnkiWebView()
        layout.addWidget(self.webview)
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新数据")
        refresh_btn.clicked.connect(self.load_visualization)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(refresh_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_visualization(self):
        """加载可视化内容"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Anki数据可视化</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .chart-container { margin: 30px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }
                h2 { color: #2e7d32; }
            </style>
        </head>
        <body>
            <h1>Anki 学习数据可视化</h1>
            
            <div class="chart-container">
                <h2>学习进度趋势</h2>
                <canvas id="progressChart" width="400" height="200"></canvas>
            </div>
            
            <div class="chart-container">
                <h2>牌组分布</h2>
                <canvas id="deckChart" width="400" height="200"></canvas>
            </div>
            
            <script>
                // 模拟数据 - 实际应用中从Python获取
                const progressData = {
                    labels: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
                    datasets: [{
                        label: '学习卡片数',
                        data: [12, 19, 3, 5, 2, 3, 9],
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        tension: 0.1
                    }]
                };
                
                const deckData = {
                    labels: ['英语', '数学', '历史', '科学', '其他'],
                    datasets: [{
                        label: '笔记数量',
                        data: [300, 50, 100, 75, 25],
                        backgroundColor: [
                            'rgba(255, 99, 132, 0.8)',
                            'rgba(54, 162, 235, 0.8)',
                            'rgba(255, 205, 86, 0.8)',
                            'rgba(75, 192, 192, 0.8)',
                            'rgba(153, 102, 255, 0.8)'
                        ]
                    }]
                };
                
                // 创建图表
                new Chart(document.getElementById('progressChart'), {
                    type: 'line',
                    data: progressData,
                    options: {
                        responsive: true,
                        plugins: {
                            title: {
                                display: true,
                                text: '最近一周学习进度'
                            }
                        }
                    }
                });
                
                new Chart(document.getElementById('deckChart'), {
                    type: 'doughnut',
                    data: deckData,
                    options: {
                        responsive: true,
                        plugins: {
                            title: {
                                display: true,
                                text: '牌组笔记分布'
                            }
                        }
                    }
                });
            </script>
        </body>
        </html>
        """
        
        self.webview.stdHtml(html_content)


class PerformanceReportDialog(QDialog):
    """性能报告对话框"""
    
    def __init__(self, parent=None, report_data: Dict = None):
        super().__init__(parent)
        self.report_data = report_data or {}
        self.setWindowTitle("性能报告")
        self.setModal(True)
        self.resize(600, 400)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 报告内容
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        self.generate_report()
        layout.addWidget(self.report_text)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        export_btn = QPushButton("导出报告")
        export_btn.clicked.connect(self.export_report)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(export_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def generate_report(self):
        """生成性能报告"""
        if not self.report_data:
            self.report_text.setPlainText("暂无性能数据")
            return
        
        report = f"性能分析报告\\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n\\n"
        
        for func_name, stats in self.report_data.items():
            report += f"函数: {func_name}\\n"
            report += f"  调用次数: {stats['count']}\\n"
            report += f"  平均耗时: {stats['average']:.3f}秒\\n"
            report += f"  总耗时: {stats['total']:.3f}秒\\n"
            report += f"  最快: {stats['min']:.3f}秒\\n"
            report += f"  最慢: {stats['max']:.3f}秒\\n\\n"
        
        self.report_text.setPlainText(report)
    
    def export_report(self):
        """导出报告"""
        filename = f"performance_report_{datetime.now().strftime '%Y%m%d_%H%M%S'}.txt"
        filepath = os.path.join(os.path.expanduser("~"), "Desktop", filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self.report_text.toPlainText())
            showInfo(f"报告已导出到: {filepath}")
        except Exception as e:
            showWarning(f"导出失败: {e}")


# 初始化高级功能演示
advanced_demo = AdvancedFeaturesDemo()