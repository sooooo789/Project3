from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel


class ResultCard(QFrame):
    def __init__(self, title: str):
        super().__init__()
        self.setObjectName("ResultCard")

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 14, 16, 14)
        self._layout.setSpacing(10)

        self._title = QLabel(title)
        self._title.setObjectName("CardTitle")
        self._layout.addWidget(self._title)

        self.setStyleSheet("""
        #ResultCard {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 14px;
        }
        #CardTitle {
            font-size: 14px;
            font-weight: 800;
            color: #111827;
        }
        """)

    def add_widget(self, w):
        self._layout.addWidget(w)
