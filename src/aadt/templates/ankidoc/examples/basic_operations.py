"""
基础插件操作示例
展示常用的笔记和牌组操作功能
"""

from aqt import mw, gui_hooks
from aqt.qt import *
from aqt.utils import showInfo, showWarning, askUser
from aqt.operations import CollectionOp, QueryOp
from anki.collection import Collection, OpChanges, SearchNode
from anki.notes import Note, NoteId
from anki.errors import NotFoundError, InvalidInput


class BasicOperationsDemo:
    """基础操作演示类"""
    
    def __init__(self):
        self.setup_menu()
    
    def setup_menu(self):
        """设置菜单项"""
        def add_menu():
            menu = QMenu("基础操作演示", mw)
            
            # 笔记操作
            note_menu = menu.addMenu("笔记操作")
            note_menu.addAction("创建笔记", self.create_sample_note)
            note_menu.addAction("批量更新笔记", self.batch_update_notes)
            note_menu.addAction("搜索笔记", self.search_notes_demo)
            
            # 牌组操作
            deck_menu = menu.addMenu("牌组操作")
            deck_menu.addAction("创建牌组", self.create_deck_demo)
            deck_menu.addAction("移动笔记", self.move_notes_demo)
            
            # 标签操作
            tag_menu = menu.addMenu("标签操作")
            tag_menu.addAction("批量添加标签", self.add_tags_demo)
            tag_menu.addAction("标签统计", self.tag_statistics)
            
            mw.form.menuTools.addMenu(menu)
        
        gui_hooks.main_window_did_init.append(add_menu)
    
    def create_sample_note(self):
        """创建示例笔记"""
        def op(col: Collection) -> OpChanges:
            # 获取或创建牌组
            deck_id = col.decks.id("示例牌组", create=True)
            
            # 获取笔记类型
            notetype = col.models.by_name("Basic")
            if not notetype:
                raise InvalidInput("未找到Basic笔记类型")
            
            # 创建笔记
            note = col.new_note(notetype)
            note["Front"] = "什么是Anki?"
            note["Back"] = "Anki是一个使用间歇重复算法的记忆软件"
            
            return col.add_note(note, deck_id)
        
        CollectionOp(
            parent=mw,
            op=op
        ).success(
            lambda changes: showInfo("示例笔记创建成功！")
        ).failure(
            lambda exc: showWarning(f"创建失败: {exc}")
        ).run_in_background()
    
    def batch_update_notes(self):
        """批量更新笔记示例"""
        def search_and_update():
            def search_op(col: Collection) -> list[NoteId]:
                # 搜索示例牌组中的笔记
                search = col.build_search_string(SearchNode(deck="示例牌组"))
                return list(col.find_notes(search))
            
            def handle_search_results(note_ids: list[NoteId]):
                if not note_ids:
                    showInfo("未找到笔记")
                    return
                
                # 批量更新操作
                def update_op(col: Collection) -> OpChanges:
                    pos = col.add_custom_undo_entry("批量更新笔记")
                    updated_count = 0
                    
                    for nid in note_ids:
                        try:
                            note = col.get_note(nid)
                            # 在Back字段末尾添加时间戳
                            from datetime import datetime
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                            
                            if not note["Back"].endswith(f"[更新于: {timestamp[:10]}]"):
                                note["Back"] += f"<br><small>[更新于: {timestamp[:10]}]</small>"
                                col.update_note(note, skip_undo_entry=True)
                                updated_count += 1
                                
                        except NotFoundError:
                            continue
                    
                    return col.merge_undo_entries(pos)
                
                CollectionOp(
                    parent=mw,
                    op=update_op
                ).success(
                    lambda changes: showInfo(f"成功更新 {len(note_ids)} 个笔记")
                ).with_progress(f"更新 {len(note_ids)} 个笔记").run_in_background()
            
            QueryOp(
                parent=mw,
                op=search_op,
                success=handle_search_results
            ).with_progress("搜索笔记").run_in_background()
        
        search_and_update()
    
    def search_notes_demo(self):
        """搜索笔记演示"""
        # 获取用户输入
        text, ok = QInputDialog.getText(mw, "搜索笔记", "请输入搜索内容:")
        if not ok or not text.strip():
            return
        
        def search_op(col: Collection) -> dict:
            # 在笔记内容中搜索
            search = col.build_search_string(SearchNode(note=text))
            note_ids = list(col.find_notes(search))
            
            results = {
                "count": len(note_ids),
                "notes": []
            }
            
            # 获取前10个笔记的详细信息
            for nid in note_ids[:10]:
                try:
                    note = col.get_note(nid)
                    results["notes"].append({
                        "id": nid,
                        "front": note.get("Front", "")[:50],
                        "back": note.get("Back", "")[:50]
                    })
                except NotFoundError:
                    continue
            
            return results
        
        def show_results(results: dict):
            if results["count"] == 0:
                showInfo("未找到匹配的笔记")
                return
            
            msg = f"找到 {results['count']} 个匹配的笔记\n\n"
            for note_info in results["notes"]:
                msg += f"ID: {note_info['id']}\n"
                msg += f"正面: {note_info['front']}...\n"
                msg += f"背面: {note_info['back']}...\n\n"
            
            if results["count"] > 10:
                msg += f"（仅显示前10个结果）"
            
            showInfo(msg)
        
        QueryOp(
            parent=mw,
            op=search_op,
            success=show_results
        ).with_progress("搜索中").run_in_background()
    
    def create_deck_demo(self):
        """创建牌组演示"""
        deck_name, ok = QInputDialog.getText(mw, "创建牌组", "请输入牌组名称:")
        if not ok or not deck_name.strip():
            return
        
        def op(col: Collection) -> OpChanges:
            # 创建主牌组
            main_deck_id = col.decks.id(deck_name, create=True)
            
            # 创建子牌组
            sub_decks = ["基础", "进阶", "复习"]
            for sub_name in sub_decks:
                full_name = f"{deck_name}::{sub_name}"
                col.decks.id(full_name, create=True)
            
            return col.add_custom_undo_entry(f"创建牌组: {deck_name}")
        
        CollectionOp(
            parent=mw,
            op=op
        ).success(
            lambda changes: showInfo(f"牌组 '{deck_name}' 及其子牌组创建成功！")
        ).run_in_background()
    
    def move_notes_demo(self):
        """移动笔记演示"""
        # 获取所有牌组
        def get_decks_and_move():
            def get_decks_op(col: Collection) -> list[str]:
                return col.decks.all_names()
            
            def handle_decks(deck_names: list[str]):
                if len(deck_names) < 2:
                    showInfo("需要至少2个牌组才能演示移动功能")
                    return
                
                # 显示选择对话框
                dialog = DeckSelectionDialog(mw, deck_names)
                if dialog.exec():
                    source_deck, target_deck = dialog.get_selection()
                    self.move_notes_between_decks(source_deck, target_deck)
            
            QueryOp(
                parent=mw,
                op=get_decks_op,
                success=handle_decks
            ).run_in_background()
        
        get_decks_and_move()
    
    def move_notes_between_decks(self, source_deck: str, target_deck: str):
        """在牌组间移动笔记"""
        def search_and_move():
            def search_op(col: Collection) -> list[NoteId]:
                search = col.build_search_string(SearchNode(deck=source_deck))
                note_ids = list(col.find_notes(search))
                return note_ids[:5]  # 只移动前5个笔记作为演示
            
            def handle_move(note_ids: list[NoteId]):
                if not note_ids:
                    showInfo(f"牌组 '{source_deck}' 中没有笔记")
                    return
                
                def move_op(col: Collection) -> OpChanges:
                    target_deck_id = col.decks.id(target_deck, create=True)
                    moved_count = 0
                    
                    for nid in note_ids:
                        try:
                            note = col.get_note(nid)
                            for card in note.cards():
                                if card.deck_id != target_deck_id:
                                    card.deck_id = target_deck_id
                                    col.update_card(card)
                                    moved_count += 1
                        except NotFoundError:
                            continue
                    
                    return col.add_custom_undo_entry(f"移动笔记: {source_deck} -> {target_deck}")
                
                CollectionOp(
                    parent=mw,
                    op=move_op
                ).success(
                    lambda changes: showInfo(f"成功移动 {len(note_ids)} 个笔记")
                ).run_in_background()
            
            QueryOp(
                parent=mw,
                op=search_op,
                success=handle_move
            ).run_in_background()
        
        search_and_move()
    
    def add_tags_demo(self):
        """批量添加标签演示"""
        tag_name, ok = QInputDialog.getText(mw, "添加标签", "请输入标签名称:")
        if not ok or not tag_name.strip():
            return
        
        def search_and_tag():
            def search_op(col: Collection) -> list[NoteId]:
                # 搜索示例牌组中的笔记
                search = col.build_search_string(SearchNode(deck="示例牌组"))
                return list(col.find_notes(search))
            
            def handle_tagging(note_ids: list[NoteId]):
                if not note_ids:
                    showInfo("未找到笔记")
                    return
                
                def tag_op(col: Collection) -> OpChanges:
                    return col.tags.bulk_add(note_ids, tag_name.strip())
                
                CollectionOp(
                    parent=mw,
                    op=tag_op
                ).success(
                    lambda changes: showInfo(f"成功为 {len(note_ids)} 个笔记添加标签 '{tag_name}'")
                ).run_in_background()
            
            QueryOp(
                parent=mw,
                op=search_op,
                success=handle_tagging
            ).run_in_background()
        
        search_and_tag()
    
    def tag_statistics(self):
        """标签统计"""
        def stats_op(col: Collection) -> dict:
            all_tags = col.tags.all()
            stats = {}
            
            for tag in all_tags:
                search = col.build_search_string(SearchNode(tag=tag))
                count = len(list(col.find_notes(search)))
                stats[tag] = count
            
            return stats
        
        def show_stats(stats: dict):
            if not stats:
                showInfo("没有找到任何标签")
                return
            
            # 按使用次数排序
            sorted_stats = sorted(stats.items(), key=lambda x: x[1], reverse=True)
            
            msg = "标签使用统计:\n\n"
            for tag, count in sorted_stats[:20]:  # 只显示前20个
                msg += f"{tag}: {count} 个笔记\n"
            
            if len(sorted_stats) > 20:
                msg += f"\n（仅显示前20个标签）"
            
            showInfo(msg)
        
        QueryOp(
            parent=mw,
            op=stats_op,
            success=show_stats
        ).with_progress("统计标签").run_in_background()


class DeckSelectionDialog(QDialog):
    """牌组选择对话框"""
    
    def __init__(self, parent, deck_names: list[str]):
        super().__init__(parent)
        self.deck_names = deck_names
        self.setWindowTitle("选择牌组")
        self.setModal(True)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 源牌组选择
        layout.addWidget(QLabel("从牌组:"))
        self.source_combo = QComboBox()
        self.source_combo.addItems(self.deck_names)
        layout.addWidget(self.source_combo)
        
        # 目标牌组选择
        layout.addWidget(QLabel("移动到牌组:"))
        self.target_combo = QComboBox()
        self.target_combo.addItems(self.deck_names)
        if len(self.deck_names) > 1:
            self.target_combo.setCurrentIndex(1)
        layout.addWidget(self.target_combo)
        
        # 按钮
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def get_selection(self) -> tuple[str, str]:
        source = self.source_combo.currentText()
        target = self.target_combo.currentText()
        return source, target


# 初始化演示
demo = BasicOperationsDemo()