"""
story_image_dialog.py - 美食故事配图上传弹窗
"""

import shutil
import uuid
from pathlib import Path

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QMessageBox, QFrame,
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

from frontend.watercolor_style import COLORS, get_font, get_button_style, get_dialog_style
from backend.paths import user_story_images_dir


IMAGE_FILTER = "图片文件 (*.png *.jpg *.jpeg *.webp *.bmp);;所有文件 (*.*)"


def save_user_story_image(src_path: str) -> str:
    """复制用户选择的图片到故事配图目录，返回相对路径 stories/user/xxx"""
    src = Path(src_path)
    if not src.exists():
        raise FileNotFoundError(src_path)
    ext = src.suffix.lower()
    if ext not in (".png", ".jpg", ".jpeg", ".webp", ".bmp"):
        ext = ".jpg"
    filename = f"user_{uuid.uuid4().hex[:12]}{ext}"
    dest = user_story_images_dir() / filename
    shutil.copy2(src, dest)
    return f"stories/user/{filename}"


class StoryImageDialog(QDialog):
    """选择并预览故事配图"""

    def __init__(self, parent=None, current_image: str = ""):
        super().__init__(parent)
        self._source_path = ""
        self._saved_relative = current_image.strip()
        self.setWindowTitle("上传故事配图")
        self.setMinimumSize(420, 380)
        self._build_ui()
        if current_image:
            self._show_existing(current_image)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 16)
        layout.setSpacing(12)

        hint = QLabel("为这条美食记忆选一张配图，保存故事时会一并写入。")
        hint.setFont(get_font(10))
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {COLORS['text_medium'].name()};")
        layout.addWidget(hint)

        self.preview = QLabel("点击下方按钮选择图片")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumSize(360, 220)
        self.preview.setStyleSheet(f"""
            QLabel {{
                background: {COLORS['bg_warm'].name()};
                border: 1px dashed {COLORS['border'].name()};
                border-radius: 12px;
                color: {COLORS['text_light'].name()};
            }}
        """)
        layout.addWidget(self.preview)

        self.name_lbl = QLabel()
        self.name_lbl.setFont(get_font(9))
        self.name_lbl.setStyleSheet(f"color: {COLORS['text_light'].name()};")
        self.name_lbl.setWordWrap(True)
        layout.addWidget(self.name_lbl)

        btn_row = QHBoxLayout()
        pick_btn = QPushButton("选择图片…")
        pick_btn.setStyleSheet(get_button_style("secondary"))
        pick_btn.clicked.connect(self._pick_image)
        btn_row.addWidget(pick_btn)

        clear_btn = QPushButton("清除配图")
        clear_btn.setStyleSheet(get_button_style("primary", radius=10))
        clear_btn.clicked.connect(self._clear_image)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        action_row = QHBoxLayout()
        action_row.addStretch()
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        action_row.addWidget(cancel_btn)
        ok_btn = QPushButton("确定")
        ok_btn.setStyleSheet(get_button_style("primary"))
        ok_btn.clicked.connect(self._confirm)
        action_row.addWidget(ok_btn)
        layout.addLayout(action_row)

        self.setStyleSheet(get_dialog_style())

    def _pick_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择故事配图", "", IMAGE_FILTER)
        if not path:
            return
        pix = QPixmap(path)
        if pix.isNull():
            QMessageBox.warning(self, "提示", "无法读取该图片，请换一张试试。")
            return
        self._source_path = path
        self._saved_relative = ""
        scaled = pix.scaled(360, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.preview.setPixmap(scaled)
        self.name_lbl.setText(Path(path).name)

    def _show_existing(self, relative_path: str):
        from backend.paths import resolve_story_image
        p = resolve_story_image(relative_path)
        if not p:
            return
        pix = QPixmap(str(p))
        if pix.isNull():
            return
        self._saved_relative = relative_path
        self.preview.setPixmap(pix.scaled(360, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.name_lbl.setText(relative_path)

    def _clear_image(self):
        self._source_path = ""
        self._saved_relative = ""
        self.preview.clear()
        self.preview.setText("点击下方按钮选择图片")
        self.name_lbl.setText("")

    def _confirm(self):
        if self._source_path:
            try:
                self._saved_relative = save_user_story_image(self._source_path)
            except Exception as e:
                QMessageBox.warning(self, "保存失败", f"图片未能保存：{e}")
                return
        self.accept()

    def selected_image(self) -> str:
        return self._saved_relative
