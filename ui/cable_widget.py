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

        # 재질
        self.material = QComboBox()
        self.material.addItems(["Cu", "Al"])

        # 절연
        self.insulation = QComboBox()
        self.insulation.addItems(["XLPE", "PVC"])

        # 설치방법
        self.install = QComboBox()
        self.install.addItems(["트레이", "덕트", "매설"])

        # 주위온도
        self.ambient = QLineEdit()
        self.ambient.setPlaceholderText("예: 30")

        # 병렬 케이블 수
        self.parallel = QLineEdit()
        self.parallel.setPlaceholderText("예: 1")

        # 단면적(mm2)  <<<<<<<<<< 추가
        self.section = QLineEdit()
        self.section.setPlaceholderText("예: 95  (단위: mm²)")

        for label, w in [
            ("재질", self.material),
            ("절연", self.insulation),
            ("설치방법", self.install),
            ("주위온도(°C)", self.ambient),
            ("병렬 케이블 수", self.parallel),
            ("케이블 단면적(mm²)", self.section),
        ]:
            lb = QLabel(label)
            layout.addWidget(lb)
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

    def go_back(self):
        # 기본 입력으로 돌아가는 게 자연스러움
        self.parent.setCurrentWidget(self.parent.input_page)

    def save(self):
        # 숫자 필드 검증
        try:
            ambient = float(self.ambient.text().strip())
            parallel = int(float(self.parallel.text().strip()))
            section = float(self.section.text().strip())
        except Exception:
            QMessageBox.warning(self, "입력 오류", "주위온도/병렬/단면적은 숫자로 입력하세요.")
            return

        if parallel <= 0:
            parallel = 1
        if ambient <= -50 or ambient > 200:
            QMessageBox.warning(self, "입력 오류", "주위온도 범위를 확인하세요.")
            return
        if section <= 0:
            QMessageBox.warning(self, "입력 오류", "단면적(mm²)은 0보다 커야 합니다.")
            return

        data = {
            "cable_material": self.material.currentText(),
            "cable_insulation": self.insulation.currentText(),
            "cable_install": self.install.currentText(),
            "cable_ambient": ambient,
            "cable_parallel": parallel,
            "cable_section_mm2": section,  # << 저장 핵심
        }

        self.parent.cable_data = data
        self.status.setText(
            "저장 완료\n"
            f"- {data['cable_material']} / {data['cable_insulation']} / {data['cable_install']}\n"
            f"- {data['cable_ambient']:.0f}℃ / 병렬 {data['cable_parallel']} / {data['cable_section_mm2']:.0f}mm²"
        )
        QMessageBox.information(self, "저장", "케이블 조건 저장 완료")


    def go_home(self):
        self.parent.setCurrentWidget(self.parent.home_page)

    def go_basic(self):
        self.parent.setCurrentWidget(self.parent.input_page)
