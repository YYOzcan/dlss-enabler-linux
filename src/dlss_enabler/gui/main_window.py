"""Main Window for DLSS Enabler Linux GUI."""

from __future__ import annotations

import os
import subprocess
import urllib.request
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QObject, QSize, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QComboBox,
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
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
from ..patcher import GamePatcher, PatchResult
from ..quirks import SUPPORTED_HOOK_METHODS, get_game_quirk
from ..scanner import GameInfo, GameScanner
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
                progress_callback=lambda cur, tot, msg: self.progress.emit(cur, tot, msg)
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
                with urllib.request.urlopen(req, timeout=5) as resp, open(cache_file, "wb") as f:
                    f.write(resp.read())

            if cache_file.exists():
                pix = QPixmap(str(cache_file))
                if not pix.isNull():
                    self.image_loaded.emit(self.game_id, pix)
        except Exception:
            pass


# =============================================================================
# CUSTOM GAME LIST ITEM WIDGET
# =============================================================================
class GameListItemWidget(QWidget):
    def __init__(self, game: GameInfo, parent=None):
        super().__init__(parent)
        self.game = game
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(12)

        # Platform Pill
        self.platform_label = QLabel(self.game.launcher)
        self.platform_label.setStyleSheet("""
            background-color: #1e2538;
            color: #818cf8;
            font-size: 10px;
            font-weight: 700;
            padding: 3px 7px;
            border-radius: 4px;
        """)
        self.platform_label.setFixedWidth(78)
        self.platform_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.platform_label)

        # Info Box (Title + Path hint)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        self.title_label = QLabel(self.game.title)
        self.title_label.setStyleSheet("font-weight: 700; font-size: 13px; color: #f8fafc;")
        info_layout.addWidget(self.title_label)

        short_path = self.game.install_path
        if len(short_path) > 42:
            short_path = "..." + short_path[-39:]
        self.path_label = QLabel(short_path)
        self.path_label.setStyleSheet("font-size: 11px; color: #64748b;")
        info_layout.addWidget(self.path_label)

        layout.addLayout(info_layout, stretch=1)

        # Status Badge
        self.status_badge = QLabel()
        self.update_status_badge()
        layout.addWidget(self.status_badge)

    def update_status_badge(self):
        if self.game.is_patched:
            method_str = f" • {self.game.patch_method}.dll" if self.game.patch_method else ""
            self.status_badge.setText(f"✓ Patched{method_str}")
            self.status_badge.setStyleSheet("""
                background-color: #064e3b;
                color: #34d399;
                font-weight: 700;
                font-size: 11px;
                padding: 4px 8px;
                border-radius: 6px;
                border: 1px solid #059669;
            """)
        else:
            self.status_badge.setText("Not Patched")
            self.status_badge.setStyleSheet("""
                background-color: #1e2436;
                color: #94a3b8;
                font-weight: 600;
                font-size: 11px;
                padding: 4px 8px;
                border-radius: 6px;
                border: 1px solid #262f44;
            """)


