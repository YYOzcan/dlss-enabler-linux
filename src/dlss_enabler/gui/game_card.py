"""Game Card Widget and Detail Modal for DLSS Enabler Linux GUI.
Displays vertical game cover art in a clean, elegant poster card grid.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QEvent, QPoint, QRect, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont, QIcon, QPainter, QPainterPath, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..i18n import t
from ..patcher import GamePatcher, PatchResult
from ..quirks import SUPPORTED_HOOK_METHODS, get_game_quirk
from ..scanner import GameInfo


# =============================================================================
# GAME POSTER CARD WIDGET
# =============================================================================
class GameCardWidget(QWidget):
    clicked = pyqtSignal(GameInfo)

    CARD_WIDTH = 190
    CARD_HEIGHT = 275
    COVER_HEIGHT = 200

    def __init__(self, game: GameInfo, covers_cache: Path, parent=None):
        super().__init__(parent)
        self.game = game
        self.covers_cache = covers_cache
        self.pixmap: Optional[QPixmap] = None
        self.is_hovered = False

        self.setFixedSize(self.CARD_WIDTH, self.CARD_HEIGHT)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

        self.load_cover()

    def load_cover(self):
        """Load cover art from local file or cache."""
        # 1. Direct local cover (Steam librarycache or Heroic icons)
        if self.game.local_cover_path and os.path.exists(self.game.local_cover_path):
            pix = QPixmap(self.game.local_cover_path)
            if not pix.isNull():
                self.pixmap = pix
                self.update()
                return

        # 2. Downloaded cache file
        cached_file = self.covers_cache / f"{self.game.id}.jpg"
        if cached_file.exists():
            pix = QPixmap(str(cached_file))
            if not pix.isNull():
                self.pixmap = pix
                self.update()
                return

    def set_cover_pixmap(self, pix: QPixmap):
        self.pixmap = pix
        self.update()

    def enterEvent(self, event):
        self.is_hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.game)
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        w = self.width()
        h = self.height()
        radius = 12

        # Card Background Path
        card_path = QPainterPath()
        card_path.addRoundedRect(0.5, 0.5, w - 1, h - 1, radius, radius)

        # Draw Base Background
        bg_color = QColor("#171c2b") if self.is_hovered else QColor("#121520")
        painter.fillPath(card_path, bg_color)

        # 1. Draw Cover Image in Top Area
        cover_rect = QRect(0, 0, w, self.COVER_HEIGHT)
        cover_path = QPainterPath()
        cover_path.setFillRule(Qt.FillRule.WindingFill)
        cover_path.addRoundedRect(0.0, 0.0, float(w), float(self.COVER_HEIGHT), float(radius), float(radius))
        # Square off bottom corners so only top corners of cover are rounded
        cover_path.addRect(0.0, float(radius), float(w), float(self.COVER_HEIGHT - radius))

        painter.save()
        painter.setClipPath(cover_path)

        if self.pixmap and not self.pixmap.isNull():
            # Fill cover background first with dark backdrop
            painter.fillRect(0, 0, w, self.COVER_HEIGHT, QColor("#121520"))

            # Draw scaled cover image filling the cover rectangle nicely
            scaled = self.pixmap.scaled(
                QSize(w, self.COVER_HEIGHT),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            # Center crop
            x_off = max(0, (scaled.width() - w) // 2)
            y_off = max(0, (scaled.height() - self.COVER_HEIGHT) // 2)
            painter.drawPixmap(0, 0, scaled, x_off, y_off, w, self.COVER_HEIGHT)

            # Gradient scrim at bottom of cover for smooth transition into title
            from PyQt6.QtGui import QLinearGradient
            lg = QLinearGradient(0, self.COVER_HEIGHT - 45, 0, self.COVER_HEIGHT)
            lg.setColorAt(0, QColor(0, 0, 0, 0))
            lg.setColorAt(1, QColor(18, 21, 32, 230))
            painter.fillRect(0, self.COVER_HEIGHT - 45, w, 45, lg)
        else:
            # Elegant Fallback: Dark gradient with game initials
            from PyQt6.QtGui import QLinearGradient
            lg = QLinearGradient(0, 0, w, self.COVER_HEIGHT)
            lg.setColorAt(0, QColor("#1e2436"))
            lg.setColorAt(1, QColor("#10131d"))
            painter.fillRect(0, 0, w, self.COVER_HEIGHT, lg)

            # Initials badge
            initials = "".join([part[0] for part in self.game.title.split()[:2] if part]).upper()
            painter.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
            painter.setPen(QColor("#4f46e5"))
            painter.drawText(cover_rect, Qt.AlignmentFlag.AlignCenter, initials)

        painter.restore()

        # 2. Draw Top Left Platform Badge
        self._draw_platform_badge(painter)

        # 3. Draw Top Right Status Badge
        self._draw_status_badge(painter, w)

        # 4. Draw Bottom Title & Subtitle
        self._draw_bottom_text(painter, w, h)

        # 5. Draw Border
        border_color = QColor("#6366f1") if self.is_hovered else QColor("#1f2538")
        border_width = 1.5 if self.is_hovered else 1.0
        from PyQt6.QtGui import QPen
        painter.setPen(QPen(border_color, border_width))
        painter.drawPath(card_path)

        painter.end()

    def _draw_platform_badge(self, painter: QPainter):
        launcher_name = self.game.launcher.upper()
        if "STEAM" in launcher_name:
            label = "STEAM"
            color = QColor("#38bdf8")
        elif "HEROIC" in launcher_name:
            label = "HEROIC"
            color = QColor("#c084fc")
        elif "LUTRIS" in launcher_name:
            label = "LUTRIS"
            color = QColor("#fb923c")
        else:
            label = "CUSTOM"
            color = QColor("#94a3b8")

        painter.save()
        font = QFont("Segoe UI", 8, QFont.Weight.Bold)
        painter.setFont(font)

        badge_w = painter.fontMetrics().horizontalAdvance(label) + 12
        badge_h = 18
        badge_rect = QRect(8, 8, badge_w, badge_h)

        # Background pill
        bg_path = QPainterPath()
        bg_path.addRoundedRect(8, 8, badge_w, badge_h, 4, 4)
        painter.fillPath(bg_path, QColor(10, 13, 20, 200))

        # Text
        painter.setPen(color)
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, label)
        painter.restore()

    def _draw_status_badge(self, painter: QPainter, width: int):
        painter.save()
        font = QFont("Segoe UI", 8, QFont.Weight.Bold)
        painter.setFont(font)

        if self.game.is_patched:
            label = t("card_dlss_active")
            text_color = QColor("#34d399")
            bg_color = QColor(6, 78, 59, 230)
            border_color = QColor("#059669")
        elif self.game.is_native_linux and not self.game.executable_path:
            label = t("card_native")
            text_color = QColor("#38bdf8")
            bg_color = QColor(12, 74, 110, 220)
            border_color = QColor("#0284c7")
        else:
            label = t("card_ready")
            text_color = QColor("#94a3b8")
            bg_color = QColor(22, 27, 40, 210)
            border_color = QColor("#334155")

        badge_w = painter.fontMetrics().horizontalAdvance(label) + 14
        badge_h = 20
        badge_x = width - badge_w - 8
        badge_y = 8
        badge_rect = QRect(badge_x, badge_y, badge_w, badge_h)

        badge_path = QPainterPath()
        badge_path.addRoundedRect(badge_x, badge_y, badge_w, badge_h, 6, 6)
        painter.fillPath(badge_path, bg_color)

        from PyQt6.QtGui import QPen
        painter.setPen(QPen(border_color, 1))
        painter.drawPath(badge_path)

        painter.setPen(text_color)
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, label)
        painter.restore()

    def _draw_bottom_text(self, painter: QPainter, width: int, height: int):
        painter.save()
        bottom_rect = QRect(10, self.COVER_HEIGHT + 6, width - 20, height - self.COVER_HEIGHT - 12)

        # Title
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.setPen(QColor("#ffffff") if self.is_hovered else QColor("#e2e8f0"))

        fm = painter.fontMetrics()
        elided_title = fm.elidedText(self.game.title, Qt.TextElideMode.ElideRight, width - 20)
        painter.drawText(QRect(10, self.COVER_HEIGHT + 8, width - 20, 22), Qt.AlignmentFlag.AlignLeft, elided_title)

        # Subtitle / Hook Method
        painter.setFont(QFont("Segoe UI", 8, QFont.Weight.DemiBold))
        if self.game.is_patched:
            painter.setPen(QColor("#10b981"))
            sub_text = f"✓ {self.game.patch_method}.dll"
        elif self.game.is_native_linux and not self.game.executable_path:
            painter.setPen(QColor("#38bdf8"))
            sub_text = "Native Linux build"
        else:
            painter.setPen(QColor("#64748b"))
            sub_text = "Ready to patch"

        painter.drawText(QRect(10, self.COVER_HEIGHT + 32, width - 20, 18), Qt.AlignmentFlag.AlignLeft, sub_text)

        # Hover CTA Hint
        if self.is_hovered:
            painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            painter.setPen(QColor("#818cf8"))
            painter.drawText(QRect(10, self.COVER_HEIGHT + 52, width - 20, 16), Qt.AlignmentFlag.AlignRight, "Click to manage →")

        painter.restore()


# =============================================================================
# GAME DETAIL MODAL DIALOG
# =============================================================================
class GameDetailModal(QDialog):
    def __init__(self, game: GameInfo, patcher: GamePatcher, parent=None):
        super().__init__(parent)
        self.game = game
        self.patcher = patcher

        self.setObjectName("GameModal")
        self.setWindowTitle(f"{game.title} - DLSS Enabler")
        self.setFixedSize(680, 600)
        self.setModal(True)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        # 1. Header Card (Title, Platform, Patch Status)
        header_card = QFrame()
        header_card.setObjectName("ModalHeaderCard")
        h_layout = QHBoxLayout(header_card)
        h_layout.setContentsMargins(16, 16, 16, 16)
        h_layout.setSpacing(16)

        # Cover Preview if available
        self.cover_lbl = QLabel()
        self.cover_lbl.setFixedSize(90, 130)
        self.cover_lbl.setStyleSheet("background-color: #1a1e2c; border-radius: 8px; border: 1px solid #28324a;")
        self.cover_lbl.setScaledContents(True)

        if self.game.local_cover_path and os.path.exists(self.game.local_cover_path):
            self.cover_lbl.setPixmap(QPixmap(self.game.local_cover_path))
        else:
            cached_file = Path.home() / ".cache" / "dlss-enabler-linux" / "covers" / f"{self.game.id}.jpg"
            if cached_file.exists():
                self.cover_lbl.setPixmap(QPixmap(str(cached_file)))
            else:
                self.cover_lbl.setText("Cover")
                self.cover_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        h_layout.addWidget(self.cover_lbl)

        # Title and details
        meta_vbox = QVBoxLayout()
        meta_vbox.setSpacing(4)

        title_lbl = QLabel(self.game.title)
        title_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #ffffff;")
        title_lbl.setWordWrap(True)
        meta_vbox.addWidget(title_lbl)

        platform_lbl = QLabel(f"Launcher: {self.game.launcher}  •  AppID / Slug: {self.game.id}")
        platform_lbl.setStyleSheet("color: #818cf8; font-size: 12px; font-weight: 600;")
        meta_vbox.addWidget(platform_lbl)

        # Status Badge
        status_row = QHBoxLayout()
        status_row.setSpacing(8)

        self.status_badge = QLabel()
        self.update_status_badge()
        status_row.addWidget(self.status_badge)
        status_row.addStretch()
        meta_vbox.addLayout(status_row)

        h_layout.addLayout(meta_vbox, stretch=1)
        layout.addWidget(header_card)

        # 2. Executable / Target Path Section
        path_card = QFrame()
        path_card.setObjectName("ModalSectionCard")
        p_layout = QVBoxLayout(path_card)
        p_layout.setSpacing(8)

        target_lbl = QLabel(t("target_exe_header"))
        target_lbl.setStyleSheet("font-size: 11px; font-weight: 800; color: #818cf8; letter-spacing: 0.5px;")
        p_layout.addWidget(target_lbl)

        exe_row = QHBoxLayout()
        self.exe_input = QLineEdit(self.game.executable_path or self.game.install_path)
        self.exe_input.setReadOnly(True)
        self.exe_input.setStyleSheet("background-color: #0b0d14; font-family: monospace; font-size: 11px;")
        exe_row.addWidget(self.exe_input, stretch=1)

        btn_browse = QPushButton(t("btn_browse"))
        btn_browse.setProperty("class", "btn-secondary")
        btn_browse.clicked.connect(self.on_browse_exe)
        exe_row.addWidget(btn_browse)
        p_layout.addLayout(exe_row)

        layout.addWidget(path_card)

        # 3. Quirk Note (if any)
        quirk = get_game_quirk(self.game.id, self.game.title)
        notes = quirk.get("notes") if quirk else self.game.quirk_notes
        if notes:
            q_card = QFrame()
            q_card.setStyleSheet("background-color: #1a1e28; border-left: 4px solid #f59e0b; border-radius: 6px; padding: 10px;")
            q_box = QVBoxLayout(q_card)
            q_box.setContentsMargins(8, 6, 8, 6)
            q_lbl = QLabel(f"💡 {notes}")
            q_lbl.setStyleSheet("color: #fde68a; font-size: 12px;")
            q_lbl.setWordWrap(True)
            q_box.addWidget(q_lbl)
            layout.addWidget(q_card)

        # 4. Method Selection & Launch Options
        cfg_card = QFrame()
        cfg_card.setObjectName("ModalSectionCard")
        cfg_layout = QVBoxLayout(cfg_card)
        cfg_layout.setSpacing(10)

        method_row = QHBoxLayout()
        method_lbl = QLabel(t("hook_proxy_label"))
        method_lbl.setStyleSheet("font-weight: 600; color: #cbd5e1;")
        method_row.addWidget(method_lbl)

        self.method_combo = QComboBox()
        for key, desc in SUPPORTED_HOOK_METHODS:
            self.method_combo.addItem(desc, key)

        rec_method = (quirk.get("recommended_method") if quirk else None) or self.game.recommended_method or "version"
        idx = self.method_combo.findData(rec_method)
        if idx >= 0:
            self.method_combo.setCurrentIndex(idx)
        self.method_combo.currentIndexChanged.connect(self.update_launch_options)
        method_row.addWidget(self.method_combo, stretch=1)
        cfg_layout.addLayout(method_row)

        # Launch options input + copy
        launch_row = QHBoxLayout()
        self.launch_input = QLineEdit()
        self.launch_input.setReadOnly(True)
        self.launch_input.setStyleSheet("background-color: #0b0d14; font-family: monospace; font-size: 11px; color: #38bdf8;")
        launch_row.addWidget(self.launch_input, stretch=1)

        self.btn_copy = QPushButton(t("btn_copy"))
        self.btn_copy.setProperty("class", "btn-secondary")
        self.btn_copy.clicked.connect(self.copy_launch_options)
        launch_row.addWidget(self.btn_copy)
        cfg_layout.addLayout(launch_row)

        # Launcher instructions
        self.instructions_lbl = QLabel()
        self.instructions_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.instructions_lbl.setWordWrap(True)
        cfg_layout.addWidget(self.instructions_lbl)

        layout.addWidget(cfg_card)

        self.update_launch_options()

        # 5. Primary Buttons Row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.btn_install = QPushButton(t("btn_reinstall") if self.game.is_patched else t("btn_install"))
        self.btn_install.setProperty("class", "btn-primary")
        self.btn_install.setFixedHeight(42)
        self.btn_install.clicked.connect(self.on_install)
        btn_row.addWidget(self.btn_install, stretch=2)

        self.btn_uninstall = QPushButton(t("btn_uninstall"))
        self.btn_uninstall.setProperty("class", "btn-danger")
        self.btn_uninstall.setFixedHeight(42)
        self.btn_uninstall.clicked.connect(self.on_uninstall)
        self.btn_uninstall.setVisible(self.game.is_patched)
        btn_row.addWidget(self.btn_uninstall, stretch=1)

        btn_folder = QPushButton(t("btn_open_folder"))
        btn_folder.setProperty("class", "btn-secondary")
        btn_folder.setFixedHeight(42)
        btn_folder.clicked.connect(self.on_open_folder)
        btn_row.addWidget(btn_folder, stretch=1)

        btn_close = QPushButton(t("btn_close"))
        btn_close.setProperty("class", "btn-secondary")
        btn_close.setFixedHeight(42)
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)

        layout.addLayout(btn_row)

    def update_status_badge(self):
        if self.game.is_patched:
            self.status_badge.setText(f"{t('badge_patched')} • {self.game.patch_method}.dll")
            self.status_badge.setStyleSheet("""
                background-color: #064e3b;
                color: #34d399;
                font-weight: 700;
                font-size: 11px;
                padding: 4px 10px;
                border-radius: 6px;
                border: 1px solid #059669;
            """)
        elif self.game.is_native_linux and not self.game.executable_path:
            self.status_badge.setText(t("badge_native_linux"))
            self.status_badge.setStyleSheet("""
                background-color: #1e293b;
                color: #38bdf8;
                font-weight: 600;
                font-size: 11px;
                padding: 4px 10px;
                border-radius: 6px;
                border: 1px solid #0284c7;
            """)
        else:
            self.status_badge.setText(t("badge_unpatched"))
            self.status_badge.setStyleSheet("""
                background-color: #1e2436;
                color: #94a3b8;
                font-weight: 600;
                font-size: 11px;
                padding: 4px 10px;
                border-radius: 6px;
                border: 1px solid #262f44;
            """)

    def update_launch_options(self):
        method = self.method_combo.currentData() or "version"
        cmd = self.patcher.generate_launch_options(method)
        self.launch_input.setText(cmd)
        inst = self.patcher.get_launcher_instructions(self.game.launcher, method)
        self.instructions_lbl.setText(f"ℹ️ {inst}")

    def copy_launch_options(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.launch_input.text())
        self.btn_copy.setText(t("toast_copied"))
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(1500, lambda: self.btn_copy.setText(t("btn_copy")))

    def on_browse_exe(self):
        start_dir = self.game.install_path
        fpath, _ = QFileDialog.getOpenFileName(
            self,
            t("dialog_select_game_exe"),
            start_dir,
            "Executables (*.exe);;All Files (*)"
        )
        if fpath:
            self.game.executable_path = fpath
            self.exe_input.setText(fpath)

    def on_install(self):
        method = self.method_combo.currentData() or "version"
        self.btn_install.setEnabled(False)
        self.btn_install.setText(t("btn_installing"))
        QApplication.processEvents()

        res: PatchResult = self.patcher.patch_game(self.game, method=method)

        self.btn_install.setEnabled(True)
        if res.success:
            self.update_status_badge()
            self.btn_install.setText(t("btn_reinstall"))
            self.btn_uninstall.setVisible(True)
            QMessageBox.information(
                self,
                t("dialog_install_success_title"),
                t(
                    "dialog_install_success_msg",
                    method=res.method,
                    target=res.target_dir,
                    opts=res.launch_options
                )
            )
        else:
            QMessageBox.critical(self, t("dialog_install_fail_title"), f"{res.message}")

    def on_uninstall(self):
        reply = QMessageBox.question(
            self,
            t("dialog_uninstall_confirm_title"),
            t("dialog_uninstall_confirm_msg", title=self.game.title),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        success, msg = self.patcher.unpatch_game(self.game)
        if success:
            self.update_status_badge()
            self.btn_install.setText(t("btn_install"))
            self.btn_uninstall.setVisible(False)
            QMessageBox.information(self, t("dialog_restored_title"), msg)
        else:
            QMessageBox.warning(self, t("dialog_uninstall_notice_title"), msg)

    def on_open_folder(self):
        target_dir = self.patcher.get_target_directory(self.game)
        if target_dir.exists():
            subprocess.run(["xdg-open", str(target_dir)], check=False)
