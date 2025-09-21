import datetime
import sys
import json
import os

from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLineEdit,
                               QPushButton, QListWidget, QListWidgetItem,
                               QHBoxLayout, QLabel, QFileDialog, QSizePolicy,
                               QMessageBox, QTextEdit, QProgressBar, QGroupBox)
from PySide6.QtCore import Qt, QDir, QStandardPaths, QSize, QThread, Signal, QTimer

from autogit_ui.core.autogit import autogit


class GitWorker(QThread):
    """Git操作工作线程"""
    finished = Signal(object)  # 传递AutoGitResult对象
    progress = Signal(str)  # 传递进度信息

    def __init__(self, path, message=None, push=True):
        super().__init__()
        self.path = path
        self.message = message
        self.push = push

    def run(self):
        self.progress.emit("开始Git操作...")
        result = autogit(self.path, self.message, self.push, silent=True)
        self.finished.emit(result)


class StatusWidget(QWidget):
    """状态显示组件"""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # 分组框
        group_box = QGroupBox("操作日志")
        group_layout = QVBoxLayout(group_box)

        # 状态文本显示
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(120)
        self.status_text.setReadOnly(True)
        self.status_text.setPlaceholderText("操作日志将在这里显示...")

        group_layout.addWidget(self.status_text)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        group_layout.addWidget(self.progress_bar)

        layout.addWidget(group_box)

    def append_log(self, message, log_type="info", details=""):
        """追加日志信息"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")

        # 根据类型选择图标和颜色
        if log_type == "info":
            icon = "✅"
            color = "#2d5a2d"
        elif log_type == "error":
            icon = "❌"
            color = "#d63031"
        elif log_type == "warning":
            icon = "⚠️"
            color = "#856404"
        elif log_type == "progress":
            icon = "🔄"
            color = "#0066cc"
        else:
            icon = "ℹ️"
            color = "#333"

        # 构建消息
        full_msg = f"[{timestamp}] {icon} {message}"
        if details:
            full_msg += f"\n    详情: {details}"

        # 追加到现有内容
        current_text = self.status_text.toPlainText()
        if current_text:
            new_text = current_text + "\n" + full_msg
        else:
            new_text = full_msg

        self.status_text.setPlainText(new_text)

        # 自动滚动到底部
        scrollbar = self.status_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def show_info(self, message, details=""):
        """显示信息"""
        self.append_log(message, "info", details)

    def show_error(self, message, details=""):
        """显示错误"""
        self.append_log(message, "error", details)

    def show_warning(self, message, details=""):
        """显示警告"""
        self.append_log(message, "warning", details)

    def show_progress(self, message):
        """显示进度"""
        self.append_log(message, "progress")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 不确定进度

    def hide_progress(self):
        """隐藏进度条"""
        self.progress_bar.setVisible(False)

    def clear(self):
        """清空状态"""
        self.status_text.clear()
        self.hide_progress()


class PathItemWidget(QWidget):
    """自定义列表项控件"""

    def __init__(self, path, parent=None, on_delete=None, status_widget=None):
        super().__init__(parent)
        self.path = path
        self.on_delete = on_delete
        self.status_widget = status_widget
        self.git_worker = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # 路径标签
        self.path_label = QLabel(path)
        self.path_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout.addWidget(self.path_label)

        # 自动提交按钮
        self.autogit_button = QPushButton("自动提交")

        self.autogit_button.clicked.connect(self.trigger_autogit)
        layout.addWidget(self.autogit_button)

        # 删除按钮
        self.delete_button = QPushButton("删除")
        self.delete_button.clicked.connect(self.trigger_delete)
        layout.addWidget(self.delete_button)

        # 设置控件的固定高度和样式
        self.setMinimumHeight(45)
        self.setMaximumHeight(45)

    def trigger_autogit(self):
        """触发自动Git操作"""
        if self.git_worker and self.git_worker.isRunning():
            self.status_widget.show_warning("操作正在进行中，请稍候...")
            return

        # 禁用按钮
        self.autogit_button.setEnabled(False)
        self.autogit_button.setText("处理中...")

        # 显示进度
        self.status_widget.show_progress(f"正在处理: {os.path.basename(self.path)}")

        # 创建工作线程
        datetime_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.git_worker = GitWorker(self.path, datetime_now, True)
        self.git_worker.progress.connect(self.on_progress)
        self.git_worker.finished.connect(self.on_finished)
        self.git_worker.start()

    def on_progress(self, message):
        """处理进度更新"""
        self.status_widget.show_progress(message)

    def on_finished(self, result):
        """处理操作完成"""
        # 恢复按钮状态
        self.autogit_button.setEnabled(True)
        self.autogit_button.setText("自动提交")
        self.status_widget.hide_progress()

        # 根据结果显示状态
        repo_name = os.path.basename(self.path)
        if result.success:
            self.status_widget.show_info(f"{repo_name}: {result.message}", result.details)

            # 如果有实际提交，显示成功消息框
            if "没有文件需要提交" not in result.message:
                QMessageBox.information(self, "操作成功",
                                        f"仓库 '{repo_name}' 操作成功!\n\n{result.message}")
        else:
            self.status_widget.show_error(f"{repo_name}: {result.message}", result.details)

            # 显示错误对话框
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle("操作失败")
            msg_box.setText(f"仓库 '{repo_name}' 操作失败")
            msg_box.setDetailedText(f"错误详情:\n{result.details}")
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.exec()

    def trigger_delete(self):
        """触发删除操作"""
        # 确认对话框
        reply = QMessageBox.question(self, "确认删除",
                                     f"确定要删除路径 '{self.path}' 吗？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            if self.on_delete:
                self.on_delete(self.path)
            self.status_widget.show_info(f"已删除路径: {os.path.basename(self.path)}")


class StringListApp(QWidget):
    """主应用程序窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Git 自动化工具")
        self.resize(700, 600)


        QApplication.setOrganizationName("MyCompany")
        QApplication.setApplicationName("GitAutomator")

        data_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        if not QDir().exists(data_dir):
            QDir().mkpath(data_dir)

        self.file_path = QDir(data_dir).filePath("path_list.json")
        self.strings = self.load_strings()

        self.setup_ui()
        self.populate_list()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)

        # 标题
        title_label = QLabel("Git 自动化工具")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 输入区域
        input_group = QGroupBox("添加 Git 仓库")
        input_layout = QVBoxLayout(input_group)

        path_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("在这里输入或选择Git仓库路径...")

        self.input_field.returnPressed.connect(self.add_string)
        path_layout.addWidget(self.input_field)

        self.browse_button = QPushButton("选择文件夹")

        self.browse_button.clicked.connect(self.browse_for_path)
        path_layout.addWidget(self.browse_button)

        input_layout.addLayout(path_layout)

        # 添加按钮布局
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("添加仓库")

        self.save_button.clicked.connect(self.add_string)
        button_layout.addWidget(self.save_button)

        # 批量操作按钮
        self.batch_commit_button = QPushButton("批量提交所有仓库")

        self.batch_commit_button.clicked.connect(self.batch_commit_all)
        button_layout.addWidget(self.batch_commit_button)

        input_layout.addLayout(button_layout)
        layout.addWidget(input_group)

        # 列表显示区域
        list_group = QGroupBox("Git 仓库列表")

        list_layout = QVBoxLayout(list_group)

        self.list_widget = QListWidget()

        list_layout.addWidget(self.list_widget)
        layout.addWidget(list_group)

        # 状态显示组件
        self.status_widget = StatusWidget()
        layout.addWidget(self.status_widget)

    def load_strings(self):
        """加载保存的路径列表"""
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_strings(self):
        """保存路径列表"""
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.strings, f, ensure_ascii=False, indent=4)
        except Exception as e:
            self.status_widget.show_error("保存失败", str(e))

    def populate_list(self):
        """填充列表"""
        self.list_widget.clear()
        for s in self.strings:
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 45))
            self.list_widget.addItem(item)
            widget = PathItemWidget(s, on_delete=self.delete_path, status_widget=self.status_widget)
            self.list_widget.setItemWidget(item, widget)

    def add_string(self):
        """添加新路径"""
        new_path = self.input_field.text().strip()
        if not new_path:
            self.status_widget.show_warning("请输入或选择一个路径")
            return

        if not os.path.isdir(new_path):
            self.status_widget.show_error("路径无效", "这不是一个有效的文件夹路径")
            return

        # 简单检查是否是Git仓库
        if not os.path.exists(os.path.join(new_path, '.git')):
            reply = QMessageBox.question(self, "确认添加",
                                         f"路径 '{new_path}' 似乎不是Git仓库，确定要添加吗？",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                return

        if new_path not in self.strings:
            self.strings.append(new_path)
            self.save_strings()
            self.populate_list()
            self.input_field.clear()
            self.status_widget.show_info(f"已添加仓库: {os.path.basename(new_path)}")
        else:
            self.status_widget.show_warning("路径已存在")

    def delete_path(self, path):
        """删除路径"""
        if path in self.strings:
            self.strings.remove(path)
            self.save_strings()
            self.populate_list()

    def browse_for_path(self):
        """浏览选择路径"""
        selected_path = QFileDialog.getExistingDirectory(self, "选择Git仓库目录")
        if selected_path:
            self.input_field.setText(selected_path)

    def batch_commit_all(self):
        """批量提交所有仓库"""
        if not self.strings:
            self.status_widget.show_warning("没有可提交的仓库")
            return

        reply = QMessageBox.question(self, "确认批量操作",
                                     f"确定要对所有 {len(self.strings)} 个仓库执行自动提交吗？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.batch_commit_button.setEnabled(False)
            self.batch_commit_button.setText("批量处理中...")
            self.status_widget.show_progress(f"开始批量提交操作... (0/{len(self.strings)})")

            # 初始化批量操作状态
            self.batch_results = []
            self.batch_total = len(self.strings)
            self.batch_completed = 0
            self.batch_workers = []

            # 为每个仓库创建工作线程
            datetime_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for i, repo_path in enumerate(self.strings):
                worker = GitWorker(repo_path, f"Batch commit: {datetime_now}", True)
                worker.finished.connect(lambda result, path=repo_path: self.on_batch_worker_finished(result, path))
                worker.progress.connect(lambda msg, path=repo_path: self.on_batch_worker_progress(msg, path))

                self.batch_workers.append(worker)

                # 错开启动时间，避免同时启动太多线程
                QTimer.singleShot(i * 200, worker.start)

    def on_batch_worker_progress(self, message, repo_path):
        """处理批量操作进度"""
        repo_name = os.path.basename(repo_path)
        self.status_widget.show_progress(f"{repo_name}: {message}")

    def on_batch_worker_finished(self, result, repo_path):
        """处理单个仓库的批量操作完成"""
        self.batch_completed += 1
        repo_name = os.path.basename(repo_path)

        # 记录结果
        self.batch_results.append({
            'path': repo_path,
            'name': repo_name,
            'result': result
        })

        # 显示单个仓库的结果
        if result.success:
            if "没有文件需要提交" not in result.message:
                self.status_widget.show_info(f"{repo_name}: {result.message}")
            else:
                self.status_widget.append_log(f"{repo_name}: {result.message}", "warning")
        else:
            self.status_widget.show_error(f"{repo_name}: {result.message}", result.details)

        # 更新进度
        progress_msg = f"批量操作进行中... ({self.batch_completed}/{self.batch_total})"
        self.status_widget.show_progress(progress_msg)

        # 检查是否所有操作都完成
        if self.batch_completed >= self.batch_total:
            self.finish_batch_commit()

    def finish_batch_commit(self):
        """完成批量提交"""
        self.batch_commit_button.setEnabled(True)
        self.batch_commit_button.setText("批量提交所有仓库")
        self.status_widget.hide_progress()

        # 统计结果
        success_count = sum(1 for r in self.batch_results if r['result'].success)
        failed_count = self.batch_total - success_count
        committed_count = sum(1 for r in self.batch_results
                              if r['result'].success and "没有文件需要提交" not in r['result'].message)
        no_changes_count = sum(1 for r in self.batch_results
                               if r['result'].success and "没有文件需要提交" in r['result'].message)

        # 显示总结
        summary_msg = f"批量操作完成! 成功: {success_count}, 失败: {failed_count}"
        if committed_count > 0:
            summary_msg += f", 实际提交: {committed_count}"
        if no_changes_count > 0:
            summary_msg += f", 无变更: {no_changes_count}"

        if failed_count == 0:
            self.status_widget.show_info(summary_msg)
        else:
            self.status_widget.show_warning(summary_msg)

        # 显示详细结果对话框
        self.show_batch_results_dialog()

        # 清理批量操作状态
        self.batch_workers.clear()
        self.batch_results.clear()

    def show_batch_results_dialog(self):
        """显示批量操作结果对话框"""
        dialog = QMessageBox(self)
        dialog.setWindowTitle("批量操作结果")

        # 统计信息
        success_count = sum(1 for r in self.batch_results if r['result'].success)
        failed_count = self.batch_total - success_count
        committed_count = sum(1 for r in self.batch_results
                              if r['result'].success and "没有文件需要提交" not in r['result'].message)

        if failed_count == 0:
            dialog.setIcon(QMessageBox.Icon.Information)
            dialog.setText(
                f"批量操作全部成功!\n\n总共处理: {self.batch_total} 个仓库\n实际提交: {committed_count} 个仓库")
        else:
            dialog.setIcon(QMessageBox.Icon.Warning)
            dialog.setText(
                f"批量操作部分失败\n\n成功: {success_count} 个\n失败: {failed_count} 个\n实际提交: {committed_count} 个")

        # 详细结果
        details = []
        for r in self.batch_results:
            status = "✅" if r['result'].success else "❌"
            details.append(f"{status} {r['name']}: {r['result'].message}")

        dialog.setDetailedText("\n".join(details))
        dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
        dialog.exec()


def main():
    app = QApplication(sys.argv)
    window = StringListApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()