from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel

class ResultCard(QFrame):
    def __init__(self, title: str):
        super().__init__()

        self.setObjectName("resultCard")

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 16, 16, 16)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("cardTitle")

        layout.addWidget(self.title_label)

    def add_widget(self, widget):
        self.layout().addWidget(widget)
