import datetime
import sys
import json
import os
from functools import partial

from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLineEdit,
                               QPushButton, QListWidget, QListWidgetItem,
                               QHBoxLayout, QLabel, QFileDialog, QSizePolicy)
from PySide6.QtCore import Qt, QDir, QStandardPaths

from src.core.autogit import autogit

import sys
import json
import os
from functools import partial

from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLineEdit,
                               QPushButton, QListWidget, QListWidgetItem,
                               QHBoxLayout, QLabel, QFileDialog, QSizePolicy)
from PySide6.QtCore import Qt, QDir, QStandardPaths, QSize





# --- 自定义列表项控件 ---
class PathItemWidget(QWidget):
    def __init__(self, path, parent=None, on_delete=None):
        super().__init__(parent)
        self.path = path
        self.on_delete = on_delete  # 用于删除的回调函数

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # 路径标签
        self.path_label = QLabel(path)
        self.path_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.path_label)

        # 自动提交按钮
        self.autogit_button = QPushButton("自动提交")
        self.autogit_button.clicked.connect(partial(self.trigger_autogit, path))
        layout.addWidget(self.autogit_button)

        # 删除按钮
        self.delete_button = QPushButton("删除")
        self.delete_button.clicked.connect(self.trigger_delete)
        layout.addWidget(self.delete_button)

        # 设置控件的固定高度，确保列表项高度足够
        self.setMinimumHeight(40)  # 设置最小高度
        self.setMaximumHeight(40)  # 设置最大高度，以防拉伸

    def trigger_autogit(self, path):
        datetime_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        autogit(path=path,message=datetime_now, push=True)

    def trigger_delete(self):
        if self.on_delete:
            self.on_delete(self.path)


# --- 主应用程序窗口 ---
class StringListApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Git 自动化工具")
        self.resize(500, 400)

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

        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("在这里输入或选择Git仓库路径...")
        input_layout.addWidget(self.input_field)

        self.browse_button = QPushButton("选择文件夹")
        self.browse_button.clicked.connect(self.browse_for_path)
        input_layout.addWidget(self.browse_button)
        layout.addLayout(input_layout)

        self.save_button = QPushButton("添加")
        self.save_button.clicked.connect(self.add_string)
        layout.addWidget(self.save_button)

        # 列表显示区域
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

    def load_strings(self):
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_strings(self):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.strings, f, ensure_ascii=False, indent=4)

    def populate_list(self):
        self.list_widget.clear()
        for s in self.strings:
            item = QListWidgetItem()
            # 设置列表项的高度为固定值
            item.setSizeHint(QSize(0, 40))
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, PathItemWidget(s, on_delete=self.delete_path))

    def add_string(self):
        new_path = self.input_field.text().strip()
        if new_path:
            if os.path.isdir(new_path):
                if new_path not in self.strings:
                    self.strings.append(new_path)
                    self.save_strings()
                    self.populate_list()
                    self.input_field.clear()
                else:
                    print("路径已存在。")
            else:
                print("这不是一个有效的文件夹路径。")

    def delete_path(self, path):
        if path in self.strings:
            self.strings.remove(path)
            self.save_strings()
            self.populate_list()

    def browse_for_path(self):
        selected_path = QFileDialog.getExistingDirectory(self, "选择Git仓库目录")
        if selected_path:
            self.input_field.setText(selected_path)
            self.add_string()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StringListApp()
    window.show()
    sys.exit(app.exec())