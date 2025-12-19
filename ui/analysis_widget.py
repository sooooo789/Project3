import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from analysis.evt_analysis import fit_evt, return_level
from utils.plot_config import set_korean_font


class AnalysisWidget(QWidget):
    def __init__(self):
        super().__init__()
        set_korean_font()

        layout = QVBoxLayout()
        self.label = QLabel()
        layout.addWidget(self.label)

        self.figure = Figure(figsize=(5, 3))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        self.setLayout(layout)
        self.run_evt()

    def run_evt(self):
        data = np.random.normal(100, 15, 365)  # 공공데이터 대체
        shape, loc, scale = fit_evt(data)
        level_10y = return_level(shape, loc, scale, 10)

        self.label.setText(
            f"GEV 분포 피팅 결과\n"
            f"10년 재현 피크 부하: {level_10y:.1f}"
        )

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.hist(data, bins=30, density=True)
        ax.set_title("전력 피크 분포 (EVT)")
        self.canvas.draw()