# =============================================================================
# MAIN WINDOW
# =============================================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DLSS Enabler for Linux - Universal Upscaling & Frame Gen Manager")
        self.resize(1180, 760)
        self.setMinimumSize(960, 620)
        self.setStyleSheet(DARK_THEME_QSS)

        # Core engines
        self.scanner = GameScanner()
        self.downloader = DLSSDownloader()
        self.patcher = GamePatcher(self.downloader)

        self.all_games: list[GameInfo] = []
        self.filtered_games: list[GameInfo] = []
        self.selected_game: Optional[GameInfo] = None

        self.covers_cache = Path.home() / ".cache" / "dlss-enabler-linux" / "covers"
        self.covers_cache.mkdir(parents=True, exist_ok=True)

        self.active_workers: list[QThread] = []

        self.init_ui()
        self.refresh_core_status()
        self.start_scan_games()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Top Header Bar
        top_header = self._create_top_header()
        main_layout.addWidget(top_header)

        # Download / Progress Banner (hidden by default)
        self.progress_banner = self._create_progress_banner()
        main_layout.addWidget(self.progress_banner)

        # 2. Main Content Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(2)
        splitter.setStyleSheet("QSplitter::handle { background-color: #1a2030; }")

        # Left Panel (Game list, search, filters)
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)

        # Right Panel (Game details & controls)
        self.right_panel = self._create_right_panel()
        splitter.addWidget(self.right_panel)

        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 6)

        main_layout.addWidget(splitter, stretch=1)

    # =========================================================================
    # HEADER WIDGET
    # =========================================================================
    def _create_top_header(self) -> QWidget:
        header = QFrame()
        header.setObjectName("TopHeader")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(16)

        # App Logo & Branding
        logo_layout = QVBoxLayout()
        logo_layout.setSpacing(1)

        title = QLabel("DLSS Enabler for Linux")
        title.setObjectName("AppTitle")
        subtitle = QLabel("Universal Upscaler & Frame Generation Injector for Proton / Wine")
        subtitle.setObjectName("AppSubtitle")

        logo_layout.addWidget(title)
        logo_layout.addWidget(subtitle)
        layout.addLayout(logo_layout)

        layout.addStretch()

        # Core Status Card
        self.core_status_card = QFrame()
        self.core_status_card.setObjectName("CoreVersionCard")
        core_layout = QHBoxLayout(self.core_status_card)
        core_layout.setContentsMargins(12, 6, 12, 6)
        core_layout.setSpacing(10)

        self.core_status_label = QLabel("Checking Core...")
        self.core_status_label.setObjectName("CoreVersionLabel")
        core_layout.addWidget(self.core_status_label)

        self.btn_update_core = QPushButton("Check / Update")
        self.btn_update_core.setObjectName("btn_update_core")
        self.btn_update_core.setProperty("class", "btn-secondary")
        self.btn_update_core.setFixedHeight(30)
        self.btn_update_core.clicked.connect(self.start_download_core)
        core_layout.addWidget(self.btn_update_core)

        layout.addWidget(self.core_status_card)

        # Add Custom Game Button
        btn_add_custom = QPushButton("+ Add Game")
        btn_add_custom.setProperty("class", "btn-secondary")
        btn_add_custom.setFixedHeight(34)
        btn_add_custom.clicked.connect(self.on_add_custom_game)
        layout.addWidget(btn_add_custom)

        # Rescan Games Button
        btn_rescan = QPushButton("↻ Refresh")
        btn_rescan.setProperty("class", "btn-secondary")
        btn_rescan.setFixedHeight(34)
        btn_rescan.clicked.connect(self.start_scan_games)
        layout.addWidget(btn_rescan)

        return header

    def _create_progress_banner(self) -> QWidget:
        banner = QFrame()
        banner.setStyleSheet("background-color: #121829; border-bottom: 1px solid #1f2740; padding: 6px 20px;")
        layout = QHBoxLayout(banner)
        layout.setContentsMargins(16, 6, 16, 6)
        layout.setSpacing(14)

        self.progress_label = QLabel("Downloading DLSS Enabler binaries...")
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
    # LEFT PANEL (GAME BROWSER)
    # =========================================================================
    def _create_left_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background-color: #0f121d; padding: 10px;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Search Box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search installed games...")
        self.search_input.textChanged.connect(self.apply_filters)
        layout.addWidget(self.search_input)

        # Launcher Filters
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(6)

        self.launcher_filter_group = QButtonGroup(self)
        self.btn_filter_all = QPushButton("All")
        self.btn_filter_steam = QPushButton("Steam")
        self.btn_filter_heroic = QPushButton("Heroic")
        self.btn_filter_lutris = QPushButton("Lutris")
        self.btn_filter_custom = QPushButton("Custom")

        for i, btn in enumerate([self.btn_filter_all, self.btn_filter_steam, self.btn_filter_heroic, self.btn_filter_lutris, self.btn_filter_custom]):
            btn.setProperty("class", "filter-chip")
            btn.setCheckable(True)
            self.launcher_filter_group.addButton(btn, i)
            filter_layout.addWidget(btn)
            btn.clicked.connect(self.apply_filters)

        self.btn_filter_all.setChecked(True)
        layout.addLayout(filter_layout)

        # Status Filter Row
        status_row = QHBoxLayout()
        status_row.setSpacing(6)

        self.status_filter_group = QButtonGroup(self)
        self.btn_status_all = QPushButton("All Status")
        self.btn_status_patched = QPushButton("Patched Only")
        self.btn_status_unpatched = QPushButton("Unpatched Only")

        for i, btn in enumerate([self.btn_status_all, self.btn_status_patched, self.btn_status_unpatched]):
            btn.setProperty("class", "filter-chip")
            btn.setCheckable(True)
            self.status_filter_group.addButton(btn, i)
            status_row.addWidget(btn)
            btn.clicked.connect(self.apply_filters)

        self.btn_status_all.setChecked(True)
        layout.addLayout(status_row)

        # Game List View
        self.game_list_widget = QListWidget()
        self.game_list_widget.currentItemChanged.connect(self.on_game_selected)
        layout.addWidget(self.game_list_widget, stretch=1)

        # Footer count label
        self.footer_label = QLabel("Scanning games...")
        self.footer_label.setStyleSheet("color: #64748b; font-size: 11px; padding: 2px;")
        layout.addWidget(self.footer_label)

        return panel

    # =========================================================================
    # RIGHT PANEL (GAME DETAILS & ACTIONS)
    # =========================================================================
    def _create_right_panel(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #0d0f17; }")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Placeholder when no game is selected
        self.empty_state_widget = QWidget()
        empty_layout = QVBoxLayout(self.empty_state_widget)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setSpacing(12)

        icon_lbl = QLabel("🎮")
        icon_lbl.setStyleSheet("font-size: 48px;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(icon_lbl)

        empty_title = QLabel("Select a Game")
        empty_title.setStyleSheet("font-size: 18px; font-weight: 700; color: #cbd5e1;")
        empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_title)

        empty_desc = QLabel("Choose a game from the list to view compatibility, configure proxy hook methods, and install DLSS Enabler in one click.")
        empty_desc.setStyleSheet("color: #64748b; font-size: 13px; max-width: 400px;")
        empty_desc.setWordWrap(True)
        empty_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_desc)

        layout.addWidget(self.empty_state_widget)

        # Detail Container (visible when game selected)
        self.detail_container = QWidget()
        detail_layout = QVBoxLayout(self.detail_container)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(16)

        # Header Card (Cover Art + Title + Status)
        header_card = QFrame()
        header_card.setObjectName("GameDetailCard")
        header_card_layout = QHBoxLayout(header_card)
        header_card_layout.setContentsMargins(16, 16, 16, 16)
        header_card_layout.setSpacing(16)

        self.cover_label = QLabel()
        self.cover_label.setFixedSize(140, 75)
        self.cover_label.setStyleSheet("background-color: #1e2436; border-radius: 8px; border: 1px solid #28324a;")
        self.cover_label.setScaledContents(True)
        header_card_layout.addWidget(self.cover_label)

        title_info_layout = QVBoxLayout()
        title_info_layout.setSpacing(4)

        self.detail_title = QLabel("Game Title")
        self.detail_title.setObjectName("DetailTitle")
        title_info_layout.addWidget(self.detail_title)

        meta_row = QHBoxLayout()
        meta_row.setSpacing(8)

        self.detail_launcher = QLabel("Platform")
        self.detail_launcher.setObjectName("DetailLauncher")
        meta_row.addWidget(self.detail_launcher)

        self.detail_status_badge = QLabel("Not Patched")
        self.detail_status_badge.setProperty("class", "badge-unpatched")
        meta_row.addWidget(self.detail_status_badge)
        meta_row.addStretch()

        title_info_layout.addLayout(meta_row)
        header_card_layout.addLayout(title_info_layout, stretch=1)
        detail_layout.addWidget(header_card)

        # Executable & Paths Card
        paths_card = QFrame()
        paths_card.setObjectName("GameDetailCard")
        paths_layout = QVBoxLayout(paths_card)
        paths_layout.setSpacing(10)

        path_title = QLabel("TARGET EXECUTABLE & DIRECTORY")
        path_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #818cf8; letter-spacing: 0.5px;")
        paths_layout.addWidget(path_title)

        exe_row = QHBoxLayout()
        self.exe_path_input = QLineEdit()
        self.exe_path_input.setReadOnly(True)
        self.exe_path_input.setStyleSheet("background-color: #0b0d14; font-family: monospace; font-size: 11px;")
        exe_row.addWidget(self.exe_path_input, stretch=1)

        btn_browse_exe = QPushButton("Browse...")
        btn_browse_exe.setProperty("class", "btn-secondary")
        btn_browse_exe.clicked.connect(self.on_change_executable)
        exe_row.addWidget(btn_browse_exe)
        paths_layout.addLayout(exe_row)

        detail_layout.addWidget(paths_card)

        # Quirk / Tips Card (conditional)
        self.quirk_card = QFrame()
        self.quirk_card.setObjectName("QuirkBox")
        quirk_layout = QVBoxLayout(self.quirk_card)
        quirk_layout.setContentsMargins(12, 10, 12, 10)
        self.quirk_label = QLabel()
        self.quirk_label.setWordWrap(True)
        quirk_layout.addWidget(self.quirk_label)
        detail_layout.addWidget(self.quirk_card)

        # Configuration & Injection Method Card
        config_card = QFrame()
        config_card.setObjectName("GameDetailCard")
        config_layout = QVBoxLayout(config_card)
        config_layout.setSpacing(14)

        config_title = QLabel("DLSS ENABLER INJECTION METHOD")
        config_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #818cf8; letter-spacing: 0.5px;")
        config_layout.addWidget(config_title)

        method_row = QHBoxLayout()
        method_lbl = QLabel("Hook Proxy DLL:")
        method_lbl.setStyleSheet("font-weight: 600; color: #cbd5e1;")
        method_row.addWidget(method_lbl)

        self.method_combo = QComboBox()
        for key, desc in SUPPORTED_HOOK_METHODS:
            self.method_combo.addItem(desc, key)
        self.method_combo.currentIndexChanged.connect(self.update_launch_options_box)
        method_row.addWidget(self.method_combo, stretch=1)
        config_layout.addLayout(method_row)

        # Proton Launch Options Box
        launch_opts_title = QLabel("RECOMMENDED PROTON LAUNCH OPTIONS")
        launch_opts_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #818cf8; letter-spacing: 0.5px; margin-top: 6px;")
        config_layout.addWidget(launch_opts_title)

        launch_row = QHBoxLayout()
        self.launch_options_box = QLineEdit()
        self.launch_options_box.setObjectName("LaunchOptionBox")
        self.launch_options_box.setReadOnly(True)
        launch_row.addWidget(self.launch_options_box, stretch=1)

        self.btn_copy_launch = QPushButton("📋 Copy")
        self.btn_copy_launch.setProperty("class", "btn-secondary")
        self.btn_copy_launch.clicked.connect(self.copy_launch_options)
        launch_row.addWidget(self.btn_copy_launch)
        config_layout.addLayout(launch_row)

        # Toast label for copy feedback
        self.copy_toast = QLabel("")
        self.copy_toast.setStyleSheet("color: #10b981; font-weight: 600; font-size: 11px;")
        config_layout.addWidget(self.copy_toast)

        detail_layout.addWidget(config_card)

        # Primary Actions Row
        actions_card = QFrame()
        actions_card.setObjectName("GameDetailCard")
        actions_layout = QHBoxLayout(actions_card)
        actions_layout.setSpacing(12)

        self.btn_install_patch = QPushButton("⚡ Install DLSS Enabler")
        self.btn_install_patch.setProperty("class", "btn-primary")
        self.btn_install_patch.setFixedHeight(44)
        self.btn_install_patch.clicked.connect(self.on_install_patch)
        actions_layout.addWidget(self.btn_install_patch, stretch=2)

        self.btn_uninstall_patch = QPushButton("↺ Uninstall / Restore")
        self.btn_uninstall_patch.setProperty("class", "btn-danger")
        self.btn_uninstall_patch.setFixedHeight(44)
        self.btn_uninstall_patch.clicked.connect(self.on_uninstall_patch)
        actions_layout.addWidget(self.btn_uninstall_patch, stretch=1)

        self.btn_open_folder = QPushButton("📁 Open Folder")
        self.btn_open_folder.setProperty("class", "btn-secondary")
        self.btn_open_folder.setFixedHeight(44)
        self.btn_open_folder.clicked.connect(self.on_open_folder)
        actions_layout.addWidget(self.btn_open_folder, stretch=1)

        detail_layout.addWidget(actions_card)

        # Summary / Installed Files Info
        self.files_card = QFrame()
        self.files_card.setObjectName("GameDetailCard")
        files_card_layout = QVBoxLayout(self.files_card)
        files_card_layout.setSpacing(8)

        files_title = QLabel("INSTALLED COMPONENTS")
        files_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #818cf8; letter-spacing: 0.5px;")
        files_card_layout.addWidget(files_title)

        self.installed_files_label = QLabel("No active DLSS Enabler files installed.")
        self.installed_files_label.setStyleSheet("color: #94a3b8; font-size: 12px; font-family: monospace;")
        self.installed_files_label.setWordWrap(True)
        files_card_layout.addWidget(self.installed_files_label)

        detail_layout.addWidget(self.files_card)

        layout.addWidget(self.detail_container)
        self.detail_container.hide()

        scroll.setWidget(container)
        return scroll

    # =========================================================================
    # CORE ENGINE STATUS & UPDATES
    # =========================================================================
    def refresh_core_status(self):
        cached = self.downloader.get_cached_version()
        if cached:
            ver = cached.get("tag", "v0.9.4")
            self.core_status_label.setText(f"● DLSS Enabler {ver} (Ready)")
            self.core_status_label.setStyleSheet("color: #10b981; font-weight: 700;")
            self.btn_update_core.setText("Check Updates")
        else:
            self.core_status_label.setText("○ Not Downloaded")
            self.core_status_label.setStyleSheet("color: #f59e0b; font-weight: 700;")
            self.btn_update_core.setText("Download Now")

    def start_download_core(self):
        self.progress_banner.show()
        self.progress_bar.setValue(0)
        self.progress_label.setText("Connecting to GitHub...")
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
            QMessageBox.information(self, "DLSS Enabler Ready", msg)
        else:
            QMessageBox.warning(self, "Download Failed", f"Could not download binaries:\n{msg}")

    # =========================================================================
    # SCANNING & LIST MANAGEMENT
    # =========================================================================
    def start_scan_games(self):
        self.footer_label.setText("Scanning games across Steam, Heroic, Lutris, Bottles...")
        worker = ScannerWorker(self.scanner)
        worker.finished.connect(self.on_scan_finished)
        self.active_workers.append(worker)
        worker.start()

    def on_scan_finished(self, games: list[GameInfo]):
        self.all_games = games
        self.apply_filters()
        self.footer_label.setText(f"Found {len(games)} games across installed launchers.")

    def apply_filters(self):
        query = self.search_input.text().strip().lower()
        launcher_btn_id = self.launcher_filter_group.checkedId()
        status_btn_id = self.status_filter_group.checkedId()

        filtered: list[GameInfo] = []
        for g in self.all_games:
            # Search filter
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
        self.populate_game_list()

    def populate_game_list(self):
        self.game_list_widget.clear()
        for game in self.filtered_games:
            item = QListWidgetItem()
            item.setSizeHint(QSize(260, 68))
            widget = GameListItemWidget(game)
            self.game_list_widget.addItem(item)
            self.game_list_widget.setItemWidget(item, widget)

        if not self.filtered_games:
            self.show_empty_state()

    # =========================================================================
    # GAME SELECTION & DETAILS
    # =========================================================================
    def on_game_selected(self, current: Optional[QListWidgetItem], previous: Optional[QListWidgetItem]):
        if not current:
            self.show_empty_state()
            return

        row = self.game_list_widget.row(current)
        if 0 <= row < len(self.filtered_games):
            self.selected_game = self.filtered_games[row]
            self.display_game_details(self.selected_game)

    def show_empty_state(self):
        self.selected_game = None
        self.empty_state_widget.show()
        self.detail_container.hide()

    def display_game_details(self, game: GameInfo):
        self.empty_state_widget.hide()
        self.detail_container.show()

        # Title & Meta
        self.detail_title.setText(game.title)
        self.detail_launcher.setText(f"Platform: {game.launcher}")

        # Status badge
        if game.is_patched:
            self.detail_status_badge.setText(f"✓ Patched ({game.patch_method}.dll)")
            self.detail_status_badge.setProperty("class", "badge-patched")
            self.btn_install_patch.setText("⚡ Reinstall / Update DLSS Enabler")
            self.btn_uninstall_patch.setEnabled(True)
            self.btn_uninstall_patch.show()
        else:
            self.detail_status_badge.setText("Not Patched")
            self.detail_status_badge.setProperty("class", "badge-unpatched")
            self.btn_install_patch.setText("⚡ Install DLSS Enabler")
            self.btn_uninstall_patch.setEnabled(False)
            self.btn_uninstall_patch.hide()

        # Refresh style
        self.detail_status_badge.style().unpolish(self.detail_status_badge)
        self.detail_status_badge.style().polish(self.detail_status_badge)

        # Executable input
        self.exe_path_input.setText(game.executable_path or game.install_path)

        # Cover Art
        self.cover_label.clear()
        if game.cover_url:
            cached_cover = self.covers_cache / f"{game.id}.jpg"
            if cached_cover.exists():
                pix = QPixmap(str(cached_cover))
                self.cover_label.setPixmap(pix)
            else:
                self.cover_label.setText("Loading...")
                worker = ImageLoaderWorker(game.id, game.cover_url, self.covers_cache)
                worker.image_loaded.connect(self.on_cover_loaded)
                self.active_workers.append(worker)
                worker.start()
        else:
            self.cover_label.setText("No Art")

        # Quirk Box
        quirk = get_game_quirk(game.id, game.title)
        notes = quirk.get("notes") if quirk else game.quirk_notes
        if notes:
            self.quirk_label.setText(f"💡 Recommendation & Tips:\n{notes}")
            self.quirk_card.show()
        else:
            self.quirk_card.hide()

        # Method combo selection
        rec_method = (quirk.get("recommended_method") if quirk else None) or game.recommended_method or "version"
        idx = self.method_combo.findData(rec_method)
        if idx >= 0:
            self.method_combo.setCurrentIndex(idx)
        else:
            self.method_combo.setCurrentIndex(0)

        self.update_launch_options_box()
        self.update_installed_files_view()

    def on_cover_loaded(self, game_id: str, pix: QPixmap):
        if self.selected_game and self.selected_game.id == game_id:
            self.cover_label.setPixmap(pix)

    def update_launch_options_box(self):
        method = self.method_combo.currentData() or "version"
        cmd = self.patcher.generate_launch_options(method)
        self.launch_options_box.setText(cmd)
        self.copy_toast.setText("")

    def copy_launch_options(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.launch_options_box.text())
        self.copy_toast.setText("✓ Copied launch options to clipboard!")

    def update_installed_files_view(self):
        if not self.selected_game or not self.selected_game.is_patched:
            self.installed_files_label.setText("No active DLSS Enabler files installed.")
            return

        target_dir = self.patcher.get_target_directory(self.selected_game)
        manifest_file = target_dir / ".dlss_enabler_manifest.json"
        if manifest_file.exists():
            try:
                import json
                with open(manifest_file, "r") as f:
                    data = json.load(f)
                    files = data.get("installed_files", [])
                    method = data.get("method", "version")
                    time_str = data.get("installed_at", "")
                    ver_str = data.get("version", "")
                    self.installed_files_label.setText(
                        f"Version: {ver_str}\n"
                        f"Installed at: {time_str}\n"
                        f"Hook: {method}.dll\n"
                        f"Active DLLs:\n" + "\n".join(f"  • {f}" for f in files)
                    )
                    return
            except Exception:
                pass

        self.installed_files_label.setText(f"Patched with {self.selected_game.patch_method}.dll")

    # =========================================================================
    # ACTIONS: INSTALL / UNINSTALL / DIRECTORY
    # =========================================================================
    def on_install_patch(self):
        if not self.selected_game:
            return

        method = self.method_combo.currentData() or "version"
        self.btn_install_patch.setEnabled(False)
        self.btn_install_patch.setText("Installing...")
        QApplication.processEvents()

        res: PatchResult = self.patcher.patch_game(self.selected_game, method=method)

        self.btn_install_patch.setEnabled(True)
        if res.success:
            self.display_game_details(self.selected_game)
            # Update list item badge
            row = self.game_list_widget.currentRow()
            item = self.game_list_widget.item(row)
            if item:
                widget = self.game_list_widget.itemWidget(item)
                if isinstance(widget, GameListItemWidget):
                    widget.update_status_badge()

            QMessageBox.information(
                self,
                "Installation Successful",
                f"DLSS Enabler has been installed successfully!\n\n"
                f"Hook Method: {res.method}.dll\n"
                f"Target: {res.target_dir}\n\n"
                f"Launch Options:\n{res.launch_options}\n\n"
                f"Be sure to set the launch options in your game properties."
            )
        else:
            QMessageBox.critical(self, "Installation Failed", f"Could not install DLSS Enabler:\n{res.message}")

    def on_uninstall_patch(self):
        if not self.selected_game:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Uninstall",
            f"Are you sure you want to remove DLSS Enabler from '{self.selected_game.title}'?\n"
            f"Original backup files will be restored automatically.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        success, msg = self.patcher.unpatch_game(self.selected_game)
        if success:
            self.display_game_details(self.selected_game)
            row = self.game_list_widget.currentRow()
            item = self.game_list_widget.item(row)
            if item:
                widget = self.game_list_widget.itemWidget(item)
                if isinstance(widget, GameListItemWidget):
                    widget.update_status_badge()
            QMessageBox.information(self, "Restored", msg)
        else:
            QMessageBox.warning(self, "Uninstall Notice", msg)

    def on_open_folder(self):
        if not self.selected_game:
            return
        target_dir = self.patcher.get_target_directory(self.selected_game)
        if target_dir.exists():
            subprocess.run(["xdg-open", str(target_dir)], check=False)

    def on_change_executable(self):
        if not self.selected_game:
            return
        start_dir = self.selected_game.install_path
        fpath, _ = QFileDialog.getOpenFileName(
            self,
            "Select Game Executable",
            start_dir,
            "Executables (*.exe);;All Files (*)"
        )
        if fpath:
            self.selected_game.executable_path = fpath
            self.exe_path_input.setText(fpath)
            self.scanner._check_patch_status(self.selected_game)
            self.display_game_details(self.selected_game)

    def on_add_custom_game(self):
        dpath = QFileDialog.getExistingDirectory(
            self,
            "Select Game Folder",
            str(Path.home())
        )
        if dpath:
            new_game = self.scanner.add_custom_game(Path(dpath))
            self.all_games.append(new_game)
            self.apply_filters()
            # Select new game
            for i in range(self.game_list_widget.count()):
                item = self.game_list_widget.item(i)
                w = self.game_list_widget.itemWidget(item)
                if isinstance(w, GameListItemWidget) and w.game.id == new_game.id:
                    self.game_list_widget.setCurrentRow(i)
                    break
