# ui/detail_result_widget.py
import os
import json

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QScrollArea, QStackedWidget, QComboBox, QFrame
)
from PySide6.QtCore import QTimer, Qt

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

        # 카드 안 "제목/라벨" 회색줄(글자 뒤 배경) 제거 핵심:
        # APP_STYLE의 QWidget background-color가 QLabel에도 먹어서 카드(흰색) 위에 줄처럼 보임.
        # 여기서 QLabel 배경을 투명으로 강제해서 카드 배경(흰색)이 그대로 보이게 함.
        self.setStyleSheet("QLabel { background: transparent; }")

        # =========================
        # Helpers (회색 줄배경/하이라이트 제거)
        # =========================
        def _as_plain_block(label: QLabel, object_name: str, bigger: bool = False):
            label.setObjectName(object_name)
            label.setWordWrap(True)
            label.setTextFormat(Qt.PlainText)
            label.setAutoFillBackground(False)
            if bigger:
                label.setStyleSheet("background: transparent; font-size: 14px; line-height: 1.35;")
            else:
                label.setStyleSheet("background: transparent;")

        # =========================
        # Layout: Outer
        # =========================
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(10)

        # =========================
        # Navigation
        # =========================
        nav = QWidget()
        nav_l = QHBoxLayout(nav)
        nav_l.setContentsMargins(0, 0, 0, 0)
        nav_l.setSpacing(10)

        self.btn_to_result = QPushButton("← 결과로")
        self.btn_to_result.clicked.connect(self.go_result)

        self.btn_over = QPushButton("요약")
        self.btn_chart = QPushButton("그래프")
        self.btn_chart.setObjectName("PrimaryButton")

        self.btn_over.clicked.connect(lambda: self.pages.setCurrentIndex(0))
        self.btn_chart.clicked.connect(lambda: self.pages.setCurrentIndex(1))

        self.baseline_combo = QComboBox()
        self.baseline_combo.addItems([
            "기준선: I_design(설계)",
            "기준선: I_load(부하)",
            "기준선: I_allow(30℃ 허용)",
        ])
        self.baseline_combo.currentIndexChanged.connect(self.on_baseline_changed)

        nav_l.addWidget(self.btn_to_result)
        nav_l.addSpacing(10)
        nav_l.addWidget(self.btn_over)
        nav_l.addWidget(self.btn_chart)
        nav_l.addStretch(1)
        nav_l.addWidget(self.baseline_combo)
        outer.addWidget(nav)

        # =========================
        # Pages
        # =========================
        self.pages = QStackedWidget()
        outer.addWidget(self.pages)

        # =========================
        # Overview Page
        # =========================
        self.over_scroll = QScrollArea()
        self.over_scroll.setWidgetResizable(True)
        self.over_scroll.setFrameShape(QFrame.NoFrame)
        self.over_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.pages.addWidget(self.over_scroll)

        over_body = QWidget()
        self.over_scroll.setWidget(over_body)
        over = QVBoxLayout(over_body)
        over.setContentsMargins(30, 20, 30, 30)
        over.setSpacing(14)

        # ---- Hard Engineering Card
        self.equip_card = ResultCard("설비 판정 (Hard Engineering)")
        self.equip_title = QLabel("")
        self.equip_title.setObjectName("H1")
        self.equip_title.setTextFormat(Qt.PlainText)
        self.equip_title.setAutoFillBackground(False)
        self.equip_title.setStyleSheet("background: transparent;")

        self.equip_desc = QLabel("")
        _as_plain_block(self.equip_desc, "Muted")

        self.equip_card.add_widget(self.equip_title)
        self.equip_card.add_widget(self.equip_desc)
        over.addWidget(self.equip_card)

        # Divider
        div = QFrame()
        div.setObjectName("Divider")
        div.setFixedHeight(1)
        over.addWidget(div)

        # ---- Risk Card (텍스트 블록 방식)
        self.risk_card = ResultCard("운전 위험도 평가 (참고 지표)")
        self.risk_head = QLabel("")
        self.risk_head.setObjectName("H1")
        self.risk_head.setTextFormat(Qt.PlainText)
        self.risk_head.setAutoFillBackground(False)
        self.risk_head.setStyleSheet("background: transparent;")

        self.meta_line = QLabel("")
        _as_plain_block(self.meta_line, "Muted")

        self.break_notice = QLabel(
            "본 평가는 운전 리스크 참고 지표입니다.\n"
            "DEMO 데이터 사용 시 정량 점수 및 DB 반영은 비활성화됩니다."
        )
        _as_plain_block(self.break_notice, "Muted")

        self.risk_note = QLabel("")
        _as_plain_block(self.risk_note, "Muted")

        self.risk_break = QLabel("")
        _as_plain_block(self.risk_break, "Mono")

        self.risk_card.add_widget(self.risk_head)
        self.risk_card.add_widget(self.meta_line)
        self.risk_card.add_widget(self.break_notice)
        self.risk_card.add_widget(self.risk_note)
        self.risk_card.add_widget(self.risk_break)
        over.addWidget(self.risk_card)

        # ---- Text Summary
        self.text_card = ResultCard("해석 요약")
        self.text_label = QLabel("")
        _as_plain_block(self.text_label, "AnalysisText", bigger=True)
        self.text_card.add_widget(self.text_label)
        over.addWidget(self.text_card)

        # ---- Compare
        self.compare_card = ResultCard("판정 이력 비교")
        self.compare_label = QLabel("이전 판정 데이터 없음")
        _as_plain_block(self.compare_label, "Muted")
        self.compare_card.add_widget(self.compare_label)
        over.addWidget(self.compare_card)

        over.addStretch(1)

        # =========================
        # Chart Page
        # =========================
        self.chart_scroll = QScrollArea()
        self.chart_scroll.setWidgetResizable(True)
        self.chart_scroll.setFrameShape(QFrame.NoFrame)
        self.chart_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.pages.addWidget(self.chart_scroll)

        chart_body = QWidget()
        self.chart_scroll.setWidget(chart_body)
        chart = QVBoxLayout(chart_body)
        chart.setContentsMargins(30, 20, 30, 30)
        chart.setSpacing(12)

        self.figure = Figure(figsize=(8, 10))
        self.figure.patch.set_facecolor("white")
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background: #FFFFFF; border-radius: 14px;")
        chart.addWidget(self.canvas)
        chart.addStretch(1)

        # =========================
        # State
        # =========================
        self.input_data = None
        self.results = None
        self.dt = 1.0
        self.load_series = None
        self._baseline_key = "I_design"

    def _prev_path(self) -> str:
        base = os.path.dirname(os.path.dirname(__file__))
        return os.path.join(base, "data", "prev_judgement.json")

    def _load_prev(self):
        path = self._prev_path()
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def on_baseline_changed(self, idx: int):
        if idx == 0:
            self._baseline_key = "I_design"
        elif idx == 1:
            self._baseline_key = "I_load"
        else:
            self._baseline_key = "I_allow_hard"

        if self.results is not None and self.load_series is not None:
            self.run_analysis()

    def load_data(self, input_data, results):
        self.input_data = input_data or {}
        self.results = results or {}

        dt = float(self.results.get("dt", 1.0))
        self.dt = dt if dt > 0 else 1.0

        base = float(self.results.get("I_load", self.results.get("limit_current", 0.0)) or 0.0)
        if base <= 0:
            base = 100.0

        seed = int(self.results.get("demo_seed", 2025))
        rng = np.random.default_rng(seed)
        self.load_series = (base + rng.normal(0.0, base * 0.05, size=300)).astype(float)

        self.results["data_source_note"] = f"데모 시계열(시뮬레이션, seed={seed})"
        self.results["is_demo"] = True

        if self.results.get("I_design") is not None:
            self.baseline_combo.setCurrentIndex(0)
            self._baseline_key = "I_design"
        else:
            self.baseline_combo.setCurrentIndex(1)
            self._baseline_key = "I_load"

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

    def _get_baseline(self):
        def _f(key):
            try:
                v = self.results.get(key, None)
                return float(v) if v is not None else None
            except Exception:
                return None

        I_load = _f("I_load")
        I_design = _f("I_design")
        I_allow = _f("I_allow_hard")

        baseline = None
        label = ""

        if self._baseline_key == "I_allow_hard":
            baseline = I_allow
            label = "I_allow(30℃ 허용)"
        elif self._baseline_key == "I_load":
            baseline = I_load
            label = "I_load(부하)"
        else:
            baseline = I_design
            label = "I_design(설계)"

        if baseline is None:
            baseline = I_load
            label = "I_load(부하)"
            if baseline is None:
                baseline = float(np.mean(self.load_series))
                label = "평균(대체)"

        return baseline, label, I_load, I_design, I_allow

    @staticmethod
    def _bootstrap_evt_ci(series_evt, baseline, n_boot=200, seed=2025):
        rng = np.random.default_rng(int(seed))
        x = np.array(series_evt, dtype=float)
        if x.size < 8:
            return None, None, None

        probs = []
        for _ in range(int(n_boot)):
            sample = rng.choice(x, size=x.size, replace=True)
            try:
                gev = fit_gev(sample, baseline)
                p = float(gev.get("exceed_prob", np.nan))
                if np.isfinite(p):
                    probs.append(min(max(p, 0.0), 1.0))
            except Exception:
                continue

        if len(probs) < 20:
            return None, None, None

        probs = np.array(probs, dtype=float)
        return float(np.quantile(probs, 0.025)), float(np.quantile(probs, 0.975)), float(np.mean(probs))

    def run_analysis(self):
        if self.results is None or self.load_series is None:
            return

        y = self.load_series
        dt = self.dt
        t = np.arange(len(y)) * dt

        baseline, baseline_label, I_load, I_design, I_allow = self._get_baseline()

        LIMIT_TIME = 5.0

        hard_code = self.results.get("equipment_status", "")
        self.equip_title.setText(self.results.get("equipment_final_line", ""))
        self.equip_desc.setText(self.results.get("equipment_final_sub", ""))

        block_size = max(int(round(10.0 / dt)), 5)
        n_blocks = len(y) // block_size

        if n_blocks >= 8:
            blocks = y[:n_blocks * block_size].reshape(n_blocks, block_size)
            series_evt = blocks.max(axis=1)
            evt_method = f"Block Maxima (block={block_size} samples, n={len(series_evt)})"
            evt_def = "EVT(블록 최대값 기준) 초과확률  P(block max > 기준선)"
            evt_kind = "BLOCK_MAX"
        else:
            series_evt = y.copy()
            evt_method = f"Raw series (fallback, n={len(series_evt)})"
            evt_def = "EVT(원시 시계열 기준) 초과확률  P(sample > 기준선)"
            evt_kind = "RAW"

        observed_exceed_sample = float(np.mean(y > baseline))
        observed_exceed_evt = float(np.mean(series_evt > baseline))

        gev = fit_gev(series_evt, baseline)
        c = float(gev["shape"])
        loc = float(gev["loc"])
        scale = float(gev["scale"])

        evt_prob = float(gev.get("exceed_prob", 0.0))
        evt_prob = min(max(evt_prob, 0.0), 1.0)

        ci_low, ci_high, ci_mean = self._bootstrap_evt_ci(
            series_evt=series_evt,
            baseline=baseline,
            n_boot=200,
            seed=int(self.results.get("demo_seed", 2025)),
        )

        durations = peak_duration_analysis(y, baseline)
        durations = durations if isinstance(durations, np.ndarray) else np.array([])
        durations_sec = durations.astype(float) * dt if durations.size > 0 else np.array([])
        max_duration = float(durations_sec.max()) if durations_sec.size > 0 else 0.0

        breaker_ok = (self.results.get("breaker_result") == "적합")

        pickup = self.results.get("breaker_pickup")
        tms = self.results.get("breaker_tms")
        Isc_A = self.results.get("Isc_A")

        tcc_margin = None
        tcc_available = True
        t_trip = self.results.get("t_trip_est", None)

        try:
            pickup = float(pickup)
            tms = float(tms)
            Isc_A = float(Isc_A)
            if pickup <= 0 or tms <= 0 or Isc_A <= 0:
                tcc_available = False
        except Exception:
            tcc_available = False

        if tcc_available:
            tcc_margin = tcc_protection_margin(Isc_A, max_duration, pickup, tms)
            if t_trip is None:
                try:
                    t_trip = float(tcc_curve(np.array([Isc_A]), pickup, tms)[0])
                except Exception:
                    t_trip = None
        else:
            tcc_margin = None
            t_trip = None

        # t_clear_* 먼저 파싱(아래 note_lines에서 쓰임)
        t_clear_input = self.results.get("t_clear_input", None)
        t_clear_used = self.results.get("t_clear_used", None)
        t_clear_policy = self.results.get("t_clear_policy", "NONE")
        try:
            t_clear_input = float(t_clear_input) if t_clear_input is not None else None
        except Exception:
            t_clear_input = None
        try:
            t_clear_used = float(t_clear_used) if t_clear_used is not None else None
        except Exception:
            t_clear_used = None

        risk = calculate_operation_risk(
            evt_prob=evt_prob,
            max_duration=max_duration,
            duration_limit=LIMIT_TIME,
            tcc_margin=tcc_margin,
            breaker_ok=breaker_ok,
            hard_status=hard_code,
            is_demo=bool(self.results.get("is_demo", False)),
        )

        note = self.results.get("data_source_note", "")
        is_demo = bool(self.results.get("is_demo", False))
        demo_tag = " [DEMO]" if is_demo else ""

        if is_demo:
            level = "참고(데모)"
            self.risk_head.setText(f"운전 위험도: {level}{demo_tag} | 점수 비활성")
        else:
            level = operation_risk_level(risk["total"])
            self.risk_head.setText(f"운전 위험도: {level} | 점수 {int(risk['total'])}/100{demo_tag}")

        meta_parts = []
        if I_load is not None:
            meta_parts.append(f"I_load={I_load:.0f}A")
        if I_design is not None:
            meta_parts.append(f"I_design={I_design:.0f}A")
        if I_allow is not None:
            meta_parts.append(f"I_allow(30℃)={I_allow:.0f}A")
        meta_parts.append(f"선택 기준선={baseline_label}:{baseline:.0f}A")
        meta_parts.append(f"EVT표본={len(series_evt)} ({evt_kind})")
        if note:
            meta_parts.append(note)
        self.meta_line.setText(" | ".join(meta_parts))

        # ---- 텍스트 블록 채우기(운전 위험도)
        prot_text = "N/A" if risk["protection_score"] is None else f"{risk['protection_score']:.1f}/20"
        total_text = "비활성" if is_demo else f"{risk['total']:.1f}/100"

        self.risk_break.setText(
            f"- EVT 위험 점수: {risk['evt_score']:.1f}/40\n"
            f"- 지속시간 위험 점수: {risk['time_score']:.1f}/40\n"
            f"- 보호 위험 점수(TCC): {prot_text}\n"
            f"- 총점: {total_text}\n"
            f"  · {risk.get('protection_note', '')}"
        )

        note_lines = []
        note_lines.append(f"기준선 정의: {baseline_label} = {baseline:.0f}A")
        note_lines.append(evt_def)
        note_lines.append(f"관측 초과율(샘플): {observed_exceed_sample:.2%}")
        note_lines.append(f"관측 초과율(EVT표본): {observed_exceed_evt:.2%}")
        if ci_low is not None and ci_high is not None:
            note_lines.append(f"EVT 초과확률(모델): {evt_prob:.2%} | 95% CI [{ci_low:.2%}, {ci_high:.2%}] (n=200)")
        else:
            note_lines.append(f"EVT 초과확률(모델): {evt_prob:.2%} | CI 계산 불가(표본 부족/실패)")

        if tcc_available and (t_trip is not None) and (t_clear_input is not None) and (t_trip > t_clear_input):
            note_lines.append(f"주의: TCC 추정({t_trip:.2f}s) > 입력({t_clear_input:.2f}s) → t_used=max 적용")

        if t_clear_used is not None:
            note_lines.append(f"단락열 적용 차단시간(t_used): {t_clear_used:.3f}s ({t_clear_policy})")

        if is_demo:
            note_lines.append("DEMO: 시뮬레이션 데이터이므로 정량 점수/DB 반영 비활성(그래프 UI 확인용)")

        self.risk_note.setText("\n".join(note_lines))

        bm_explain = (
            "Block Maxima는 '블록의 최대값'으로 표본을 구성합니다. "
            "따라서 샘플 초과율과 EVT 초과확률은 의미가 다를 수 있습니다."
            if "Block Maxima" in evt_method else
            "표본 수 부족으로 Raw fallback을 사용합니다."
        )

        # ---- 해석 요약(통으로 유지)
        self.text_label.setText(
            f"선택 기준선: {baseline_label} = {baseline:.0f} A\n"
            f"{note}\n\n"
            f"{evt_def}\n"
            f"- EVT 초과확률(모델): {evt_prob:.2%}\n"
            f"- 관측 초과율(샘플): {observed_exceed_sample:.2%}\n"
            f"- 관측 초과율(EVT표본): {observed_exceed_evt:.2%}\n"
            f"EVT 적용 방식: {evt_method}\n"
            f"{bm_explain}\n"
            f"- 표본수(블록수): {len(series_evt)}\n"
            f"- 외삽 위험: 기준선이 관측범위 밖이면 불확실 증가\n\n"
            f"지속시간 판정:\n"
            f"- 기준: {LIMIT_TIME:.1f} s\n"
            f"- 관측 최대 지속: {max_duration:.1f} s\n\n"
            f"단락열 차단시간:\n"
            f"- 입력 t_clear: {('-' if t_clear_input is None else f'{t_clear_input:.3f}s')}\n"
            f"- TCC 추정: {('-' if t_trip is None else f'{t_trip:.3f}s')}\n"
            f"- 적용 t_used: {('-' if t_clear_used is None else f'{t_clear_used:.3f}s')} ({t_clear_policy})"
        )

        # ===== 그래프(기존 유지) =====
        self.figure.clear()

        ax1 = self.figure.add_subplot(311)
        ax1.plot(t, y)
        ax1.axhline(baseline, linestyle="--", label=f"기준선({baseline_label})")
        ax1.set_title("부하 전류 시계열")
        ax1.set_xlabel("Time (s)")
        ax1.set_ylabel("Current (A)")
        if note:
            ax1.text(0.02, 0.92, note, transform=ax1.transAxes, fontsize=9)
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
        ax2.axvline(baseline, linestyle="--", label=f"기준선({baseline_label})")
        ax2.set_title(f"EVT (GEV) 분포 - {evt_method}")
        ax2.set_xlabel("Current (A)")
        ax2.set_ylabel("Density")
        ax2.text(0.02, 0.90, f"fit: c={c:.3f}, loc={loc:.1f}, scale={scale:.3f}", transform=ax2.transAxes, fontsize=9)
        ax2.text(0.02, 0.80, f"P_model(exceed)={evt_prob:.2%}", transform=ax2.transAxes, fontsize=9)
        ax2.text(0.02, 0.70, f"P_obs(sample)={observed_exceed_sample:.2%}", transform=ax2.transAxes, fontsize=9)
        if ci_low is not None and ci_high is not None:
            ax2.text(0.02, 0.60, f"CI95% [{ci_low:.2%},{ci_high:.2%}] (boot n=200)", transform=ax2.transAxes, fontsize=9)
        ax2.legend()

        ax3 = self.figure.add_subplot(313)
        ax3.set_xlabel("전류 (A)")
        ax3.set_ylabel("차단 시간 (s)")
        ax3.set_title("보호계전 TCC 참고 분석 (PASS + 계산 가능 시에만 점수 반영)")
        ax3.text(0.02, 0.90, "본 그래프는 참고용입니다.", transform=ax3.transAxes, fontsize=9)

        if tcc_available:
            Imax = max(float(np.max(y)), Isc_A, pickup * 2.0)
            I = np.logspace(np.log10(pickup * 1.05), np.log10(Imax * 2.0), 300)
            T = tcc_curve(I, pickup, tms)
            ax3.loglog(I, T, label="차단기 TCC")

            if Isc_A > 0 and t_trip is not None:
                ax3.scatter([Isc_A], [t_trip], zorder=5, label="● 단락전류 Isc")
                ax3.text(0.02, 0.72, f"예상 차단시간(TCC): {t_trip:.2f} s", transform=ax3.transAxes, fontsize=9)
                ax3.text(0.02, 0.64, f"pickup={pickup:.1f}A, TMS={tms:.3f}", transform=ax3.transAxes, fontsize=9)

                if t_clear_input is not None:
                    ax3.text(0.02, 0.56, f"입력 t_clear: {t_clear_input:.2f} s", transform=ax3.transAxes, fontsize=9)
                if t_clear_used is not None:
                    ax3.text(0.02, 0.48, f"적용 t_used: {t_clear_used:.2f} s ({t_clear_policy})", transform=ax3.transAxes, fontsize=9)
        else:
            ax3.text(0.02, 0.72, "TCC 파라미터 부족(pickup/TMS/Isc)으로 그래프 평가 불가", transform=ax3.transAxes, fontsize=9)

        if breaker_ok is False:
            ax3.text(0.02, 0.40, "Icu 부적합: 본 TCC 해석은 의미가 제한됩니다.", transform=ax3.transAxes, fontsize=9)

        ax3.legend()

        self.figure.tight_layout()
        self.figure.subplots_adjust(hspace=0.65)
        self.canvas.draw()

        assessment_id = self.results.get("assessment_id")
        asset_id = self.results.get("asset_id")

        try:
            if (not is_demo) and (assessment_id is not None):
                update_assessment_risk(
                    assessment_id=assessment_id,
                    risk_internal=float(risk["total"]),
                    risk_external=0.0
                )
        except Exception:
            pass

        compare_text = "이전 판정 데이터 없음"

        try:
            if asset_id is not None:
                rows = get_last_two_assessments(asset_id)
                if isinstance(rows, (list, tuple)) and len(rows) == 2:
                    curr = rows[0]
                    prev = rows[1]

                    _, curr_hard, curr_risk, _ = curr
                    _, prev_hard, prev_risk, _ = prev

                    delta = None
                    if curr_risk is not None and prev_risk is not None:
                        delta = float(curr_risk) - float(prev_risk)

                    arrow = "→"
                    if delta is not None:
                        arrow = "▲" if delta > 0 else "▼" if delta < 0 else "→"
                    delta_txt = f"{delta:+.1f}" if delta is not None else "-"

                    cr = f"{float(curr_risk):.1f}" if curr_risk is not None else "-"
                    pr = f"{float(prev_risk):.1f}" if prev_risk is not None else "-"

                    compare_text = (
                        "이전 판정 대비 변화(DB)\n"
                        f"- 설비 판정: {prev_hard} → {curr_hard}\n"
                        f"- 위험도 점수: {pr} → {cr} ({arrow} {delta_txt})"
                    )
        except Exception:
            compare_text = "이전 판정 데이터 없음"

        if compare_text == "이전 판정 데이터 없음":
            prev_local = self._load_prev()
            if isinstance(prev_local, dict) and prev_local:
                compare_text = (
                    "이전 판정 대비 변화(로컬)\n"
                    f"- 규정판정: {prev_local.get('equipment_status', '-')} → {hard_code}\n"
                    f"- 차단기: {prev_local.get('breaker_result', '-')} → {self.results.get('breaker_result', '-')}\n"
                )

        self.compare_label.setText(compare_text)

    def go_result(self):
        p = self.parent()
        if p is None:
            return
        if hasattr(p, "result_page"):
            p.setCurrentWidget(p.result_page)
