from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QScrollArea, QStackedWidget
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import numpy as np
from scipy.stats import genextreme

from analysis.evt_analysis import fit_gev
from analysis.peak_duration import peak_duration_analysis
from analysis.risk_score import calculate_operation_risk, operation_risk_level
from analysis.protection_tcc import tcc_curve, tcc_protection_margin
from ui.components.result_card import ResultCard
from PySide6.QtCore import QTimer

from utils.plot_config import set_korean_font


class DetailResultWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        set_korean_font()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(10)

        nav = QWidget()
        nav_l = QHBoxLayout(nav)
        nav_l.setContentsMargins(0, 0, 0, 0)
        nav_l.setSpacing(10)

        self.btn_to_result = QPushButton("← 결과로")
        self.btn_to_result.clicked.connect(self.go_result)

        self.btn_over = QPushButton("요약")
        self.btn_chart = QPushButton("그래프")
        self.btn_over.clicked.connect(lambda: self.pages.setCurrentIndex(0))
        self.btn_chart.clicked.connect(lambda: self.pages.setCurrentIndex(1))

        nav_l.addWidget(self.btn_to_result)
        nav_l.addSpacing(10)
        nav_l.addWidget(self.btn_over)
        nav_l.addWidget(self.btn_chart)
        nav_l.addStretch(1)
        outer.addWidget(nav)

        self.pages = QStackedWidget()
        outer.addWidget(self.pages)

        # 요약(스크롤)
        self.over_scroll = QScrollArea()
        self.over_scroll.setWidgetResizable(True)
        self.pages.addWidget(self.over_scroll)

        over_body = QWidget()
        self.over_scroll.setWidget(over_body)
        over = QVBoxLayout(over_body)
        over.setContentsMargins(30, 20, 30, 30)
        over.setSpacing(12)

        self.equip_card = ResultCard("설비 판정 (Hard Engineering)")
        self.equip_title = QLabel("")
        self.equip_title.setStyleSheet("font-weight:900; font-size:16px;")
        self.equip_desc = QLabel("")
        self.equip_desc.setWordWrap(True)
        self.equip_desc.setStyleSheet("color:#374151;")
        self.equip_card.add_widget(self.equip_title)
        self.equip_card.add_widget(self.equip_desc)
        over.addWidget(self.equip_card)

        self.risk_card = ResultCard("운전 위험도 평가 (Data-based, 참고 지표)")
        self.risk_head = QLabel("")
        self.risk_head.setStyleSheet("font-weight:900; font-size:16px;")
        self.risk_note = QLabel("")
        self.risk_note.setWordWrap(True)
        self.risk_note.setStyleSheet("color:#374151;")
        self.risk_break = QLabel("")
        self.risk_break.setWordWrap(True)
        self.risk_break.setStyleSheet("color:#374151;")
        self.risk_card.add_widget(self.risk_head)
        self.risk_card.add_widget(self.risk_note)
        self.risk_card.add_widget(self.risk_break)
        over.addWidget(self.risk_card)

        self.text_card = ResultCard("해석 요약")
        self.text_label = QLabel("")
        self.text_label.setWordWrap(True)
        self.text_label.setStyleSheet("color:#374151;")
        self.text_card.add_widget(self.text_label)
        over.addWidget(self.text_card)

        over.addStretch(1)

        # 그래프(스크롤)
        self.chart_scroll = QScrollArea()
        self.chart_scroll.setWidgetResizable(True)
        self.pages.addWidget(self.chart_scroll)

        chart_body = QWidget()
        self.chart_scroll.setWidget(chart_body)
        chart = QVBoxLayout(chart_body)
        chart.setContentsMargins(30, 20, 30, 30)
        chart.setSpacing(12)

        self.figure = Figure(figsize=(8, 10))
        self.canvas = FigureCanvas(self.figure)
        chart.addWidget(self.canvas)
        chart.addStretch(1)

    def load_data(self, input_data, results):
        self.input_data = input_data
        self.results = results

        dt = float(results.get("dt", 1.0))
        self.dt = dt if dt > 0 else 1.0

        base = float(input_data["I_load"])
        self.load_series = np.array([base + np.random.randn() * base * 0.05 for _ in range(300)]).flatten()

        QTimer.singleShot(0, self.run_analysis)

    def run_analysis(self):
        y = self.load_series
        dt = self.dt
        t = np.arange(len(y)) * dt

        DESIGN_LIMIT = self.results.get("limit_current")
        if DESIGN_LIMIT is None or not np.isfinite(DESIGN_LIMIT):
            DESIGN_LIMIT = float(y.mean())

        if y.min() == y.max():
            y = y + np.random.randn(len(y)) * 0.01

        LIMIT_TIME = 5.0

        hard_status = self.results.get("equipment_status", "")
        self.equip_title.setText(self.results.get("equipment_final_line", ""))
        self.equip_desc.setText(self.results.get("equipment_final_sub", ""))

        if hard_status != "적합":
            self.risk_note.setText(
                "※ 설비 판정이 '적합'으로 확정되지 않았으므로,\n"
                "   운전 위험도 평가는 참고용으로만 제공합니다.\n"
                "   (보호(TCC) 점수는 N/A로 처리됩니다.)"
            )
        else:
            self.risk_note.setText(
                "※ 운전 위험도 평가는 설비 판정과 독립적인 참고 지표입니다.\n"
                "   설비 사용 가능 여부는 설비 판정 결과를 따릅니다."
            )

        # EVT(전류 기준)
        block_size = max(int(round(10.0 / dt)), 5)
        n_blocks = len(y) // block_size
        if n_blocks >= 3:
            blocks = y[:n_blocks * block_size].reshape(n_blocks, block_size)
            series_evt = blocks.max(axis=1)
            evt_method = f"Block Maxima (block={block_size} samples)"
        else:
            series_evt = y
            evt_method = "Raw series (fallback)"

        gev = fit_gev(series_evt, DESIGN_LIMIT)
        evt_prob = float(gev.get("exceed_prob", 0.0))
        observed_exceed = float(np.mean(y > DESIGN_LIMIT))

        # 지속시간(시간 기준)
        durations = peak_duration_analysis(y, DESIGN_LIMIT)
        durations = durations if isinstance(durations, np.ndarray) else np.array([])
        durations_sec = durations.astype(float) * dt if durations.size > 0 else np.array([])
        max_duration = float(durations_sec.max()) if durations_sec.size > 0 else 0.0

        # TCC 점수 입력
        breaker_ok = (self.results.get("breaker_result") == "적합")

        pickup = self.results.get("breaker_pickup")
        TMS = self.results.get("breaker_tms")
        Isc_A = self.results.get("Isc_A")

        tcc_margin = None
        tcc_available = True

        try:
            pickup = float(pickup)
            TMS = float(TMS)
            Isc_A = float(Isc_A)
            if pickup <= 0 or TMS <= 0 or Isc_A <= 0:
                tcc_available = False
        except Exception:
            tcc_available = False

        if tcc_available:
            tcc_margin = tcc_protection_margin(Isc_A, max_duration, pickup, TMS)
        else:
            tcc_margin = None

        risk = calculate_operation_risk(
            evt_prob=evt_prob,
            max_duration=max_duration,
            duration_limit=LIMIT_TIME,
            tcc_margin=tcc_margin,
            breaker_ok=breaker_ok,
            hard_status=hard_status
        )

        level = operation_risk_level(risk["total"])
        self.risk_head.setText(f"운전 위험도: {level}  |  점수 {int(risk['total'])}/100")

        prot_text = "N/A" if risk["protection_score"] is None else f"{risk['protection_score']:.1f}/20"
        self.risk_break.setText(
            f"- EVT 점수: {risk['evt_score']:.1f}/40\n"
            f"- 지속시간 점수: {risk['time_score']:.1f}/40\n"
            f"- 보호(TCC) 점수: {prot_text}\n"
            f"- 보호 점수 처리: {risk.get('protection_note', '')}\n"
            f"{risk.get('note', '')}"
        )

        mean_close = abs(float(np.mean(y)) - float(DESIGN_LIMIT)) / max(abs(float(np.mean(y))), 1.0) < 0.1
        conservative_note = (
            "※ 본 EVT 결과는 보수적(Block Maxima) 추정입니다.\n"
            "   설계 기준이 평균 부하와 근접할 경우 초과확률이 과대평가될 수 있습니다."
            if mean_close else
            "※ 본 EVT 결과는 보수적(Block Maxima) 추정 기반입니다."
        )

        self.text_label.setText(
            f"EVT 초과확률: {evt_prob:.2%}\n"
            f"(전류 기준: 설계전류 {float(DESIGN_LIMIT):.0f} A 초과 확률, GEV 추정)\n\n"
            f"지속시간 판정:\n"
            f"- 설계 기준: {LIMIT_TIME:.1f} s\n"
            f"- 관측 최대 지속: {max_duration:.1f} s\n\n"
            f"관측 초과율: {observed_exceed:.2%}\n"
            f"EVT 적용 방식: {evt_method}\n\n"
            f"{conservative_note}"
        )

        # -------- 그래프 --------
        self.figure.clear()

        ax1 = self.figure.add_subplot(311)
        ax1.plot(t, y)
        ax1.axhline(DESIGN_LIMIT, linestyle="--", label="설계 기준")
        ax1.set_title("부하 전류 시계열")
        ax1.set_xlabel("Time (s)")
        ax1.set_ylabel("Current (A)")
        ax1.legend()

        ax2 = self.figure.add_subplot(312)
        ax2.hist(series_evt, bins=20, density=True, alpha=0.6)
        x = np.linspace(series_evt.min(), series_evt.max(), 300)
        pdf = genextreme.pdf(x, gev["shape"], gev["loc"], gev["scale"])
        ax2.plot(x, pdf, linewidth=2, label="GEV PDF")
        ax2.axvline(DESIGN_LIMIT, linestyle="--", label="설계 기준")
        ax2.set_title(f"EVT (GEV) 분포 - {evt_method}")
        ax2.set_xlabel("Current (A)")
        ax2.legend()

        ax3 = self.figure.add_subplot(313)
        ax3.set_title("보호계전 TCC 분석" if breaker_ok else "보호계전 TCC 참고 분석 (Icu 적합 가정)")
        ax3.set_xlabel("전류 (A)")
        ax3.set_ylabel("차단 시간 (s)")

        if tcc_available:
            I = np.logspace(np.log10(pickup * 1.05), np.log10(max(Isc_A, pickup) * 2.0), 300)
            T = tcc_curve(I, pickup, TMS)
            ax3.loglog(I, T, label="차단기 TCC")

            if Isc_A > pickup:
                t_trip = float(tcc_curve(np.array([Isc_A]), pickup, TMS)[0])
                ax3.scatter([Isc_A], [t_trip], color="red", zorder=5, label="● 단락전류 Isc")
                ax3.text(0.02, 0.88, f"예상 차단시간: {t_trip:.2f} s", transform=ax3.transAxes)
        else:
            ax3.text(0.02, 0.88, "TCC 파라미터 부족으로 그래프 평가 불가", transform=ax3.transAxes)

        ax3.text(
            0.02, 0.05,
            "※ 본 TCC 해석은 차단기 Icu 적합을 전제로 한 참고 분석입니다.",
            transform=ax3.transAxes,
            fontsize=9
        )

        if breaker_ok is False:
            for line in ax3.get_lines():
                try:
                    line.set_color("gray")
                    line.set_alpha(0.4)
                except Exception:
                    pass

        ax3.legend()

        self.figure.tight_layout()
        self.figure.subplots_adjust(hspace=0.6)
        self.canvas.draw()

    def go_result(self):
        self.parent().setCurrentWidget(self.parent().result_page)
