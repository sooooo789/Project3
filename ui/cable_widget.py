# ui/cable_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QLineEdit,
    QPushButton, QMessageBox, QHBoxLayout, QScrollArea
)
from PySide6.QtCore import Qt


class CableWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent  # 보통 QStackedWidget

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(10)

        # 스크롤
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        outer.addWidget(self.scroll)

        body = QWidget()
        self.scroll.setWidget(body)

        layout = QVBoxLayout(body)
        layout.setContentsMargins(30, 25, 30, 30)
        layout.setSpacing(12)

        title = QLabel("케이블 입력")
        title.setStyleSheet("font-weight:900; font-size:18px;")
        layout.addWidget(title)

        self.mode = QComboBox()
        self.mode.addItems(["자동선정(AUTO)", "수동입력(MANUAL)"])

        # 프로파일은 저장만 해두고(향후 테이블 선택에 활용),
        # ResultWidget에서 그대로 넘겨서 engineering.py가 쓰게 만들기 위한 필드
        self.profile = QComboBox()
        self.profile.addItems(["IEC 보수(Conservative)", "IEC 현실(1C)"])

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
            ("테이블 프로파일", self.profile),
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
        # input_page 있으면 거기로, 없으면 닫기
        if hasattr(self.parent, "input_page"):
            self.parent.setCurrentWidget(self.parent.input_page)
        elif hasattr(self.parent, "home_page"):
            self.parent.setCurrentWidget(self.parent.home_page)
        else:
            self.close()

    def showEvent(self, event):
        super().showEvent(event)
        cd = getattr(self.parent, "cable_data", None)
        if isinstance(cd, dict) and cd:
            self.status.setText(
                "현재 저장된 케이블 조건 있음\n"
                f"- 모드: {cd.get('cable_mode')}\n"
                f"- 재질/절연/설치: {cd.get('cable_material')} / {cd.get('cable_insulation')} / {cd.get('cable_install')}\n"
                f"- 온도/병렬: {cd.get('cable_ambient')}℃ / {cd.get('cable_parallel')}\n"
                f"- S(수동): {cd.get('cable_section_mm2_input')}"
            )
        else:
            self.status.setText("저장된 케이블 조건 없음")

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
        profile = "IEC_REALISTIC_1C" if "현실" in self.profile.currentText() else "IEC_CONSERVATIVE"

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

        # ✅ 핵심: ResultWidget이 읽는 키와 100% 일치시키기(cable_ 접두사 고정)
        data = {
            "cable_mode": mode,
            "cable_table_profile": profile,
            "cable_material": self.material.currentText(),
            "cable_insulation": self.insulation.currentText(),
            "cable_install": self.install.currentText(),
            "cable_ambient": ambient,
            "cable_parallel": parallel,
            "cable_section_mm2_input": section_mm2,  # MANUAL일 때만 값
        }

        self.parent.cable_data = data

        self.status.setText(
            "저장 완료\n"
            f"- 모드: {mode} / 프로파일: {profile}\n"
            f"- {data['cable_material']} / {data['cable_insulation']} / {data['cable_install']}\n"
            f"- {data['cable_ambient']:.0f}℃ / 병렬 {data['cable_parallel']}\n"
            f"- S(수동): {('미사용(AUTO)' if section_mm2 is None else f'{section_mm2:.0f}mm²')}"
        )
        QMessageBox.information(self, "저장", "케이블 조건 저장 완료")
