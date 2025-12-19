from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout


class HomeWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        layout = QVBoxLayout(self)
        layout.setContentsMargins(70, 60, 70, 60)
        layout.setSpacing(16)

        title = QLabel("전력설비 분석 툴")
        title.setStyleSheet("font-weight:900; font-size:22px;")
        layout.addWidget(title)

        desc = QLabel(
            "첫 단계에서 입력 종류를 선택하세요.\n"
            "- 기본 입력: 전압/용량/임피던스/부하전류/차단기 등\n"
            "- 케이블 입력: 재질/절연/설치/온도/병렬 등 (케이블만 저장)"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color:#374151;")
        layout.addWidget(desc)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self.btn_basic = QPushButton("기본 입력")
        self.btn_basic.setMinimumHeight(56)
        self.btn_basic.clicked.connect(self.go_basic)

        self.btn_cable = QPushButton("케이블 입력")
        self.btn_cable.setMinimumHeight(56)
        self.btn_cable.clicked.connect(self.go_cable)

        btn_row.addWidget(self.btn_basic)
        btn_row.addWidget(self.btn_cable)

        layout.addLayout(btn_row)
        layout.addStretch(1)

    def go_basic(self):
        self.parent.setCurrentWidget(self.parent.input_page)

    def go_cable(self):
        self.parent.setCurrentWidget(self.parent.cable_page)
