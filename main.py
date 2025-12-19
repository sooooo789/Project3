import sys
from PySide6.QtWidgets import QApplication, QStackedWidget
from utils.style import APP_STYLE

from ui.home_widget import HomeWidget
from ui.input_widget import InputWidget
from ui.cable_widget import CableWidget
from ui.result_widget import ResultWidget
from ui.detail_result_widget import DetailResultWidget


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLE)
    stack = QStackedWidget()

    home_page = HomeWidget(stack)
    input_page = InputWidget(stack)
    cable_page = CableWidget(stack)
    result_page = ResultWidget(stack)
    detail_page = DetailResultWidget(stack)

    stack.home_page = home_page
    stack.input_page = input_page
    stack.cable_page = cable_page
    stack.result_page = result_page
    stack.detail_page = detail_page

    # 케이블 입력 저장소(아무것도 없으면 None)
    stack.cable_data = None

    stack.addWidget(home_page)
    stack.addWidget(input_page)
    stack.addWidget(cable_page)
    stack.addWidget(result_page)
    stack.addWidget(detail_page)

    stack.setCurrentWidget(home_page)
    stack.resize(1100, 820)
    stack.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
