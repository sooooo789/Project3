import sys
from PySide6.QtWidgets import QApplication, QStackedWidget

from ui.input_widget import InputWidget
from ui.result_widget import ResultWidget


class MainWindow(QStackedWidget):
    def __init__(self):
        super().__init__()

        self.input_page = InputWidget()
        self.result_page = ResultWidget()

        self.addWidget(self.input_page)
        self.addWidget(self.result_page)

        self.input_page.calculate_requested.connect(self.run_calculation)

    def run_calculation(self, inputs: dict):
        self.result_page.run(inputs)
        self.setCurrentWidget(self.result_page)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.setWindowTitle("전력 설비 분석 툴")
    window.resize(1200, 800)
    window.show()
    sys.exit(app.exec())
