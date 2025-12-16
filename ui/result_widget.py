# ui/result_widget.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

from calc.short_circuit import calc_short_circuit
from calc.thermal import calc_thermal


class ResultWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)

        self.sc_label = QLabel()
        self.sc_reason = QLabel()

        self.thermal_label = QLabel()
        self.thermal_reason = QLabel()

        self.layout.addWidget(self.sc_label)
        self.layout.addWidget(self.sc_reason)
        self.layout.addWidget(self.thermal_label)
        self.layout.addWidget(self.thermal_reason)

    def run(self, inputs: dict):
        isc, _, sc_reason = calc_short_circuit(
            inputs["capacity"],
            inputs["voltage"],
            inputs["impedance"],
        )

        thermal = calc_thermal(
            inputs["load_current"],
            inputs["allowable_current"],
        )

        self.sc_label.setText(f"단락전류: {isc:.2f} kA")
        self.sc_reason.setText(sc_reason)

        self.thermal_label.setText(
            f"열상승 상태: {thermal['status']} "
            f"(부하율 {thermal['load_ratio']:.2f})"
        )
        self.thermal_reason.setText(thermal["reason"])
