"""Main Window for DLSS Enabler Linux GUI.
Displays installed games in a responsive, modern poster card grid with cover art.
"""

from __future__ import annotations

import os
import subprocess
import urllib.request
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QEvent, QObject, QRect, QSize, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QIcon, QPixmap, QResizeEvent
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ..downloader import DLSSDownloader, ReleaseInfo
from ..i18n import I18nManager, SUPPORTED_LANGUAGES, t
from ..patcher import GamePatcher, PatchResult
from ..scanner import GameInfo, GameScanner
from .game_card import GameCardWidget, GameDetailModal
from .styles import DARK_THEME_QSS


# =============================================================================
# WORKER THREADS (BACKGROUND TASKS)
# =============================================================================
class ScannerWorker(QThread):
    finished = pyqtSignal(list)

    def __init__(self, scanner: GameScanner):
        super().__init__()
        self.scanner = scanner

    def run(self):
        games = self.scanner.scan_all_games()
        self.finished.emit(games)


class DownloadWorker(QThread):
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, downloader: DLSSDownloader):
        super().__init__()
        self.downloader = downloader

    def run(self):
        try:
            rel = self.downloader.check_latest_release()
            self.downloader.download_and_extract(
                rel,
                progress_callback=lambda cur, tot, msg: self.progress.emit(cur, tot, msg),
            )
            self.finished.emit(True, f"Successfully downloaded and installed {rel.name}!")
        except Exception as exc:
            self.finished.emit(False, str(exc))


class ImageLoaderWorker(QThread):
    image_loaded = pyqtSignal(str, QPixmap)

    def __init__(self, game_id: str, url: str, cache_dir: Path):
        super().__init__()
        self.game_id = game_id
        self.url = url
        self.cache_dir = cache_dir

    def run(self):
        try:
            cache_file = self.cache_dir / f"{self.game_id}.jpg"
            if not cache_file.exists():
                req = urllib.request.Request(self.url, headers={"User-Agent": "DLSS-Enabler-Linux/1.0"})
                with urllib.request.urlopen(req, timeout=8) as resp, open(cache_file, "wb") as f:
                    f.write(resp.read())

            if cache_file.exists():
                pix = QPixmap(str(cache_file))
                if not pix.isNull():
                    self.image_loaded.emit(self.game_id, pix)
        except Exception:
            pass


