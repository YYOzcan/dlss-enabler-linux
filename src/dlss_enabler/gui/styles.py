"""Modern Dark / Cyberpunk theme stylesheet for DLSS Enabler Linux GUI."""

DARK_THEME_QSS = """
/* Global Window Style */
QWidget {
    background-color: #0d0f17;
    color: #e2e8f0;
    font-family: 'Segoe UI', 'Inter', 'Ubuntu', 'Noto Sans', sans-serif;
    font-size: 13px;
    selection-background-color: #6366f1;
    selection-color: #ffffff;
}

/* Main Window */
QMainWindow {
    background-color: #0d0f17;
}

/* Header & Top Bar */
#TopHeader {
    background-color: #131722;
    border-bottom: 1px solid #1f2638;
    padding: 12px 20px;
}

#AppTitle {
    font-size: 18px;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: 0.5px;
}

#AppSubtitle {
    font-size: 12px;
    color: #818cf8;
    font-weight: 500;
}

/* Core Version Card */
#CoreVersionCard {
    background-color: #1a2030;
    border: 1px solid #2d3748;
    border-radius: 8px;
    padding: 6px 14px;
}

#CoreVersionLabel {
    font-size: 12px;
    font-weight: 600;
    color: #10b981;
}

/* Search Bar */
QLineEdit {
    background-color: #161b2a;
    border: 1px solid #262f44;
    border-radius: 8px;
    padding: 8px 14px;
    color: #f1f5f9;
    font-size: 13px;
}

QLineEdit:focus {
    border: 1px solid #6366f1;
    background-color: #1a2135;
}

/* Filter Chips / Buttons */
QPushButton.filter-chip {
    background-color: #161b2a;
    border: 1px solid #262f44;
    border-radius: 16px;
    padding: 6px 14px;
    color: #94a3b8;
    font-weight: 600;
    font-size: 12px;
}

QPushButton.filter-chip:hover {
    background-color: #20273c;
    color: #ffffff;
    border-color: #3b4668;
}

QPushButton.filter-chip:checked {
    background-color: #4f46e5;
    border: 1px solid #6366f1;
    color: #ffffff;
}

/* Primary Action Buttons */
QPushButton.btn-primary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #7c3aed);
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 700;
    font-size: 13px;
}

QPushButton.btn-primary:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4338ca, stop:1 #6d28d9);
}

QPushButton.btn-primary:pressed {
    background: #3730a3;
}

QPushButton.btn-primary:disabled {
    background: #272d42;
    color: #64748b;
}

/* Success Button */
QPushButton.btn-success {
    background-color: #059669;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton.btn-success:hover {
    background-color: #047857;
}

/* Danger / Uninstall Button */
QPushButton.btn-danger {
    background-color: #26171f;
    color: #f87171;
    border: 1px solid #7f1d1d;
    border-radius: 8px;
    padding: 9px 18px;
    font-weight: 600;
    font-size: 13px;
}

QPushButton.btn-danger:hover {
    background-color: #dc2626;
    color: #ffffff;
    border-color: #dc2626;
}

/* Secondary Button */
QPushButton.btn-secondary {
    background-color: #1e2436;
    color: #e2e8f0;
    border: 1px solid #2e3852;
    border-radius: 8px;
    padding: 9px 16px;
    font-weight: 600;
}

QPushButton.btn-secondary:hover {
    background-color: #273048;
    border-color: #435074;
}

/* Game List / Scroll Area */
QListWidget {
    background-color: #10131d;
    border: 1px solid #1c2234;
    border-radius: 10px;
    outline: none;
    padding: 6px;
}

QListWidget::item {
    background-color: #151a27;
    border: 1px solid #1f273b;
    border-radius: 8px;
    margin-bottom: 6px;
    padding: 10px;
    color: #f8fafc;
}

QListWidget::item:hover {
    background-color: #1b2234;
    border-color: #313c59;
}

QListWidget::item:selected {
    background-color: #222a42;
    border: 1px solid #6366f1;
    color: #ffffff;
}

/* Game Details Panel */
#GameDetailCard {
    background-color: #131722;
    border: 1px solid #1f2638;
    border-radius: 12px;
    padding: 20px;
}

#DetailTitle {
    font-size: 20px;
    font-weight: 800;
    color: #ffffff;
}

#DetailLauncher {
    font-size: 12px;
    color: #94a3b8;
    font-weight: 500;
}

/* Status Badges */
QLabel.badge-patched {
    background-color: #064e3b;
    color: #34d399;
    border: 1px solid #059669;
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 11px;
    font-weight: 700;
}

QLabel.badge-unpatched {
    background-color: #1e2436;
    color: #94a3b8;
    border: 1px solid #2f3850;
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 11px;
    font-weight: 600;
}

/* Info Box / Quirk Box */
#QuirkBox {
    background-color: #1a1e2e;
    border-left: 4px solid #f59e0b;
    border-radius: 6px;
    padding: 10px 14px;
    color: #fde68a;
    font-size: 12px;
}

#LaunchOptionBox {
    background-color: #0a0c13;
    border: 1px solid #1f273d;
    border-radius: 8px;
    padding: 10px;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 12px;
    color: #38bdf8;
}

/* Combo Box */
QComboBox {
    background-color: #161b2a;
    border: 1px solid #273048;
    border-radius: 8px;
    padding: 8px 12px;
    color: #f1f5f9;
    font-weight: 600;
}

QComboBox:hover {
    border-color: #6366f1;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #161b2a;
    border: 1px solid #273048;
    selection-background-color: #4f46e5;
    color: #f8fafc;
    padding: 4px;
    border-radius: 6px;
}

/* Progress Bar */
QProgressBar {
    background-color: #161b2a;
    border: 1px solid #242c42;
    border-radius: 6px;
    text-align: center;
    color: #ffffff;
    font-weight: 700;
    font-size: 11px;
    height: 16px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #06b6d4);
    border-radius: 5px;
}

/* Scrollbars */
QScrollBar:vertical {
    background: #0d0f17;
    width: 8px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #252d42;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #3b4668;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""
