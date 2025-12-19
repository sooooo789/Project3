from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QLineEdit,
    QPushButton, QMessageBox, QHBoxLayout
)


class CableWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 30)
        layout.setSpacing(12)

        title = QLabel("케이블 입력")
        title.setStyleSheet("font-weight:900; font-size:18px;")
        layout.addWidget(title)

        self.mode = QComboBox()
        self.mode.addItems(["자동선정(AUTO)", "수동입력(MANUAL)"])

        self.material = QComboBox()
        self.material.addItems(["Cu", "Al"])

        self.insulation = QComboBox()
        self.insulation.addItems(["XLPE", "PVC"])

        self.install = QComboBox()
        self.install.addItems(["트레이", "덕트", "매설"])

        self.ambient = QLineEdit()
        self.ambient.setPlaceholderText("예: 30")

        self.parallel = QLineEdit()
        self.parallel.setPlaceholderText("예: 1")

        self.section = QLineEdit()
        self.section.setPlaceholderText("수동입력일 때만 사용 (예: 95)")

        for label, w in [
            ("모드", self.mode),
            ("재질", self.material),
            ("절연", self.insulation),
            ("설치방법", self.install),
            ("주위온도(°C)", self.ambient),
            ("병렬 케이블 수", self.parallel),
            ("케이블 단면적 S(mm²)", self.section),
        ]:
            layout.addWidget(QLabel(label))
            layout.addWidget(w)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.btn_back = QPushButton("← 돌아가기")
        self.btn_back.setMinimumHeight(44)
        self.btn_back.clicked.connect(self.go_back)

        self.btn_save = QPushButton("저장")
        self.btn_save.setMinimumHeight(44)
        self.btn_save.clicked.connect(self.save)

        btn_row.addWidget(self.btn_back)
        btn_row.addWidget(self.btn_save)
        layout.addLayout(btn_row)

        self.status = QLabel("")
        self.status.setStyleSheet("color:#374151;")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        layout.addStretch(1)

        self.mode.currentIndexChanged.connect(self._apply_mode_ui)
        self._apply_mode_ui()

    def _apply_mode_ui(self):
        is_manual = "MANUAL" in self.mode.currentText()
        self.section.setEnabled(is_manual)

    def go_back(self):
        self.parent.setCurrentWidget(self.parent.input_page)

    def save(self):
        try:
            ambient = float(self.ambient.text().strip())
            parallel = int(float(self.parallel.text().strip()))
        except Exception:
            QMessageBox.warning(self, "입력 오류", "주위온도/병렬은 숫자로 입력하세요.")
            return

        if parallel <= 0:
            parallel = 1

        mode = "MANUAL" if "MANUAL" in self.mode.currentText() else "AUTO"

        section_mm2 = None
        if mode == "MANUAL":
            try:
                section_mm2 = float(self.section.text().strip())
            except Exception:
                QMessageBox.warning(self, "입력 오류", "수동입력 모드에서는 단면적(S)을 숫자로 입력하세요.")
                return
            if section_mm2 <= 0:
                QMessageBox.warning(self, "입력 오류", "단면적(S)은 0보다 커야 합니다.")
                return

        data = {
            "cable_mode": mode,
            "cable_material": self.material.currentText(),
            "cable_insulation": self.insulation.currentText(),
            "cable_install": self.install.currentText(),
            "cable_ambient": ambient,
            "cable_parallel": parallel,
            "cable_section_mm2_input": section_mm2,  # 수동입력일 때만 값 존재
        }

        self.parent.cable_data = data
        self.status.setText(
            "저장 완료\n"
            f"- 모드: {mode}\n"
            f"- {data['cable_material']} / {data['cable_insulation']} / {data['cable_install']}\n"
            f"- {data['cable_ambient']:.0f}℃ / 병렬 {data['cable_parallel']}\n"
            f"- S(입력): {('미사용(AUTO)' if section_mm2 is None else f'{section_mm2:.0f}mm²')}"
        )
        QMessageBox.information(self, "저장", "케이블 조건 저장 완료")
