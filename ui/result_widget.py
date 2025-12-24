# ui/result_widget.py
import json
import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QScrollArea, QMessageBox, QFrame, QGridLayout
)
from PySide6.QtCore import Qt

from ui.components.result_card import ResultCard

from calculations.engineering import (
    rated_current,
    short_circuit_current,
    breaker_judgement,
    cable_allowable_hard_op,
    thermal_adiabatic_check,
)

from analysis.protection_tcc import tcc_curve


class ResultWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        # 회색 줄배경(라벨 뒤 배경) 제거: 상위 스타일의 QLabel background-color가 카드 위에서 줄처럼 보이는 문제 방지
        self.setStyleSheet("QLabel { background: transparent; }")

        def _plain(label: QLabel, obj: str = None):
            if obj:
                label.setObjectName(obj)
            label.setWordWrap(True)
            label.setTextFormat(Qt.PlainText)
            label.setAutoFillBackground(False)
            label.setStyleSheet("background: transparent;")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(10)

        nav = QWidget()
        nav_l = QHBoxLayout(nav)
        nav_l.setContentsMargins(0, 0, 0, 0)
        nav_l.setSpacing(10)

        self.btn_home = QPushButton("← 홈으로")
        self.btn_input = QPushButton("← 입력으로")
        self.btn_detail = QPushButton("상세 분석 →")
        self.btn_detail.setObjectName("PrimaryButton")

        self.btn_home.setMinimumHeight(40)
        self.btn_input.setMinimumHeight(40)
        self.btn_detail.setMinimumHeight(40)

        self.btn_home.clicked.connect(self.go_home)
        self.btn_input.clicked.connect(self.go_input)
        self.btn_detail.clicked.connect(self.go_detail)

        nav_l.addWidget(self.btn_home)
        nav_l.addWidget(self.btn_input)
        nav_l.addStretch(1)
        nav_l.addWidget(self.btn_detail)
        outer.addWidget(nav)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        outer.addWidget(self.scroll)

        body = QWidget()
        self.scroll.setWidget(body)

        self.layout = QVBoxLayout(body)
        self.layout.setContentsMargins(30, 25, 30, 30)
        self.layout.setSpacing(12)

        title = QLabel("계산 결과")
        title.setObjectName("H1")
        title.setTextFormat(Qt.PlainText)
        title.setAutoFillBackground(False)
        title.setStyleSheet("background: transparent;")
        self.layout.addWidget(title)

        # ===== 최종 판정 헤더 =====
        header = QFrame()
        header.setObjectName("Card")
        header_l = QVBoxLayout(header)
        header_l.setContentsMargins(16, 14, 16, 14)
        header_l.setSpacing(8)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(10)

        self.badge = QLabel("")
        self.badge.setObjectName("Badge")
        self.badge.setAlignment(Qt.AlignCenter)
        self.badge.setTextFormat(Qt.PlainText)
        self.badge.setAutoFillBackground(False)
        self.badge.setStyleSheet("background: transparent;")

        self.final_line = QLabel("")
        _plain(self.final_line, "H2")

        top_row.addWidget(self.badge, 0, Qt.AlignLeft)
        top_row.addWidget(self.final_line, 1)
        header_l.addLayout(top_row)

        self.final_sub = QLabel("")
        _plain(self.final_sub, "Muted")
        header_l.addWidget(self.final_sub)

        self.layout.addWidget(header)

        # ===== 요약 카드 =====
        self.card_summary = ResultCard("요약")
        self.summary_grid = QWidget()
        self.summary_grid_l = QGridLayout(self.summary_grid)
        self.summary_grid_l.setContentsMargins(0, 0, 0, 0)
        self.summary_grid_l.setHorizontalSpacing(14)
        self.summary_grid_l.setVerticalSpacing(6)

        self._summary_rows = []
        for i in range(10):
            k = QLabel("")
            v = QLabel("")
            k.setObjectName("Key")
            v.setObjectName("Value")

            k.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            v.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

            k.setTextFormat(Qt.PlainText)
            v.setTextFormat(Qt.PlainText)
            k.setAutoFillBackground(False)
            v.setAutoFillBackground(False)
            k.setStyleSheet("background: transparent;")
            v.setStyleSheet("background: transparent;")

            self.summary_grid_l.addWidget(k, i, 0)
            self.summary_grid_l.addWidget(v, i, 1)
            self._summary_rows.append((k, v))

        self.card_summary.add_widget(self.summary_grid)
        self.layout.addWidget(self.card_summary)

        # ===== 카드들 =====
        self.card_breaker = ResultCard("차단기")
        self.lb_breaker = QLabel("")
        _plain(self.lb_breaker, "CardBody")
        self.card_breaker.add_widget(self.lb_breaker)
        self.layout.addWidget(self.card_breaker)

        self.card_cable = ResultCard("케이블")
        self.lb_cable = QLabel("")
        _plain(self.lb_cable, "CardBody")
        self.card_cable.add_widget(self.lb_cable)
        self.layout.addWidget(self.card_cable)

        self.card_thermal = ResultCard("열상승(단락열)")
        self.lb_thermal = QLabel("")
        _plain(self.lb_thermal, "CardBody")
        self.card_thermal.add_widget(self.lb_thermal)
        self.layout.addWidget(self.card_thermal)

        self.card_compare = ResultCard("이전과 비교")
        self.lb_compare = QLabel("")
        _plain(self.lb_compare, "CardBody")
        self.card_compare.add_widget(self.lb_compare)
        self.layout.addWidget(self.card_compare)

        self.notice = QLabel(
            "※ 운전 위험도(EVT/지속시간/보호)는 상세 분석에서 참고 지표로 제공됩니다.\n"
            "※ 설비 판정(차단기/케이블/열상승)은 법·기준 기반의 최종 판단입니다."
        )
        _plain(self.notice, "Muted")
        self.layout.addWidget(self.notice)

        self.layout.addStretch(1)

        self._last_results = None
        self._last_input = None

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

    def _save_prev(self, payload: dict):
        path = self._prev_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    @staticmethod
    def _safe_float(x):
        try:
            return float(x)
        except Exception:
            return None

    @staticmethod
    def _fmt_a(x):
        if x is None:
            return "-"
        try:
            return f"{float(x):,.1f} A"
        except Exception:
            return "-"

    @staticmethod
    def _fmt_ka_from_a(x_a):
        if x_a is None:
            return "-"
        try:
            ka = float(x_a) / 1000.0
            return f"{ka:,.1f} kA ({float(x_a):,.0f} A)"
        except Exception:
            return "-"

    @staticmethod
    def _auto_tcc_params(In_A, I_load, Isc_A):
        base = None
        if In_A is not None and In_A > 0:
            base = float(In_A)
        elif I_load is not None and I_load > 0:
            base = float(I_load)
        else:
            return None, None

        pickup = base * 1.25
        tms = 0.10

        try:
            if I_load is not None and I_load > 0 and pickup < (0.8 * float(I_load)):
                pickup = float(I_load) * 1.10
        except Exception:
            pass

        try:
            if Isc_A is not None and Isc_A > 0 and pickup >= Isc_A:
                pickup = Isc_A * 0.3
        except Exception:
            pass

        if pickup <= 0 or tms <= 0:
            return None, None
        return float(pickup), float(tms)

    @staticmethod
    def _breaker_margin_grade(protection_ratio):
        if protection_ratio is None:
            return None, None
        try:
            r = float(protection_ratio)
        except Exception:
            return None, None

        spare = r - 1.0
        spare_pct = spare * 100.0
        if spare < 0:
            return "FAIL", spare_pct
        if spare < 0.05:
            return "위험(<5%)", spare_pct
        if spare < 0.10:
            return "경고(<10%)", spare_pct
        if spare < 0.20:
            return "주의(<20%)", spare_pct
        return "충분", spare_pct

    def _set_badge(self, equipment_status: str):
        s = str(equipment_status or "").upper()
        if s == "PASS":
            self.badge.setObjectName("BadgeSuccess")
            self.badge.setText("PASS")
        elif s == "FAIL":
            self.badge.setObjectName("BadgeDanger")
            self.badge.setText("FAIL")
        else:
            self.badge.setObjectName("BadgeWarn")
            self.badge.setText("NEED_MORE")

        self.badge.style().unpolish(self.badge)
        self.badge.style().polish(self.badge)

    def _set_summary_rows(self, rows):
        rows = rows or []
        for i, (k, v) in enumerate(self._summary_rows):
            if i < len(rows):
                k.setText(rows[i][0])
                v.setText(rows[i][1])
            else:
                k.setText("")
                v.setText("")

    def go_home(self):
        if hasattr(self.parent, "home_page"):
            self.parent.setCurrentWidget(self.parent.home_page)

    def go_input(self):
        if hasattr(self.parent, "input_page"):
            self.parent.setCurrentWidget(self.parent.input_page)

    def go_detail(self):
        if self._last_input is None or self._last_results is None:
            QMessageBox.information(self, "안내", "먼저 계산을 실행해 주세요.")
            return
        if hasattr(self.parent, "detail_page"):
            self.parent.detail_page.load_data(self._last_input, self._last_results)
            self.parent.setCurrentWidget(self.parent.detail_page)

    def run_calculation(self, data: dict):
        merged = dict(data)
        cd = getattr(self.parent, "cable_data", None)
        if isinstance(cd, dict) and cd:
            merged.update(cd)

        prev = self._load_prev()
        self._last_input = merged

        V = self._safe_float(merged.get("V"))
        S_kVA = self._safe_float(merged.get("S"))
        Zpct = self._safe_float(merged.get("Z"))
        I_load = self._safe_float(merged.get("I_load"))
        breaker_kA = self._safe_float(merged.get("breaker"))
        standard = str(merged.get("standard") or "KESC").upper()

        t_clear_input = merged.get("t_clear", None)
        t_clear_input = self._safe_float(t_clear_input) if t_clear_input is not None else None

        dt = self._safe_float(merged.get("dt", 1.0))
        if dt is None or dt <= 0:
            dt = 1.0

        In_A = rated_current(V, S_kVA) if (V is not None and S_kVA is not None and V > 0) else None
        Isc_A = (
            short_circuit_current(V, S_kVA, Zpct)
            if (V is not None and S_kVA is not None and Zpct is not None and V > 0 and Zpct > 0)
            else None
        )

        breaker_result = "판정 불가"
        breaker_reason = "입력 누락으로 계산 불가"
        protection_ratio = None
        breaker_margin = None
        breaker_margin_pct = None

        if Isc_A is not None and breaker_kA is not None:
            breaker_result = breaker_judgement(Isc_A, breaker_kA, standard)
            Icu_A = breaker_kA * 1000.0
            protection_ratio = (Icu_A / Isc_A) if Isc_A > 0 else None

            margin = 1.1 if standard == "IEC" else 1.0
            required_A = Isc_A * margin

            if Icu_A >= required_A:
                spare = (Icu_A / required_A) - 1.0
                breaker_reason = (
                    f"Icu {breaker_kA:,.1f} kA ≥ Isc {Isc_A/1000.0:,.1f} kA "
                    f"(계수 {margin:.2f}, 여유 {spare*100.0:,.1f}%)"
                )
            else:
                lack = 1.0 - (Icu_A / required_A)
                breaker_reason = (
                    f"Icu {breaker_kA:,.1f} kA < Isc {Isc_A/1000.0:,.1f} kA "
                    f"(계수 {margin:.2f}, 부족 {lack*100.0:,.1f}%)"
                )

            breaker_margin, breaker_margin_pct = self._breaker_margin_grade(protection_ratio)

        design_margin = 1.25
        I_design_calc = None
        if I_load is not None and I_load > 0:
            I_design_calc = float(I_load) * float(design_margin)

        cable_mode = merged.get("cable_mode") or merged.get("mode")
        table_profile = merged.get("cable_table_profile") or merged.get("table_profile")

        if str(standard).upper() == "KESC":
            table_profile = "KESC_DEFAULT"

        cable_material = merged.get("cable_material") or merged.get("material")
        cable_insulation = merged.get("cable_insulation") or merged.get("insulation")
        cable_install = merged.get("cable_install") or merged.get("install")
        cable_parallel = merged.get("cable_parallel") or merged.get("parallel")
        cable_section_in = merged.get("cable_section_mm2_input") or merged.get("section_mm2_input")
        cable_ambient = merged.get("cable_ambient") or merged.get("ambient")

        ambient_op = self._safe_float(merged.get("ambient_op")) if merged.get("ambient_op") is not None else None
        if ambient_op is None and cable_ambient is not None:
            ambient_op = self._safe_float(cable_ambient)

        has_cable_input = isinstance(cd, dict) and bool(cd)

        if not has_cable_input:
            cable_hard = {"status": "계산 불가", "reason": "입력 누락으로 계산 불가: 케이블 조건 미입력"}
            cable_op = {"status": "평가 불가", "reason": "운영 조건 평가 불가: 케이블 조건 미입력"}
        else:
            cable_hard, cable_op = cable_allowable_hard_op(
                I_load=I_load if I_load is not None else 0.0,
                material=cable_material,
                insulation=cable_insulation,
                install=cable_install,
                parallel=cable_parallel,
                mode=cable_mode or "AUTO",
                section_mm2_input=cable_section_in,
                ambient_op=ambient_op,
                standard=standard,
                table_profile=table_profile,
                design_margin=design_margin,
            )

        hard_status = cable_hard.get("status", "계산 불가")
        hard_reason = cable_hard.get("reason", "")

        hard_I_allow = cable_hard.get("I_allow_total", None)
        hard_S_used = cable_hard.get("section_mm2_used", None)
        hard_profile_used = cable_hard.get("table_profile_used", None)

        I_design = cable_hard.get("I_design", None)
        if I_design is None:
            I_design = I_design_calc

        cable_lines = []
        cable_lines.append(f"판정(Hard, 30℃ 고정): {hard_status}")
        if I_design is not None:
            cable_lines.append(f"- I_design: {float(I_design):.0f} A (I_load×{design_margin:.2f})")
        if hard_S_used is not None:
            cable_lines.append(f"- 선정 S: {float(hard_S_used):.0f} mm²")
        if hard_I_allow is not None:
            cable_lines.append(f"- 허용전류(30℃): {float(hard_I_allow):,.0f} A")
        if hard_profile_used:
            cable_lines.append(f"- 테이블: {hard_profile_used}")

        if isinstance(cable_op, dict):
            op_status = cable_op.get("status", "평가 불가")
            op_amb = cable_op.get("ambient", None)
            op_k_temp = cable_op.get("k_temp", None)
            op_I_allow = cable_op.get("I_allow_total", None)
            cable_lines.append("")
            cable_lines.append(f"운영 조건 평가: {op_status}")
            if op_amb is not None:
                cable_lines.append(f"- 운영온도: {float(op_amb):.1f} ℃")
            if op_k_temp is not None:
                cable_lines.append(f"- k_temp: {float(op_k_temp):.3f}")
            if op_I_allow is not None:
                cable_lines.append(f"- 보정 허용전류: {float(op_I_allow):,.0f} A")
        else:
            cable_lines.append("")
            cable_lines.append("운영 조건 평가: 평가 불가")

        if hard_reason:
            hr = str(hard_reason).strip()
            if len(hr) > 260:
                hr = hr[:260].rstrip() + " …"
            cable_lines.append("")
            cable_lines.append(f"근거: {hr}")

        self.lb_cable.setText("\n".join(cable_lines))

        breaker_pickup, breaker_tms = self._auto_tcc_params(In_A, I_load, Isc_A)

        t_trip_est = None
        tcc_available = True
        try:
            if breaker_pickup is None or breaker_tms is None or Isc_A is None:
                tcc_available = False
            else:
                p = float(breaker_pickup)
                tms = float(breaker_tms)
                isc = float(Isc_A)
                if p <= 0 or tms <= 0 or isc <= 0:
                    tcc_available = False
        except Exception:
            tcc_available = False

        if tcc_available:
            try:
                t_trip_est = float(tcc_curve([float(Isc_A)], float(breaker_pickup), float(breaker_tms))[0])
            except Exception:
                t_trip_est = None

        t_clear_used = None
        t_clear_policy = "NONE"
        if t_trip_est is not None and t_clear_input is not None:
            t_clear_used = max(float(t_clear_input), float(t_trip_est))
            t_clear_policy = "MAX(TCC,INPUT)"
        elif t_trip_est is not None:
            t_clear_used = float(t_trip_est)
            t_clear_policy = "TCC_DEFAULT"
        elif t_clear_input is not None:
            t_clear_used = float(t_clear_input)
            t_clear_policy = "INPUT_ONLY"
        else:
            t_clear_used = None
            t_clear_policy = "NONE"

        section_used = cable_hard.get("section_mm2_used", None) if isinstance(cable_hard, dict) else None
        thermal = thermal_adiabatic_check(
            I_sc_A=Isc_A,
            t_clear_s=t_clear_used,
            section_mm2_used=section_used,
            material=cable_material,
            insulation=cable_insulation,
            standard=standard,
            t_clear_input=t_clear_input,
            t_trip_est=t_trip_est,
            t_clear_policy=t_clear_policy,
        )
        thermal_status = thermal.get("status", "계산 불가")
        thermal_reason = thermal.get("reason", "")

        tr = str(thermal_reason).strip()
        if len(tr) > 260:
            tr = tr[:260].rstrip() + " …"

        thermal_lines = [
            f"판정: {thermal_status}",
            f"- t_clear 입력: {('-' if t_clear_input is None else f'{t_clear_input:.3f}s')}",
            f"- TCC 추정: {('-' if t_trip_est is None else f'{t_trip_est:.3f}s')}",
            f"- 적용 t_clear: {('-' if t_clear_used is None else f'{t_clear_used:.3f}s')} ({t_clear_policy})",
        ]
        if tr:
            thermal_lines.append(f"근거: {tr}")

        self.lb_thermal.setText("\n".join(thermal_lines))

        breaker_ok = (breaker_result == "적합")
        breaker_na = (breaker_result == "판정 불가")
        cable_fail = (hard_status == "부적합")
        thermal_fail = (thermal_status == "부적합")
        cable_na = (hard_status == "계산 불가")
        thermal_na = (thermal_status == "계산 불가")

        if (not breaker_ok) and (not breaker_na):
            equipment_status = "FAIL"
            equipment_final_line = "규정 판정(Hard Engineering): FAIL"
            equipment_final_sub = "차단기 차단용량(Icu) 기준 미달"
        elif cable_fail or thermal_fail:
            equipment_status = "FAIL"
            equipment_final_line = "규정 판정(Hard Engineering): FAIL"
            reasons = []
            if cable_fail:
                reasons.append("케이블 허용전류 기준 미달")
            if thermal_fail:
                reasons.append("단락열(단열식) 기준 미달")
            equipment_final_sub = " / ".join(reasons) if reasons else "규정 기준 미달 항목 존재"
        else:
            if breaker_na or cable_na or thermal_na:
                equipment_status = "NEED_MORE"
                equipment_final_line = "규정 판정(Hard Engineering): NEED_MORE"
                need = []
                if breaker_na:
                    need.append("차단기/단락 입력")
                if cable_na:
                    need.append("케이블 조건")
                if thermal_na:
                    need.append("차단시간(t_clear) 또는 TCC 추정치")
                equipment_final_sub = "추가 입력 후 재평가 필요: " + (", ".join(need) if need else "-")
            else:
                equipment_status = "PASS"
                equipment_final_line = "규정 판정(Hard Engineering): PASS"
                equipment_final_sub = "차단기/케이블/열상승 항목이 기준을 충족"

        self._set_badge(equipment_status)
        self.final_line.setText(equipment_final_line)
        self.final_sub.setText(equipment_final_sub)

        In_txt = self._fmt_a(In_A)
        Isc_txt = self._fmt_ka_from_a(Isc_A)

        pm_txt = "-"
        if protection_ratio is not None:
            try:
                pm = float(protection_ratio)
                pm_txt = f"{pm:.2f}" + (" (부족)" if pm < 1.0 else "")
            except Exception:
                pm_txt = "-"

        margin_txt = "-"
        if breaker_margin is not None and breaker_margin_pct is not None:
            margin_txt = f"{breaker_margin} ({breaker_margin_pct:+.1f}%)"

        idesign_txt = "-"
        if I_design is not None:
            idesign_txt = f"{float(I_design):.0f} A (×{design_margin:.2f})"

        iallow_txt = "-"
        if hard_I_allow is not None:
            try:
                iallow_txt = f"{float(hard_I_allow):,.0f} A"
            except Exception:
                iallow_txt = "-"

        in_meta = []
        if V is not None:
            in_meta.append(f"V={V:.3f}kV")
        if S_kVA is not None:
            in_meta.append(f"S={S_kVA:.0f}kVA")
        in_meta_txt = " / ".join(in_meta) if in_meta else "-"

        rows = [
            ("기준(Standard)", standard),
            ("정격전류(In_tr)", f"{In_txt} ({in_meta_txt})"),
            ("단락전류(Isc)", Isc_txt),
            ("차단기 여유(Icu/Isc)", pm_txt),
            ("차단기 여유 등급", margin_txt),
            ("부하전류(I_load)", self._fmt_a(I_load)),
            ("설계전류(I_design)", idesign_txt),
            ("허용전류(30℃)", iallow_txt),
            ("케이블(Hard)", hard_status),
            ("열상승(단락열)", thermal_status),
        ]
        self._set_summary_rows(rows)

        breaker_lines = [f"판정: {breaker_result}"]
        breaker_lines.append(f"- 근거: {breaker_reason}")
        breaker_lines.append(f"- 여유 등급: {margin_txt}")
        breaker_lines.append("- 참고: 여유율 3~5% 수준이면 현업 리뷰에서 위험 영역으로 보는 경우가 많습니다.")
        self.lb_breaker.setText("\n".join(breaker_lines))

        compare_text = "이전 판정 데이터 없음"
        if isinstance(prev, dict) and prev:
            def _chg(label, old, new):
                if old == new:
                    return f"- {label}: 유지({new})"
                return f"- {label}: {old} → {new}"

            compare_lines = [
                _chg("규정판정", prev.get("equipment_status"), equipment_status),
                _chg("차단기", prev.get("breaker_result"), breaker_result),
                _chg("케이블(Hard)", prev.get("cable_hard_status"), hard_status),
                _chg("열상승", prev.get("thermal_status"), thermal_status),
            ]
            compare_text = "\n".join(compare_lines)

        self.lb_compare.setText(compare_text)

        self._last_results = {
            "dt": dt,
            "limit_current": I_load,
            "I_load": I_load,
            "design_margin": design_margin,
            "I_design": I_design,
            "I_allow_hard": hard_I_allow,
            "t_clear_input": t_clear_input,
            "t_trip_est": t_trip_est,
            "t_clear_used": t_clear_used,
            "t_clear_policy": t_clear_policy,
            "Isc_A": Isc_A,
            "In_A": In_A,
            "breaker_result": breaker_result,
            "protection_ratio": protection_ratio,
            "breaker_margin_grade": breaker_margin,
            "breaker_margin_pct": breaker_margin_pct,
            "equipment_status": equipment_status,
            "equipment_final_line": equipment_final_line,
            "equipment_final_sub": equipment_final_sub,
            "cable_hard": cable_hard,
            "cable_op": cable_op,
            "thermal": thermal,
            "standard": standard,
            "breaker_pickup": breaker_pickup,
            "breaker_tms": breaker_tms,
            "demo_seed": 2025,
        }

        save_payload = {
            "equipment_status": equipment_status,
            "breaker_result": breaker_result,
            "cable_hard_status": hard_status,
            "thermal_status": thermal_status,
        }
        self._save_prev(save_payload)
