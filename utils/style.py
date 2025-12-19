# style.py

APP_STYLE = """
QWidget {
    background-color: #f8fafc;
    color: #111827;
    font-family: 'Pretendard', 'Segoe UI', 'Malgun Gothic';
    font-size: 14px;
}

QLabel {
    font-size: 14px;
    color: #111827;
}

QLabel#title {
    font-size: 20px;
    font-weight: 900;
}

QLineEdit, QComboBox {
    background-color: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 10px;
    padding: 10px;
    color: #111827;
}

QLineEdit:focus, QComboBox:focus {
    border: 2px solid #06b6d4;
}

QPushButton {
    background-color: #06b6d4;
    color: #ffffff;
    border: none;
    border-radius: 12px;
    padding: 12px 14px;
    font-weight: 800;
}

QPushButton:hover {
    background-color: #0891b2;
}

QPushButton:pressed {
    background-color: #0e7490;
}

QScrollArea {
    border: none;
}

QScrollBar:vertical {
    border: none;
    background: #e5e7eb;
    width: 10px;
    margin: 2px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #94a3b8;
    min-height: 30px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background: #64748b;
}
"""
