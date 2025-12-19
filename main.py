import sys
from PySide6.QtWidgets import QApplication, QStackedWidget

from ui.input_widget import InputWidget
from ui.cable_widget import CableWidget
from ui.result_widget import ResultWidget
from ui.detail_result_widget import DetailResultWidget

from utils.style import APP_STYLE


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLE)

    stack = QStackedWidget()

    input_page = InputWidget(stack)
    cable_page = CableWidget(stack)
    result_page = ResultWidget(stack)
    detail_page = DetailResultWidget(stack)

    stack.input_page = input_page
    stack.cable_page = cable_page
    stack.result_page = result_page
    stack.detail_page = detail_page

    stack.cable_data = {}

    stack.addWidget(input_page)
    stack.addWidget(cable_page)
    stack.addWidget(result_page)
    stack.addWidget(detail_page)

    stack.setCurrentWidget(input_page)
    stack.resize(1100, 800)
    stack.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
