from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QScrollArea, QStackedWidget
)
from PySide6.QtCore import QTimer
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import numpy as np
from scipy.stats import genextreme

from analysis.evt_analysis import fit_gev
from analysis.peak_duration import peak_duration_analysis
from analysis.risk_score import calculate_operation_risk, operation_risk_level
from analysis.protection_tcc import tcc_curve, tcc_protection_margin
from ui.components.result_card import ResultCard
from utils.plot_config import set_korean_font

from db_repo import update_assessment_risk, get_last_two_assessments


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
        self.btn_compare = QPushButton("이전과 비교")

        nav_l.addWidget(self.btn_to_result)
        nav_l.addSpacing(10)
        nav_l.addWidget(self.btn_over)
        nav_l.addWidget(self.btn_chart)
        nav_l.addStretch(1)
        nav_l.addWidget(self.btn_compare)
        outer.addWidget(nav)

        self.pages = QStackedWidget()
        outer.addWidget(self.pages)

        self.btn_over.clicked.connect(lambda: self.pages.setCurrentIndex(0))
        self.btn_chart.clicked.connect(lambda: self.pages.setCurrentIndex(1))
        self.btn_compare.clicked.connect(self.refresh_compare)

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
        self.equip_title.setWordWrap(True)
        self.equip_title.setStyleSheet("font-weight:900; font-size:16px;")
        self.equip_desc = QLabel("")
        self.equip_desc.setWordWrap(True)
        self.equip_desc.setStyleSheet("color:#111827;")
        self.equip_card.add_widget(self.equip_title)
        self.equip_card.add_widget(self.equip_desc)
        over.addWidget(self.equip_card)

        self.risk_card = ResultCard("운전 위험도 평가 (Data-based, 참고 지표)")
        self.risk_head = QLabel("")
        self.risk_head.setStyleSheet("font-weight:900; font-size:16px;")

        self.break_notice = QLabel(
            "본 점수는 위험도 점수로,\n"
            "값이 높을수록 운전 리스크가 큼을 의미합니다.\n"
            "보호(TCC) 점수는 보호 부족 시에만 위험 가중으로 반영됩니다."
        )
        self.break_notice.setWordWrap(True)
        self.break_notice.setStyleSheet("color:#111827; font-size:13px;")

        self.risk_policy = QLabel(
            "※ 운전 위험도 평가는 설비 판정(Hard)과 독립적인 참고 지표입니다."
        )
        self.risk_policy.setWordWrap(True)
        self.risk_policy.setStyleSheet("color:#111827; font-size:13px;")

        self.risk_break = QLabel("")
        self.risk_break.setWordWrap(True)
        self.risk_break.setStyleSheet("color:#111827;")

        self.risk_card.add_widget(self.risk_head)
        self.risk_card.add_widget(self.break_notice)
        self.risk_card.add_widget(self.risk_policy)
        self.risk_card.add_widget(self.risk_break)
        over.addWidget(self.risk_card)

        self.text_card = ResultCard("해석 요약")
        self.text_label = QLabel("")
        self.text_label.setWordWrap(True)
        self.text_label.setStyleSheet("color:#111827;")
        self.text_card.add_widget(self.text_label)
        over.addWidget(self.text_card)

        self.compare_card = ResultCard("판정 이력 비교")
        self.compare_label = QLabel("이전 판정 데이터 없음")
        self.compare_label.setWordWrap(True)
        self.compare_label.setStyleSheet("color:#111827;")
        self.compare_card.add_widget(self.compare_label)
        over.addWidget(self.compare_card)

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

        self.input_data = {}
        self.results = {}
        self.load_series = None
        self.dt = 1.0

    def load_data(self, input_data, results):
        self.input_data = input_data or {}
        self.results = results or {}

        dt = float(self.results.get("dt", 1.0))
        self.dt = dt if dt > 0 else 1.0

        base = float(self.input_data.get("I_load", 0.0))
        if base <= 0:
            base = float(self.results.get("limit_current", 100.0))

        self.load_series = np.array(
            [base + np.random.randn() * base * 0.05 for _ in range(300)]
        ).flatten()

        QTimer.singleShot(0, self.run_analysis)

    @staticmethod
    def _safe_hist_bins(x):
        n = len(x)
        if n <= 20:
            return max(5, n // 2)
        if n <= 100:
            return 10
        return 20

    @staticmethod
    def _safe_pdf_xlim(x, pad_ratio=0.15):
        xmin = float(np.min(x))
        xmax = float(np.max(x))
        if xmin == xmax:
            xmin -= 1.0
            xmax += 1.0
        span = xmax - xmin
        pad = span * pad_ratio
        return xmin - pad, xmax + pad

    @staticmethod
    def _gev_pdf_safe(xgrid, c, loc, scale):
        sc = float(scale)
        if not np.isfinite(sc) or sc <= 1e-9:
            sc = 1e-6
        try:
            pdf = genextreme.pdf(xgrid, c, loc=loc, scale=sc)
            pdf = np.where(np.isfinite(pdf), pdf, 0.0)
            return pdf
        except Exception:
            return np.zeros_like(xgrid, dtype=float)

    def run_analysis(self):
        y = self.load_series
        dt = self.dt
        t = np.arange(len(y)) * dt

        DESIGN_LIMIT = self.results.get("limit_current")
        try:
            DESIGN_LIMIT = float(DESIGN_LIMIT)
        except Exception:
            DESIGN_LIMIT = float(np.mean(y))

        if float(np.min(y)) == float(np.max(y)):
            y = y + np.random.randn(len(y)) * 0.01

        LIMIT_TIME = 5.0

        hard_status = self.results.get("equipment_status", "")
        equip_final_line = self.results.get("equipment_final_line", "")
        self.equip_title.setText(equip_final_line)

        cable_hard = self.results.get("cable_hard", {})
        cable_op = self.results.get("cable_op", {})
        thermal = self.results.get("thermal", {})

        self.equip_desc.setText(
            "케이블 판정(설비 기준): " + str(cable_hard.get("status", "-")) + "\n"
            "열상승(단열식): " + str(thermal.get("status", "-"))
        )

        # EVT 표본(블록맥시마)
        block_size = max(int(round(10.0 / dt)), 5)
        n_blocks = len(y) // block_size

        if n_blocks >= 8:
            blocks = y[:n_blocks * block_size].reshape(n_blocks, block_size)
            series_evt = blocks.max(axis=1)
            evt_method = f"Block Maxima (block={block_size} samples, n={len(series_evt)})"
        else:
            series_evt = y.copy()
            evt_method = f"Raw series (fallback, n={len(series_evt)})"

        observed_exceed = float(np.mean(y > DESIGN_LIMIT))

        gev = fit_gev(series_evt, DESIGN_LIMIT)
        c = float(gev["shape"])
        loc = float(gev["loc"])
        scale = float(gev["scale"])
        evt_prob = float(gev.get("exceed_prob", 0.0))
        evt_prob = min(max(evt_prob, 0.0), 1.0)

        durations = peak_duration_analysis(y, DESIGN_LIMIT)
        durations = durations if isinstance(durations, np.ndarray) else np.array([])
        durations_sec = durations.astype(float) * dt if durations.size > 0 else np.array([])
        max_duration = float(durations_sec.max()) if durations_sec.size > 0 else 0.0

        breaker_ok = bool(self.results.get("breaker_ok", False))

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
        self.risk_head.setText(f"운전 위험도: {level}  |  위험도 점수 {int(risk['total'])}/100")

        prot_note = ""
        if risk["protection_score"] is None:
            prot_text = "N/A"
            prot_note = "보호 위험 점수: N/A (점수 제외)"
        else:
            prot_text = f"{risk['protection_score']:.1f}/20"
            if float(risk["protection_score"]) <= 0.01:
                prot_note = "보호 위험 점수: 0에 가까움(보호 부족에 따른 위험 가중 없음)"
            else:
                prot_note = "보호 위험 점수: 값이 클수록 보호 부족으로 인한 위험 가중이 큼"

        self.risk_break.setText(
            f"- EVT 위험 점수: {risk['evt_score']:.1f}/40\n"
            f"- 지속시간 위험 점수: {risk['time_score']:.1f}/40\n"
            f"- 보호 위험 점수(TCC): {prot_text}\n"
            f"  · {prot_note}\n"
            f"  · {risk.get('protection_note', '')}"
        )

        op_lines = []
        op_lines.append("케이블 운영 조건 평가(Optional)")
        if cable_op.get("status") in ("평가 불가", "계산 불가"):
            op_lines.append(f"- {cable_op.get('status')}: {cable_op.get('reason')}")
        else:
            op_lines.append(f"- 최근 평균온도 {cable_op.get('ambient'):.1f}℃")
            if cable_op.get("I_allow_total") is not None:
                op_lines.append(f"- 보정 후 허용전류: {cable_op.get('I_allow_total'):,.0f} A")
            op_lines.append("- 운전 여유 감소")

        bm_explain = (
            "※ Block Maxima는 각 블록의 최대값을 사용하므로, 초과확률이 보수적으로 나올 수 있습니다."
            if "Block Maxima" in evt_method else
            "※ Raw fallback은 표본 수 부족으로 Block Maxima를 적용하지 못한 경우입니다."
        )

        self.text_label.setText(
            f"EVT 초과확률: {evt_prob:.2%}\n"
            f"(전류 기준: 설계전류 {float(DESIGN_LIMIT):.0f} A 초과 확률, GEV 추정)\n\n"
            f"지속시간 판정:\n"
            f"- 설계 기준: {LIMIT_TIME:.1f} s\n"
            f"- 관측 최대 지속: {max_duration:.1f} s\n\n"
            f"관측 초과율(원시 시계열): {observed_exceed:.2%}\n"
            f"EVT 적용 방식: {evt_method}\n"
            f"{bm_explain}\n\n"
            + "\n".join(op_lines)
        )

        # 그래프
        self.figure.clear()

        ax1 = self.figure.add_subplot(311)
        ax1.plot(t, y)
        ax1.axhline(DESIGN_LIMIT, linestyle="--", label="설계 기준")
        ax1.set_title("부하 전류 시계열")
        ax1.set_xlabel("Time (s)")
        ax1.set_ylabel("Current (A)")
        ax1.legend()

        ax2 = self.figure.add_subplot(312)
        bins = self._safe_hist_bins(series_evt)
        ax2.hist(series_evt, bins=bins, density=True, alpha=0.6, label="Histogram (density)")

        x0, x1 = self._safe_pdf_xlim(series_evt, pad_ratio=0.20)
        xgrid = np.linspace(x0, x1, 400)
        pdf = self._gev_pdf_safe(xgrid, c, loc, scale)

        if np.any(pdf > 0):
            cap = float(np.quantile(pdf, 0.995))
            pdf_plot = np.minimum(pdf, cap) if cap > 0 else pdf
        else:
            pdf_plot = pdf

        ax2.plot(xgrid, pdf_plot, linewidth=2, label="GEV PDF (clipped)")
        ax2.axvline(DESIGN_LIMIT, linestyle="--", label="설계 기준")
        ax2.set_title(f"EVT (GEV) 분포 - {evt_method}")
        ax2.set_xlabel("Current (A)")
        ax2.set_ylabel("Density")
        ax2.text(0.02, 0.90, f"fit: c={c:.3f}, loc={loc:.1f}, scale={scale:.3f}", transform=ax2.transAxes, fontsize=9)
        ax2.text(0.02, 0.80, f"EVT P(I>Limit)={evt_prob:.2%}", transform=ax2.transAxes, fontsize=9)
        ax2.legend()

        ax3 = self.figure.add_subplot(313)
        ax3.set_xlabel("전류 (A)")
        ax3.set_ylabel("차단 시간 (s)")
        ax3.set_title("보호계전 TCC 참고 분석 (Icu 적합 가정)")
        ax3.text(
            0.02, 0.90,
            "※ 본 그래프는 참고용입니다.\n"
            "   보호 위험 점수는 보호 부족 시에만 위험 가중으로 반영됩니다.",
            transform=ax3.transAxes, fontsize=9
        )

        if tcc_available:
            Imax = max(float(np.max(y)), Isc_A, pickup * 2.0)
            I = np.logspace(np.log10(pickup * 1.05), np.log10(Imax * 2.0), 300)
            T = tcc_curve(I, pickup, TMS)
            ax3.loglog(I, T, label="차단기 TCC")

            if Isc_A > pickup:
                t_trip = float(tcc_curve(np.array([Isc_A]), pickup, TMS)[0])
                ax3.scatter([Isc_A], [t_trip], color="red", zorder=5, label="● 단락전류 Isc")
                ax3.text(0.02, 0.72, f"예상 차단시간(TCC): {t_trip:.2f} s", transform=ax3.transAxes, fontsize=9)
        else:
            ax3.text(0.02, 0.72, "TCC 파라미터 부족으로 그래프 평가 불가", transform=ax3.transAxes, fontsize=9)

        if breaker_ok is False:
            for line in ax3.get_lines():
                try:
                    line.set_color("gray")
                    line.set_alpha(0.35)
                except Exception:
                    pass
            ax3.text(0.02, 0.62, "Icu 부적합: 본 TCC 해석은 의미가 제한됩니다.", transform=ax3.transAxes, fontsize=9)

        ax3.legend()

        self.figure.tight_layout()
        self.figure.subplots_adjust(hspace=0.65)
        self.canvas.draw()

        self.update_db_risk(risk_total=float(risk["total"]))
        self.refresh_compare()

    def update_db_risk(self, risk_total: float):
        assessment_id = self.results.get("assessment_id")
        if assessment_id is None:
            return
        update_assessment_risk(
            assessment_id=assessment_id,
            risk_internal=risk_total,
            risk_external=None
        )

    def refresh_compare(self):
        asset_id = self.results.get("asset_id")
        if asset_id is None:
            self.compare_label.setText("이전 판정 데이터 없음")
            return

        rows = get_last_two_assessments(asset_id)
        if len(rows) != 2:
            self.compare_label.setText("이전 판정 데이터 없음")
            return

        curr = rows[0]
        prev = rows[1]

        _, curr_hard, curr_risk, _ = curr
        _, prev_hard, prev_risk, _ = prev

        delta = None
        try:
            if curr_risk is not None and prev_risk is not None:
                delta = float(curr_risk) - float(prev_risk)
        except Exception:
            delta = None

        if delta is None:
            arrow = "→"
            delta_txt = "-"
        else:
            arrow = "▲" if delta > 0 else ("▼" if delta < 0 else "→")
            delta_txt = f"{delta:+.1f}"

        txt = (
            "이전 판정 대비 변화\n"
            f"- 설비 판정: {prev_hard} → {curr_hard}\n"
            f"- 위험도 점수: {prev_risk if prev_risk is not None else '-'} → {curr_risk if curr_risk is not None else '-'} ({arrow} {delta_txt})"
        )
        self.compare_label.setText(txt)

    def go_result(self):
        self.parent().setCurrentWidget(self.parent().result_page)