# =============================================================================
# MAIN WINDOW (GRID VIEW)
# =============================================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.i18n = I18nManager.get_instance()
        self.i18n.add_language_listener(self.update_ui_translations)

        self.resize(1160, 780)
        self.setMinimumSize(920, 600)
        self.setStyleSheet(DARK_THEME_QSS)

        # Core engines
        self.scanner = GameScanner()
        self.downloader = DLSSDownloader()
        self.patcher = GamePatcher(self.downloader)

        self.all_games: list[GameInfo] = []
        self.filtered_games: list[GameInfo] = []
        self.card_widgets: dict[str, GameCardWidget] = {}

        self.covers_cache = Path.home() / ".cache" / "dlss-enabler-linux" / "covers"
        self.covers_cache.mkdir(parents=True, exist_ok=True)

        self.active_workers: list[QThread] = []

        self.init_ui()
        self.update_ui_translations()
        self.refresh_core_status()
        self.start_scan_games()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Top Navigation Bar
        top_header = self._create_top_header()
        main_layout.addWidget(top_header)

        # Download / Progress Banner (hidden by default)
        self.progress_banner = self._create_progress_banner()
        main_layout.addWidget(self.progress_banner)

        # 2. Subheader / Filter Bar
        filter_bar = self._create_filter_bar()
        main_layout.addWidget(filter_bar)

        # 3. Game Cards Grid View (Scroll Area)
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("GridScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.grid_container = QWidget()
        self.grid_container.setObjectName("GridContainer")
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(24, 20, 24, 24)
        self.grid_layout.setSpacing(18)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.scroll_area.setWidget(self.grid_container)
        main_layout.addWidget(self.scroll_area, stretch=1)

        # 4. Empty State Widget (shown when no games match filters)
        self.empty_state_widget = self._create_empty_state_widget()
        self.empty_state_widget.hide()
        main_layout.addWidget(self.empty_state_widget, stretch=1)

    # =========================================================================
    # HEADER WIDGET
    # =========================================================================
    def _create_top_header(self) -> QWidget:
        header = QFrame()
        header.setObjectName("TopHeader")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 10, 24, 10)
        layout.setSpacing(14)

        # Logo & Title
        title_vbox = QVBoxLayout()
        title_vbox.setSpacing(1)

        self.app_title_label = QLabel()
        self.app_title_label.setObjectName("AppTitle")
        self.app_subtitle_label = QLabel()
        self.app_subtitle_label.setObjectName("AppSubtitle")

        title_vbox.addWidget(self.app_title_label)
        title_vbox.addWidget(self.app_subtitle_label)
        layout.addLayout(title_vbox)

        layout.addStretch()

        # Core Status Card
        self.core_status_card = QFrame()
        self.core_status_card.setObjectName("CoreVersionCard")
        core_layout = QHBoxLayout(self.core_status_card)
        core_layout.setContentsMargins(10, 4, 10, 4)
        core_layout.setSpacing(10)

        self.core_status_label = QLabel(t("core_checking"))
        self.core_status_label.setObjectName("CoreVersionLabel")
        core_layout.addWidget(self.core_status_label)

        self.btn_update_core = QPushButton()
        self.btn_update_core.setObjectName("btn_update_core")
        self.btn_update_core.setProperty("class", "btn-secondary")
        self.btn_update_core.setFixedHeight(28)
        self.btn_update_core.clicked.connect(self.start_download_core)
        core_layout.addWidget(self.btn_update_core)

        layout.addWidget(self.core_status_card)

        # Add Custom Game Button
        self.btn_add_custom = QPushButton()
        self.btn_add_custom.setProperty("class", "btn-secondary")
        self.btn_add_custom.setFixedHeight(32)
        self.btn_add_custom.clicked.connect(self.on_add_custom_game)
        layout.addWidget(self.btn_add_custom)

        # Rescan Games Button
        self.btn_rescan = QPushButton()
        self.btn_rescan.setProperty("class", "btn-secondary")
        self.btn_rescan.setFixedHeight(32)
        self.btn_rescan.clicked.connect(self.start_scan_games)
        layout.addWidget(self.btn_rescan)

        # Language Switcher
        self.lang_combo = QComboBox()
        self.lang_combo.setFixedWidth(130)
        self.lang_combo.setFixedHeight(32)
        for code, label in SUPPORTED_LANGUAGES:
            self.lang_combo.addItem(label, code)

        idx = self.lang_combo.findData(self.i18n.current_lang)
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)
        self.lang_combo.currentIndexChanged.connect(self.on_language_changed)
        layout.addWidget(self.lang_combo)

        return header

    def on_language_changed(self, index: int):
        code = self.lang_combo.currentData()
        if code:
            self.i18n.set_language(code)

    def _create_progress_banner(self) -> QWidget:
        banner = QFrame()
        banner.setStyleSheet("background-color: #121829; border-bottom: 1px solid #1f2740; padding: 6px 24px;")
        layout = QHBoxLayout(banner)
        layout.setContentsMargins(16, 6, 16, 6)
        layout.setSpacing(14)

        self.progress_label = QLabel()
        self.progress_label.setStyleSheet("color: #38bdf8; font-weight: 600;")
        layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedWidth(280)
        layout.addWidget(self.progress_bar)

        banner.hide()
        return banner

    # =========================================================================
    # FILTER BAR
    # =========================================================================
    def _create_filter_bar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("FilterBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(24, 8, 24, 8)
        layout.setSpacing(14)

        # Search Bar
        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchBar")
        self.search_input.textChanged.connect(self.apply_filters)
        layout.addWidget(self.search_input)

        # Platform Filter Buttons
        self.launcher_filter_group = QButtonGroup(self)
        self.btn_filter_all = QPushButton()
        self.btn_filter_steam = QPushButton()
        self.btn_filter_heroic = QPushButton()
        self.btn_filter_lutris = QPushButton()
        self.btn_filter_custom = QPushButton()

        for i, btn in enumerate([self.btn_filter_all, self.btn_filter_steam, self.btn_filter_heroic, self.btn_filter_lutris, self.btn_filter_custom]):
            btn.setProperty("class", "filter-chip")
            btn.setCheckable(True)
            self.launcher_filter_group.addButton(btn, i)
            layout.addWidget(btn)
            btn.clicked.connect(self.apply_filters)

        self.btn_filter_all.setChecked(True)

        # Separator line
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("color: #1f2538; max-height: 20px;")
        layout.addWidget(sep)

        # Status Filter Buttons
        self.status_filter_group = QButtonGroup(self)
        self.btn_status_all = QPushButton()
        self.btn_status_patched = QPushButton()
        self.btn_status_unpatched = QPushButton()

        for i, btn in enumerate([self.btn_status_all, self.btn_status_patched, self.btn_status_unpatched]):
            btn.setProperty("class", "filter-chip")
            btn.setCheckable(True)
            self.status_filter_group.addButton(btn, i)
            layout.addWidget(btn)
            btn.clicked.connect(self.apply_filters)

        self.btn_status_all.setChecked(True)

        layout.addStretch()

        # Count badge
        self.count_badge = QLabel()
        self.count_badge.setStyleSheet("""
            background-color: #161b28;
            color: #818cf8;
            font-size: 11px;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 12px;
            border: 1px solid #252e44;
        """)
        layout.addWidget(self.count_badge)

        return bar

    # =========================================================================
    # EMPTY STATE
    # =========================================================================
    def _create_empty_state_widget(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)

        icon_lbl = QLabel("🎮")
        icon_lbl.setStyleSheet("font-size: 52px;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_lbl)

        self.empty_state_title = QLabel()
        self.empty_state_title.setStyleSheet("font-size: 18px; font-weight: 800; color: #ffffff;")
        self.empty_state_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.empty_state_title)

        self.empty_state_desc = QLabel()
        self.empty_state_desc.setStyleSheet("color: #64748b; font-size: 13px; max-width: 440px;")
        self.empty_state_desc.setWordWrap(True)
        self.empty_state_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.empty_state_desc)

        return widget

    # =========================================================================
    # TRANSLATION UPDATE
    # =========================================================================
    def update_ui_translations(self):
        self.setWindowTitle(f"{t('app_title')} - {t('app_subtitle')}")
        self.app_title_label.setText(t("app_title"))
        self.app_subtitle_label.setText(t("app_subtitle"))

        self.btn_add_custom.setText(t("btn_add_game"))
        self.btn_rescan.setText(t("btn_refresh"))

        self.search_input.setPlaceholderText(t("search_placeholder"))
        self.btn_filter_all.setText(t("filter_all"))
        self.btn_filter_steam.setText(t("filter_steam"))
        self.btn_filter_heroic.setText(t("filter_heroic"))
        self.btn_filter_lutris.setText(t("filter_lutris"))
        self.btn_filter_custom.setText(t("filter_custom"))

        self.btn_status_all.setText(t("filter_status_all"))
        self.btn_status_patched.setText(t("filter_status_patched"))
        self.btn_status_unpatched.setText(t("filter_status_unpatched"))

        self.empty_state_title.setText(t("no_games_found"))
        self.empty_state_desc.setText(t("no_games_desc"))

        self.refresh_core_status()
        self.update_count_badge()

        # Update all active cards
        for card in self.card_widgets.values():
            card.update()

    def update_count_badge(self):
        total = len(self.filtered_games)
        patched = sum(1 for g in self.filtered_games if g.is_patched)
        self.count_badge.setText(f"{total} games • {patched} patched")

    # =========================================================================
    # CORE ENGINE STATUS & UPDATES
    # =========================================================================
    def refresh_core_status(self):
        cached = self.downloader.get_cached_version()
        if cached:
            ver = cached.get("tag", "v0.9.4")
            self.core_status_label.setText(t("core_ready", ver=ver))
            self.core_status_label.setStyleSheet("color: #10b981; font-weight: 700;")
            self.btn_update_core.setText(t("btn_update_core"))
        else:
            self.core_status_label.setText(t("core_missing"))
            self.core_status_label.setStyleSheet("color: #f59e0b; font-weight: 700;")
            self.btn_update_core.setText(t("btn_download_core"))

    def start_download_core(self):
        self.progress_banner.show()
        self.progress_bar.setValue(0)
        self.progress_label.setText(t("download_connecting"))
        self.btn_update_core.setEnabled(False)

        worker = DownloadWorker(self.downloader)
        worker.progress.connect(self.on_download_progress)
        worker.finished.connect(self.on_download_finished)
        self.active_workers.append(worker)
        worker.start()

    def on_download_progress(self, current: int, total: int, msg: str):
        pct = int(current * 100 / total) if total > 0 else 0
        self.progress_bar.setValue(pct)
        self.progress_label.setText(msg)

    def on_download_finished(self, success: bool, msg: str):
        self.progress_banner.hide()
        self.btn_update_core.setEnabled(True)
        self.refresh_core_status()
        if success:
            QMessageBox.information(self, t("dialog_download_success_title"), msg)
        else:
            QMessageBox.warning(self, t("dialog_download_fail_title"), t("dialog_download_fail_msg", err=msg))

    # =========================================================================
    # SCANNING & GRID POPULATION
    # =========================================================================
    def start_scan_games(self):
        self.btn_rescan.setEnabled(False)
        worker = ScannerWorker(self.scanner)
        worker.finished.connect(self.on_scan_finished)
        self.active_workers.append(worker)
        worker.start()

    def on_scan_finished(self, games: list[GameInfo]):
        self.btn_rescan.setEnabled(True)
        self.all_games = games
        self.apply_filters()

        # Trigger background image downloads for games missing local covers
        for game in self.all_games:
            if not game.local_cover_path and game.cover_url:
                cached_file = self.covers_cache / f"{game.id}.jpg"
                if not cached_file.exists():
                    worker = ImageLoaderWorker(game.id, game.cover_url, self.covers_cache)
                    worker.image_loaded.connect(self.on_cover_loaded)
                    self.active_workers.append(worker)
                    worker.start()

    def on_cover_loaded(self, game_id: str, pix: QPixmap):
        if game_id in self.card_widgets:
            self.card_widgets[game_id].set_cover_pixmap(pix)

    def apply_filters(self):
        query = self.search_input.text().strip().lower()
        launcher_btn_id = self.launcher_filter_group.checkedId()
        status_btn_id = self.status_filter_group.checkedId()

        filtered: list[GameInfo] = []
        for g in self.all_games:
            # Search
            if query and query not in g.title.lower():
                continue

            # Launcher filter: 0=All, 1=Steam, 2=Heroic, 3=Lutris, 4=Custom
            if launcher_btn_id == 1 and g.launcher != "Steam":
                continue
            elif launcher_btn_id == 2 and not g.launcher.startswith("Heroic"):
                continue
            elif launcher_btn_id == 3 and g.launcher != "Lutris":
                continue
            elif launcher_btn_id == 4 and g.launcher != "Custom":
                continue

            # Status filter: 0=All, 1=Patched, 2=Unpatched
            if status_btn_id == 1 and not g.is_patched:
                continue
            elif status_btn_id == 2 and g.is_patched:
                continue

            filtered.append(g)

        self.filtered_games = filtered
        self.update_count_badge()
        self.render_grid()

    def render_grid(self):
        # Clear existing items in grid
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        self.card_widgets.clear()

        if not self.filtered_games:
            self.scroll_area.hide()
            self.empty_state_widget.show()
            return

        self.empty_state_widget.hide()
        self.scroll_area.show()

        # Calculate columns based on width
        container_width = self.scroll_area.viewport().width() or 1000
        card_total_width = GameCardWidget.CARD_WIDTH + 18
        cols = max(3, container_width // card_total_width)

        for index, game in enumerate(self.filtered_games):
            card = GameCardWidget(game, self.covers_cache)
            card.clicked.connect(self.open_game_modal)
            self.card_widgets[game.id] = card

            row = index // cols
            col = index % cols
            self.grid_layout.addWidget(card, row, col)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        # Re-layout grid when window is resized
        if self.filtered_games:
            self.render_grid()

    # =========================================================================
    # GAME CARD CLICKED -> OPEN MODAL
    # =========================================================================
    def open_game_modal(self, game: GameInfo):
        modal = GameDetailModal(game, self.patcher, self)
        modal.exec()

        # Re-render cards after modal close to reflect any patch/unpatch changes
        if game.id in self.card_widgets:
            self.card_widgets[game.id].update()
        self.update_count_badge()

    def on_add_custom_game(self):
        dpath = QFileDialog.getExistingDirectory(
            self,
            t("dialog_select_game_folder"),
            str(Path.home()),
        )
        if dpath:
            new_game = self.scanner.add_custom_game(Path(dpath))
            self.all_games.append(new_game)
            self.apply_filters()
            self.open_game_modal(new_game)
