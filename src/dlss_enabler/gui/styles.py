"""Refined Minimalist Dark Theme stylesheet for DLSS Enabler Linux GUI.
Designed for a clean, professional, distraction-free gaming dashboard.
"""

DARK_THEME_QSS = """
/* Global Window Style */
QWidget {
    color: #e2e8f0;
    font-family: 'Segoe UI', 'Inter', 'Ubuntu', -apple-system, sans-serif;
    font-size: 13px;
    selection-background-color: #6366f1;
    selection-color: #ffffff;
}

QMainWindow, QDialog {
    background-color: #0b0d13;
}

/* Top Header Bar */
#TopHeader {
    background-color: #10131d;
    border-bottom: 1px solid #1a1f2e;
    padding: 10px 24px;
}

#AppTitle {
    font-size: 17px;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: 0.4px;
}

#AppSubtitle {
    font-size: 11px;
    color: #818cf8;
    font-weight: 500;
}

/* Core Version Badge */
#CoreVersionCard {
    background-color: #141824;
    border: 1px solid #20263a;
    border-radius: 8px;
    padding: 5px 12px;
}

#CoreVersionLabel {
    font-size: 12px;
    font-weight: 600;
}

/* Subheader / Filter Bar */
#FilterBar {
    background-color: #0d1017;
    border-bottom: 1px solid #161a26;
    padding: 10px 24px;
}

/* Search Bar */
QLineEdit#SearchBar {
    background-color: #131722;
    border: 1px solid #202638;
    border-radius: 20px;
    padding: 7px 16px;
    color: #f1f5f9;
    font-size: 12px;
    min-width: 220px;
}

QLineEdit#SearchBar:focus {
    border: 1px solid #6366f1;
    background-color: #161b2a;
}

/* Filter Chips */
QPushButton.filter-chip {
    background-color: #131722;
    border: 1px solid #202638;
    border-radius: 16px;
    padding: 5px 14px;
    color: #94a3b8;
    font-weight: 600;
    font-size: 12px;
}

QPushButton.filter-chip:hover {
    background-color: #1a2030;
    color: #ffffff;
    border-color: #2e3752;
}

QPushButton.filter-chip:checked {
    background-color: #4f46e5;
    border: 1px solid #6366f1;
    color: #ffffff;
}

/* Grid Scroll Area */
QScrollArea#GridScrollArea {
    border: none;
    background-color: #0b0d13;
}

QWidget#GridContainer {
    background-color: #0b0d13;
}

/* Game Card Widget */
#GameCard {
    background-color: #121520;
    border: 1px solid #1c2234;
    border-radius: 12px;
}

#GameCard:hover {
    background-color: #161b2a;
    border: 1px solid #6366f1;
}

#GameCardCover {
    border-top-left-radius: 11px;
    border-top-right-radius: 11px;
    background-color: #1a1e2c;
}

#GameCardTitle {
    font-size: 13px;
    font-weight: 700;
    color: #f8fafc;
}

/* Modal Dialog */
QDialog#GameModal {
    background-color: #10131d;
    border: 1px solid #262e44;
    border-radius: 16px;
}

#ModalHeaderCard {
    background-color: #141824;
    border: 1px solid #20263a;
    border-radius: 12px;
    padding: 16px;
}

#ModalSectionCard {
    background-color: #131724;
    border: 1px solid #1f2538;
    border-radius: 10px;
    padding: 14px;
}

/* Buttons */
QPushButton.btn-primary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #7c3aed);
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 9px 18px;
    font-weight: 700;
    font-size: 13px;
}

QPushButton.btn-primary:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4338ca, stop:1 #6d28d9);
}

QPushButton.btn-primary:pressed {
    background: #3730a3;
}

QPushButton.btn-secondary {
    background-color: #161b28;
    color: #e2e8f0;
    border: 1px solid #242c40;
    border-radius: 8px;
    padding: 7px 14px;
    font-weight: 600;
    font-size: 12px;
}

QPushButton.btn-secondary:hover {
    background-color: #1f2638;
    border-color: #384564;
    color: #ffffff;
}

QPushButton.btn-danger {
    background-color: #26161c;
    color: #f87171;
    border: 1px solid #6b1b2f;
    border-radius: 8px;
    padding: 9px 16px;
    font-weight: 600;
    font-size: 12px;
}

QPushButton.btn-danger:hover {
    background-color: #dc2626;
    color: #ffffff;
    border-color: #dc2626;
}

/* Input & ComboBox */
QComboBox {
    background-color: #141824;
    border: 1px solid #242c40;
    border-radius: 8px;
    padding: 6px 12px;
    color: #f1f5f9;
    font-weight: 600;
}

QComboBox:hover {
    border-color: #6366f1;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox QAbstractItemView {
    background-color: #141824;
    border: 1px solid #242c40;
    selection-background-color: #4f46e5;
    color: #f8fafc;
    padding: 4px;
    border-radius: 6px;
}

QLineEdit {
    background-color: #0d1017;
    border: 1px solid #202638;
    border-radius: 6px;
    padding: 6px 10px;
    color: #f1f5f9;
    font-size: 12px;
}

QLineEdit:focus {
    border: 1px solid #6366f1;
}

/* Scrollbar */
QScrollBar:vertical {
    background: #0b0d13;
    width: 8px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #1e2436;
    border-radius: 4px;
    min-height: 24px;
}

QScrollBar::handle:vertical:hover {
    background: #313b56;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""
