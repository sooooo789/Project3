from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel


class ResultCard(QFrame):
    def __init__(self, title: str):
        super().__init__()

        # style.py와 연결되는 핵심
        self.setObjectName("Card")

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 14, 16, 14)
        self._layout.setSpacing(10)

        self._title = QLabel(title)
        self._title.setObjectName("CardTitle")
        self._layout.addWidget(self._title)

    def add_widget(self, w):
        # 본문 라벨들은 CardBody / Mono / Muted 등으로 외부에서 지정
        self._layout.addWidget(w)
