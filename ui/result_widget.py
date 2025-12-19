# ui/result_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QScrollArea, QMessageBox
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


class ResultWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(10)

        # 상단 네비
        nav = QWidget()
        nav_l = QHBoxLayout(nav)
        nav_l.setContentsMargins(0, 0, 0, 0)
        nav_l.setSpacing(10)

        self.btn_home = QPushButton("← 홈으로")
        self.btn_input = QPushButton("← 입력으로")
        self.btn_detail = QPushButton("상세 분석 →")

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

        # 스크롤
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
        title.setStyleSheet("font-weight:900; font-size:18px;")
        self.layout.addWidget(title)

        # 최종 결론(1줄)
        self.final_line = QLabel("")
        self.final_line.setWordWrap(True)
        self.final_line.setStyleSheet("font-weight:900; font-size:16px;")
        self.layout.addWidget(self.final_line)

        self.final_sub = QLabel("")
        self.final_sub.setWordWrap(True)
        self.final_sub.setStyleSheet("color:#374151;")
        self.layout.addWidget(self.final_sub)

        # 카드들
        self.card_summary = ResultCard("계산 결과(요약)")
        self.lb_summary = QLabel("")
        self.lb_summary.setWordWrap(True)
        self.lb_summary.setStyleSheet("color:#111827;")
        self.card_summary.add_widget(self.lb_summary)
        self.layout.addWidget(self.card_summary)

        self.card_breaker = ResultCard("차단기 판정(법/기준)")
        self.lb_breaker = QLabel("")
        self.lb_breaker.setWordWrap(True)
        self.lb_breaker.setStyleSheet("color:#111827;")
        self.card_breaker.add_widget(self.lb_breaker)
        self.layout.addWidget(self.card_breaker)

        self.card_cable = ResultCard("케이블 판정")
        self.lb_cable = QLabel("")
        self.lb_cable.setWordWrap(True)
        self.lb_cable.setStyleSheet("color:#111827;")
        self.card_cable.add_widget(self.lb_cable)
        self.layout.addWidget(self.card_cable)

        self.card_thermal = ResultCard("열상승(단락열) 판정")
        self.lb_thermal = QLabel("")
        self.lb_thermal.setWordWrap(True)
        self.lb_thermal.setStyleSheet("color:#111827;")
        self.card_thermal.add_widget(self.lb_thermal)
        self.layout.addWidget(self.card_thermal)

        self.notice = QLabel(
            "※ 운전 위험도(EVT/지속시간/보호)는 상세 분석에서 참고 지표로 제공됩니다.\n"
            "※ 설비 판정(차단기/케이블/열상승)은 법·기준 기반의 최종 판단입니다."
        )
        self.notice.setWordWrap(True)
        self.notice.setStyleSheet("color:#374151; font-size:13px;")
        self.layout.addWidget(self.notice)

        self.layout.addStretch(1)

        self._last_results = None
        self._last_input = None

    # ------------------------------
    # 유틸
    # ------------------------------
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

    # ------------------------------
    # 네비
    # ------------------------------
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

    # ------------------------------
    # 핵심: 계산 실행
    # ------------------------------
    def run_calculation(self, data: dict):
        # ✅ 저장된 케이블 조건을 무조건 합친다(저장했는데 미입력 방지)
        merged = dict(data)
        cd = getattr(self.parent, "cable_data", None)
        if isinstance(cd, dict) and cd:
            merged.update(cd)

        self._last_input = merged

        V = self._safe_float(merged.get("V"))
        S_kVA = self._safe_float(merged.get("S"))
        Zpct = self._safe_float(merged.get("Z"))
        I_load = self._safe_float(merged.get("I_load"))
        breaker_kA = self._safe_float(merged.get("breaker"))
        standard = str(merged.get("standard") or "KESC").upper()  # ✅ 기본 KESC

        t_clear = merged.get("t_clear", None)
        t_clear = self._safe_float(t_clear) if t_clear is not None else None

        dt = self._safe_float(merged.get("dt", 1.0))
        if dt is None or dt <= 0:
            dt = 1.0

        # --------------------------
        # 기본 계산
        # --------------------------
        In_A = rated_current(V, S_kVA) if (V is not None and S_kVA is not None and V > 0) else None
        Isc_A = (
            short_circuit_current(V, S_kVA, Zpct)
            if (V is not None and S_kVA is not None and Zpct is not None and V > 0 and Zpct > 0)
            else None
        )

        # --------------------------
        # 차단기 판정
        # --------------------------
        breaker_result = "판정 불가"
        breaker_reason = "입력 누락으로 계산 불가"
        protection_ratio = None  # Icu/Isc

        if Isc_A is not None and breaker_kA is not None:
            breaker_result = breaker_judgement(Isc_A, breaker_kA, standard)
            Icu_A = breaker_kA * 1000.0
            protection_ratio = (Icu_A / Isc_A) if Isc_A > 0 else None

            margin = 1.1 if standard == "IEC" else 1.0
            required_A = Isc_A * margin
            if Icu_A >= required_A:
                spare = (Icu_A / required_A) - 1.0
                breaker_reason = (
                    "차단기 판정: 적합\n"
                    f"(차단기 Icu {breaker_kA:,.1f} kA ≥ 단락전류 {Isc_A/1000.0:,.1f} kA, "
                    f"기준계수 {margin:.2f}, 여유 {spare*100.0:,.1f}%)"
                )
            else:
                lack = 1.0 - (Icu_A / required_A)
                breaker_reason = (
                    "차단기 판정: 부적합\n"
                    f"(차단기 Icu {breaker_kA:,.1f} kA < 단락전류 {Isc_A/1000.0:,.1f} kA, "
                    f"기준계수 {margin:.2f}, 부족 {lack*100.0:,.1f}%)"
                )

        # --------------------------
        # 케이블 판정: Hard(30℃) + 운영조건(Optional)
        # --------------------------
        cable_mode = merged.get("cable_mode", None)
        cable_profile = merged.get("cable_table_profile", None)  # ✅ 이걸 engineering에 전달해야 진짜 반영됨
        cable_material = merged.get("cable_material", None)
        cable_insulation = merged.get("cable_insulation", None)
        cable_install = merged.get("cable_install", None)
        cable_parallel = merged.get("cable_parallel", None)
        cable_section_in = merged.get("cable_section_mm2_input", None)

        # 운영 온도(Optional): ambient_op(기상/DB) 우선, 없으면 케이블 페이지 입력값
        ambient_op = self._safe_float(merged.get("ambient_op")) if merged.get("ambient_op") is not None else None
        if ambient_op is None:
            ambient_op = self._safe_float(merged.get("cable_ambient")) if merged.get("cable_ambient") is not None else None

        # ✅ 케이블 입력 존재 판정(값이 None이어도 "키가 존재"하면 저장했다고 봄)
        cable_keys = [
            "cable_mode", "cable_table_profile",
            "cable_material", "cable_insulation", "cable_install",
            "cable_parallel", "cable_section_mm2_input", "cable_ambient"
        ]
        has_cable_input = any(k in merged for k in cable_keys)

        if not has_cable_input:
            cable_hard = {"status": "계산 불가", "reason": "입력 누락으로 계산 불가: 케이블 조건 미입력"}
            cable_op = {"status": "평가 불가", "reason": "운영 조건 평가 불가: 케이블 조건 미입력"}
        else:
            # ✅ engineering.py 수정본 시그니처 기준: standard/table_profile 전달
            cable_hard, cable_op = cable_allowable_hard_op(
                I_load=I_load if I_load is not None else 0.0,
                material=cable_material,
                insulation=cable_insulation,
                install=cable_install,
                parallel=cable_parallel,
                mode=cable_mode or "AUTO",
                section_mm2_input=cable_section_in,
                ambient_op=ambient_op,
                standard=standard,                  # ✅ KESC/IEC 반영
                table_profile=cable_profile,        # ✅ 보수/현실 프로파일 반영
            )

        hard_status = cable_hard.get("status", "계산 불가")
        hard_reason = cable_hard.get("reason", "")
        hard_I_allow = cable_hard.get("I_allow_total", None)
        hard_S_used = cable_hard.get("section_mm2_used", None)
        hard_profile_used = cable_hard.get("table_profile_used", None)

        cable_text = (
            "본 케이블 평가는 아래 구조로 분리됩니다.\n"
            "항목\t적용 방식\n"
            "설비 판정(Hard)\t기준 온도(30℃) 고정\n"
            "운영 조건 보정(Optional)\t기상 데이터로 허용전류 재평가\n"
            "운전 위험도\tEVT / 지속시간 / 보호\n\n"
            "즉, 기상 데이터는 ‘설계 적합성 판단’이 아니라\n"
            "‘운영 조건에서의 여유도 감소’를 보여주는 용도입니다.\n\n"
            "[설비 기준 판정]\n"
            f"- 기준 온도(30℃) 기준: {hard_status}\n"
        )
        if hard_S_used is not None:
            cable_text += f"- 최종 단면적 S: {float(hard_S_used):.0f} mm²\n"
        if hard_I_allow is not None:
            cable_text += f"- 총 허용전류(30℃): {float(hard_I_allow):,.0f} A\n"
        if hard_profile_used:
            cable_text += f"- 테이블 적용: {hard_profile_used}\n"
        cable_text += f"- 근거: {hard_reason}\n\n"

        cable_text += "[운영 조건 평가]\n"
        if not isinstance(cable_op, dict):
            cable_text += "- 운영 조건 평가: 평가 불가\n"
        else:
            op_status = cable_op.get("status", "평가 불가")
            op_amb = cable_op.get("ambient", None)
            op_k_temp = cable_op.get("k_temp", None)
            op_I_allow = cable_op.get("I_allow_total", None)
            op_profile_used = cable_op.get("table_profile_used", None)

            cable_text += f"- 운영 조건 평가: {op_status}\n"
            if op_amb is not None:
                cable_text += f"- 최근/운영 온도: {float(op_amb):.1f} ℃\n"
            if op_k_temp is not None:
                cable_text += f"- 온도 보정계수 k_temp: {float(op_k_temp):.3f}\n"
            if op_I_allow is not None:
                cable_text += f"- 보정 후 허용전류: {float(op_I_allow):,.0f} A\n"
            if op_profile_used:
                cable_text += f"- 테이블 적용: {op_profile_used}\n"
            cable_text += f"- 해석: {cable_op.get('reason', '')}\n"
            cable_text += "- 결론: 운영 조건에서 운전 여유(허용전류)가 감소할 수 있습니다.\n"

        self.lb_cable.setText(cable_text)

        # --------------------------
        # 열상승(단락열) 판정: S는 케이블 최종 S 사용
        # --------------------------
        section_used = cable_hard.get("section_mm2_used", None) if isinstance(cable_hard, dict) else None

        thermal = thermal_adiabatic_check(
            I_sc_A=Isc_A,
            t_clear_s=t_clear,
            section_mm2_used=section_used,
            material=cable_material,
            insulation=cable_insulation,
            standard=standard,
        )
        thermal_status = thermal.get("status", "계산 불가")
        thermal_reason = thermal.get("reason", "")

        self.lb_thermal.setText(f"열상승 판정: {thermal_status}\n{thermal_reason}")

        # --------------------------
        # 최종 설비 판정(Hard Engineering)
        # --------------------------
        breaker_ok = (breaker_result == "적합")
        breaker_na = (breaker_result == "판정 불가")

        cable_fail = (hard_status == "부적합")
        thermal_fail = (thermal_status == "부적합")

        cable_na = (hard_status == "계산 불가")
        thermal_na = (thermal_status == "계산 불가")

        if (not breaker_ok) and (not breaker_na):
            equipment_status = "FAIL"
            equipment_final_line = "최종 결론(설비 기준): 부적합"
            equipment_final_sub = "차단기 차단용량(Icu) 기준 미달로 설비 기준을 충족하지 않습니다."
        elif cable_fail or thermal_fail:
            equipment_status = "FAIL"
            equipment_final_line = "최종 결론(설비 기준): 부적합"
            reasons = []
            if cable_fail:
                reasons.append("케이블 허용전류 기준 미달")
            if thermal_fail:
                reasons.append("단락열(단열식) 기준 미달")
            equipment_final_sub = " / ".join(reasons) if reasons else "설비 기준 미달 항목이 존재합니다."
        else:
            if breaker_na or cable_na or thermal_na:
                equipment_status = "NEED_MORE"
                equipment_final_line = "최종 결론(설비 기준): 조건 미충족(추가 입력 필요)"
                need = []
                if breaker_na:
                    need.append("차단기/단락 입력")
                if cable_na:
                    need.append("케이블 조건")
                if thermal_na:
                    need.append("t_clear 및 케이블 단면적(S)")
                equipment_final_sub = "추가 입력 후 재평가가 필요합니다: " + (", ".join(need) if need else "-")
            else:
                equipment_status = "PASS"
                equipment_final_line = "최종 결론(설비 기준): 적합"
                equipment_final_sub = "차단기/케이블/열상승 항목이 기준을 충족합니다."

        self.final_line.setText(equipment_final_line)
        self.final_sub.setText(equipment_final_sub)

        # --------------------------
        # 요약 카드
        # --------------------------
        In_txt = self._fmt_a(In_A)
        Isc_txt = self._fmt_ka_from_a(Isc_A)

        pm_txt = "-"
        if protection_ratio is not None:
            try:
                pm = float(protection_ratio)
                pm_txt = f"{pm:.2f}" + (" (⚠ 부족)" if pm < 1.0 else "")
            except Exception:
                pm_txt = "-"

        cable_line = f"케이블 판정(30℃ 기준): {hard_status}"
        if hard_status == "계산 불가":
            cable_line += " (입력 누락으로 계산 불가)"
        elif hard_status == "부적합":
            cable_line += " (계산 결과 기준 미달)"
        else:
            cable_line += " (기준 만족)"

        thermal_line = f"열상승 판정: {thermal_status}"
        if thermal_status == "계산 불가":
            thermal_line += " (t_clear 또는 케이블 단면적(S) 미확정)"
        elif thermal_status == "부적합":
            thermal_line += " (단락열 기준 미달)"
        else:
            thermal_line += " (기준 만족)"

        self.lb_summary.setText(
            f"정격전류(In): {In_txt}\n"
            f"단락전류(Isc): {Isc_txt}\n"
            f"보호 여유율(Icu/Isc): {pm_txt}\n\n"
            f"{cable_line}\n"
            f"{thermal_line}"
        )

        self.lb_breaker.setText(f"차단기 판정: {breaker_result}\n{breaker_reason}")

        # --------------------------
        # 상세 분석 페이지로 넘길 results
        # --------------------------
        self._last_results = {
            "dt": dt,
            "limit_current": I_load,   # 간이(필요하면 '설계전류' 입력값으로 교체)
            "Isc_A": Isc_A,
            "In_A": In_A,
            "breaker_result": breaker_result,
            "protection_ratio": protection_ratio,
            "equipment_status": equipment_status,
            "equipment_final_line": equipment_final_line,
            "equipment_final_sub": equipment_final_sub,
            "cable_hard": cable_hard,
            "cable_op": cable_op,
            "thermal": thermal,
        }
