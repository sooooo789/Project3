from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox,
    QScrollArea, QHBoxLayout
)

from calculations.engineering import (
    rated_current,
    short_circuit_current,
    breaker_judgement,
    cable_allowable_current_adv,
    thermal_adiabatic_check,
)
from ui.components.result_card import ResultCard


class ResultWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(10)

        nav = QWidget()
        nav_l = QHBoxLayout(nav)
        nav_l.setContentsMargins(0, 0, 0, 0)
        nav_l.setSpacing(10)

        self.btn_home = QPushButton("← 홈")
        self.btn_home.clicked.connect(self.go_home)

        self.btn_input = QPushButton("기본 입력")
        self.btn_input.clicked.connect(self.go_input)

        self.btn_cable = QPushButton("케이블 입력")
        self.btn_cable.clicked.connect(self.go_cable)

        self.btn_detail = QPushButton("운전 위험도(상세) →")
        self.btn_detail.clicked.connect(self.go_detail)

        nav_l.addWidget(self.btn_home)
        nav_l.addWidget(self.btn_input)
        nav_l.addWidget(self.btn_cable)
        nav_l.addStretch(1)
        nav_l.addWidget(self.btn_detail)
        outer.addWidget(nav)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        outer.addWidget(self.scroll)

        body = QWidget()
        self.scroll.setWidget(body)

        root = QVBoxLayout(body)
        root.setContentsMargins(30, 20, 30, 30)
        root.setSpacing(12)

        header = QLabel("결과 페이지 (설비 판정)")
        header.setStyleSheet("font-weight:900; font-size:18px;")
        root.addWidget(header)

        self.final_card = ResultCard("최종 결론")
        self.final_line = QLabel("")
        self.final_line.setWordWrap(True)
        self.final_line.setStyleSheet("font-weight:900; font-size:16px;")
        self.final_sub = QLabel("")
        self.final_sub.setWordWrap(True)
        self.final_sub.setStyleSheet("color:#374151;")
        self.final_card.add_widget(self.final_line)
        self.final_card.add_widget(self.final_sub)
        root.addWidget(self.final_card)

        self.sum_card = ResultCard("핵심 수치 요약")
        self.sum_text = QLabel("")
        self.sum_text.setWordWrap(True)
        self.sum_card.add_widget(self.sum_text)
        root.addWidget(self.sum_card)

        self.judge_card = ResultCard("설비 판정 근거")
        self.judge_text = QLabel("")
        self.judge_text.setWordWrap(True)
        self.judge_text.setStyleSheet("color:#374151;")
        self.judge_card.add_widget(self.judge_text)
        root.addWidget(self.judge_card)

        self.latest_data = None
        self.latest_results = None

    @staticmethod
    def _fmt_ka_a(I_A: float) -> str:
        return f"{I_A/1000.0:,.1f} kA ({I_A:,.0f} A)"

    def run_calculation(self, data):
        self.latest_data = data

        try:
            In_A = rated_current(data["V"], data["S"])
            Isc_A = short_circuit_current(data["V"], data["S"], data["Z"])
        except Exception as e:
            QMessageBox.critical(self, "계산 오류", f"전류 계산 중 오류:\n{e}")
            self._set_fail("최종 결론: 설비 판정 불가", "입력값/조건 확인 후 재시도 필요")
            self.latest_results = None
            return

        breaker_result = breaker_judgement(Isc_A, data["breaker"], data["standard"])

        Icu_kA = float(data["breaker"])
        Isc_kA = float(Isc_A / 1000.0)
        protection_ratio = (Icu_kA / Isc_kA) if Isc_kA > 0 else 0.0

        # ----------------------------
        # 케이블 판정: AUTO/MANUAL 정책 적용
        # ----------------------------
        cable_j = cable_allowable_current_adv(
            I_load=float(data["I_load"]),
            material=data.get("cable_material"),
            insulation=data.get("cable_insulation"),
            install=data.get("cable_install"),
            ambient=data.get("cable_ambient"),
            parallel=data.get("cable_parallel"),
            mode=data.get("cable_mode", "AUTO"),
            section_mm2_input=data.get("cable_section_mm2_input"),
        )
        cable_status = cable_j["status"]
        section_used = cable_j.get("section_mm2_used")

        # ----------------------------
        # 열상승(t_clear 정책 고정)
        # t_clear = 사용자 입력값만 사용
        # ----------------------------
        thermal_j = thermal_adiabatic_check(
            I_sc_A=Isc_A,
            t_clear_s=data.get("t_clear"),
            section_mm2_used=section_used,
            material=data.get("cable_material"),
            insulation=data.get("cable_insulation"),
            standard=data.get("standard"),
        )
        thermal_status = thermal_j["status"]

        # ----------------------------
        # 설비 판정(Hard)
        # ----------------------------
        if breaker_result != "적합":
            equipment_status = "부적합"
            final_line = "최종 결론: 설비 기준 미충족으로 사용 불가"
            final_sub = "차단기 차단용량(Icu)이 단락전류(Isc)를 만족하지 않아 기준 미달입니다."

        elif cable_status == "부적합":
            equipment_status = "부적합"
            final_line = "최종 결론: 설비 기준 미충족으로 사용 불가"
            final_sub = "케이블 허용전류가 부하전류를 만족하지 않아 기준 미달입니다."

        elif thermal_status == "부적합":
            equipment_status = "부적합"
            final_line = "최종 결론: 설비 기준 미충족으로 사용 불가"
            final_sub = "열적(단열) 검토에서 기준을 초과하여 기준 미달입니다."

        elif cable_status == "계산 불가" or thermal_status == "계산 불가":
            equipment_status = "조건 미충족"
            final_line = "최종 결론: 설비 판정 조건 미충족"
            final_sub = "케이블/열상승 판정에 필요한 입력 후 재평가가 필요합니다."

        else:
            equipment_status = "적합"
            final_line = "최종 결론: 설비 기준 적합"
            final_sub = "운전 위험도 평가는 설비 판정과 독립적인 참고 지표입니다."

        self.final_line.setText(final_line)
        self.final_sub.setText(final_sub)

        sum_lines = [
            f"정격전류(In): {In_A:,.0f} A",
            f"단락전류(Isc): {self._fmt_ka_a(Isc_A)}",
            f"차단기 Icu: {Icu_kA:,.1f} kA",
            f"보호 여유율(Icu/Isc): {protection_ratio:.2f}" + (" (⚠ 부족)" if protection_ratio < 1.0 else ""),
            f"케이블 판정: {cable_status}",
            f"열상승 판정: {thermal_status}",
        ]
        if section_used is not None:
            sum_lines.append(f"최종 케이블 단면적(S): {float(section_used):.0f} mm²")

        self.sum_text.setText("\n".join(sum_lines))

        judge_lines = []
        judge_lines.append(
            f"차단기 판정: {breaker_result} "
            f"(Icu {Icu_kA:,.1f} kA, Isc {Isc_kA:,.1f} kA)"
        )

        judge_lines.append(f"케이블 판정: {cable_status}\n- {cable_j['reason']}")
        judge_lines.append(f"열상승 판정: {thermal_status}\n- {thermal_j['reason']}")

        # t_clear 정책 문구 고정
        judge_lines.append("t_clear 정책: 열상승(단열식) 계산은 사용자 입력 t_clear만 사용합니다. (TCC 예상 차단시간은 참고용)")

        self.judge_text.setText("\n\n".join(judge_lines))

        # 상세 페이지로 넘길 results
        self.latest_results = {
            "equipment_status": equipment_status,
            "equipment_final_line": final_line,
            "equipment_final_sub": final_sub,

            "breaker_result": breaker_result,
            "Isc_A": float(Isc_A),
            "limit_current": float(data["I_load"]),

            "Icu_kA": float(Icu_kA),
            "Isc_kA": float(Isc_kA),

            "breaker_pickup": float(max(float(data["I_load"]) * 1.2, 1.0)),
            "breaker_tms": 0.3,

            "dt": float(data.get("dt", 1.0)) if float(data.get("dt", 1.0)) > 0 else 1.0,

            "cable_status": cable_status,
            "cable_section_mm2_used": section_used,

            "thermal_status": thermal_status,
            "t_clear_used": data.get("t_clear"),  # 정책상 이게 항상 사용됨
        }

    def _set_fail(self, line, sub):
        self.final_line.setText(line)
        self.final_sub.setText(sub)
        self.sum_text.setText("")
        self.judge_text.setText("")

    def go_detail(self):
        if self.latest_data is None or self.latest_results is None:
            QMessageBox.information(self, "안내", "먼저 계산을 실행하십시오.")
            return
        self.parent.detail_page.load_data(self.latest_data, self.latest_results)
        self.parent.setCurrentWidget(self.parent.detail_page)

    def go_home(self):
        self.parent.setCurrentWidget(self.parent.home_page)

    def go_input(self):
        self.parent.setCurrentWidget(self.parent.input_page)

    def go_cable(self):
        self.parent.setCurrentWidget(self.parent.cable_page)
