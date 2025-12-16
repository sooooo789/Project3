# ui/input_widget.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout,
    QPushButton, QLineEdit, QLabel
)
from PySide6.QtCore import Signal


class InputWidget(QWidget):
    calculate_requested = Signal(dict)

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        self.voltage = QLineEdit()
        self.capacity = QLineEdit()
        self.impedance = QLineEdit()

        self.load_current = QLineEdit()
        self.allowable_current = QLineEdit()

        layout.addWidget(QLabel("계통 전압 (kV)"))
        layout.addWidget(self.voltage)

        layout.addWidget(QLabel("변압기 용량 (kVA)"))
        layout.addWidget(self.capacity)

        layout.addWidget(QLabel("임피던스 (%)"))
        layout.addWidget(self.impedance)

        layout.addWidget(QLabel("부하 전류 (A)"))
        layout.addWidget(self.load_current)

        layout.addWidget(QLabel("허용 전류 (A)"))
        layout.addWidget(self.allowable_current)

        btn = QPushButton("계산 실행")
        btn.clicked.connect(self.on_calculate)
        layout.addWidget(btn)

    def on_calculate(self):
        inputs = {
            "voltage": float(self.voltage.text()),
            "capacity": float(self.capacity.text()),
            "impedance": float(self.impedance.text()),
            "load_current": float(self.load_current.text()),
            "allowable_current": float(self.allowable_current.text()),
        }
        self.calculate_requested.emit(inputs)
