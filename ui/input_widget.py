from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QMessageBox, QHBoxLayout,
    QScrollArea, QSizePolicy
)

from PySide6.QtCore import Qt

class InputWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(10)

        # 스크롤 영역
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        outer.addWidget(self.scroll)

        # 스크롤 안에 들어갈 실제 폼 컨테이너
        body = QWidget()
        self.scroll.setWidget(body)

        layout = QVBoxLayout(body)
        layout.setContentsMargins(30, 25, 30, 30)
        layout.setSpacing(12)

        title = QLabel("기본 입력")
        title.setStyleSheet("font-weight:900; font-size:18px;")
        layout.addWidget(title)

        note = QLabel(
            "※ 케이블 입력은 홈에서 별도로 저장할 수 있습니다.\n"
            "   케이블 조건이 저장되어 있으면 계산 시 자동 반영됩니다."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color:#374151;")
        layout.addWidget(note)

        self.voltage = QLineEdit()
        self.capacity = QLineEdit()
        self.impedance = QLineEdit()
        self.load_current = QLineEdit()
        self.breaker_rating = QLineEdit()

        self.standard = QComboBox()
        self.standard.addItems(["KESC", "IEC"])

        self.dt = QLineEdit()
        self.dt.setPlaceholderText("기본 1.0")

        self.t_clear = QLineEdit()
        self.t_clear.setPlaceholderText("선택 입력 (예: 0.2)")

        for label, widget in [
            ("전압(kV)", self.voltage),
            ("변압기 용량(kVA)", self.capacity),
            ("임피던스(%)", self.impedance),
            ("부하전류(A)", self.load_current),
            ("차단기 차단용량 Icu(kA)", self.breaker_rating),
            ("기준", self.standard),
            ("샘플 간격 dt(s)", self.dt),
            ("고장 제거시간 t_clear(s)", self.t_clear),
        ]:
            lb = QLabel(label)
            lb.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
            layout.addWidget(lb)
            layout.addWidget(widget)

        # 버튼들(스크롤 안에 같이 들어가도 되고, 밖에 고정해도 되는데
        # 일단 형님 화면처럼 아래에 보이게 하려면 스크롤 안에 둬도 충분히 안정적임)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.btn_home = QPushButton("← 홈으로")
        self.btn_home.setMinimumHeight(44)
        self.btn_home.clicked.connect(self.go_home)
        btn_row.addWidget(self.btn_home)

        self.btn_cable = QPushButton("케이블 입력 →")
        self.btn_cable.setMinimumHeight(44)
        self.btn_cable.clicked.connect(self.go_cable)
        btn_row.addWidget(self.btn_cable)

        self.btn_run = QPushButton("계산 실행 → 결과")
        self.btn_run.setMinimumHeight(44)
        self.btn_run.clicked.connect(self.calculate)
        btn_row.addWidget(self.btn_run)

        layout.addLayout(btn_row)

        self.cable_state = QLabel("")
        self.cable_state.setStyleSheet("color:#374151;")
        self.cable_state.setWordWrap(True)
        layout.addWidget(self.cable_state)

        layout.addStretch(1)

    def showEvent(self, event):
        super().showEvent(event)
        cd = getattr(self.parent, "cable_data", None)
        self.cable_state.setText(
            "케이블 조건 저장: 있음"
            if cd else
            "케이블 조건 저장: 없음 (케이블 판정은 판정 불가로 처리됨)"
        )

    def go_home(self):
        self.parent.setCurrentWidget(self.parent.home_page)

    def go_cable(self):
        self.parent.setCurrentWidget(self.parent.cable_page)

    def calculate(self):
        required = [self.voltage, self.capacity, self.impedance, self.load_current, self.breaker_rating]
        if any(not w.text().strip() for w in required):
            QMessageBox.warning(self, "입력 오류", "필수 입력값을 모두 채워주세요.")
            return

        try:
            data = {
                "V": float(self.voltage.text()),
                "S": float(self.capacity.text()),
                "Z": float(self.impedance.text()),
                "I_load": float(self.load_current.text()),
                "breaker": float(self.breaker_rating.text()),
                "standard": self.standard.currentText(),
            }

            dt_txt = self.dt.text().strip()
            data["dt"] = float(dt_txt) if dt_txt else 1.0
            if data["dt"] <= 0:
                data["dt"] = 1.0

            t_txt = self.t_clear.text().strip()
            data["t_clear"] = float(t_txt) if t_txt else None

        except ValueError:
            QMessageBox.warning(self, "입력 오류", "숫자 형식이 올바르지 않습니다.")
            return

        cd = getattr(self.parent, "cable_data", None)
        if cd:
            data.update(cd)

        self.parent.result_page.run_calculation(data)
        self.parent.setCurrentWidget(self.parent.result_page)
