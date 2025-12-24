# calculations/engineering.py
import math


def rated_current(V_kV, S_kVA):
    V = V_kV * 1000.0
    return (S_kVA * 1000.0) / (math.sqrt(3) * V)


def short_circuit_current(V_kV, S_kVA, Z_percent):
    V = V_kV * 1000.0
    return (S_kVA * 1000.0) / (math.sqrt(3) * V) * (100.0 / Z_percent)


def breaker_judgement(I_sc_A, breaker_kA, standard):
    breaker_A = float(breaker_kA) * 1000.0
    margin = 1.1 if str(standard).upper() == "IEC" else 1.0
    return "적합" if breaker_A >= I_sc_A * margin else "부적합"


def cable_table_base(profile: str = "IEC_CONSERVATIVE"):
    p = str(profile).upper().strip()

    if p == "KESC_DEFAULT":
        return [
            (25, 110),
            (35, 135),
            (50, 170),
            (70, 215),
            (95, 260),
            (120, 300),
            (150, 340),
            (185, 385),
            (240, 450),
            (300, 520),
            (400, 610),
            (500, 690),
            (630, 800),
        ]

    if p == "IEC_REALISTIC_1C":
        return [
            (25, 190), (35, 235), (50, 285), (70, 355),
            (95, 430), (120, 490), (150, 560), (185, 640),
            (240, 780), (300, 900), (400, 1080), (500, 1250), (630, 1450),
        ]

    return [
        (25, 130), (35, 160), (50, 195), (70, 245),
        (95, 300), (120, 345), (150, 400), (185, 455),
        (240, 540), (300, 630), (400, 750), (500, 860), (630, 1000),
    ]


def _group_factor(parallel: int) -> float:
    if parallel <= 1:
        return 1.0
    if parallel == 2:
        return 0.90
    if parallel == 3:
        return 0.85
    if parallel == 4:
        return 0.80
    if parallel == 5:
        return 0.78
    if parallel == 6:
        return 0.76
    return 0.75


def _temp_factor_30_base(ambient_c: float) -> float:
    if ambient_c <= 30.0:
        return 1.0
    return max(0.7, 1.0 - 0.01 * (ambient_c - 30.0))


def _correction_factors(material, insulation, install, ambient, parallel):
    k_mat = 1.0 if material == "Cu" else 0.8
    k_ins = 1.0 if insulation == "XLPE" else 0.9

    if install == "트레이":
        k_inst = 1.0
    elif install == "덕트":
        k_inst = 0.85
    else:
        k_inst = 0.75

    k_temp = _temp_factor_30_base(float(ambient))
    k_group = _group_factor(parallel)
    return k_mat, k_ins, k_inst, k_temp, k_group


def _resolve_table(table, table_profile, standard):
    if table is not None:
        return table, (table_profile or "CUSTOM")

    st = str(standard).upper().strip()
    prof = (table_profile or "").upper().strip() if table_profile is not None else None

    # 1번 정책: KESC면 테이블 프로파일을 무조건 KESC_DEFAULT로 강제(IEC 혼입 원천 차단)
    if st == "KESC":
        prof = "KESC_DEFAULT"
    else:
        if not prof:
            prof = "IEC_CONSERVATIVE"

    return cable_table_base(profile=prof), prof


def cable_allowable_current_adv(
    I_load,
    material,
    insulation,
    install,
    ambient,
    parallel,
    mode="AUTO",
    section_mm2_input=None,
    table=None,
    standard="KESC",
    table_profile=None,
    design_margin=1.25,
):
    missing = []
    if material is None:
        missing.append("재질")
    if insulation is None:
        missing.append("절연")
    if install is None:
        missing.append("설치방법")
    if ambient is None:
        missing.append("주위온도")
    if parallel is None:
        missing.append("병렬 케이블 수")

    if missing:
        return {
            "status": "계산 불가",
            "section_mm2_used": None,
            "parallel": None,
            "I_allow_total": None,
            "I_allow_single": None,
            "k_temp": None,
            "table_profile_used": None,
            "design_margin_used": None,
            "I_design_A": None,
            "reason": f"입력 누락으로 계산 불가: {', '.join(missing)} 미입력",
        }

    try:
        I_load = float(I_load)
        ambient = float(ambient)
        parallel = int(parallel)
        dm = float(design_margin) if design_margin is not None else 1.25
    except Exception:
        return {
            "status": "계산 불가",
            "section_mm2_used": None,
            "parallel": None,
            "I_allow_total": None,
            "I_allow_single": None,
            "k_temp": None,
            "table_profile_used": None,
            "design_margin_used": None,
            "I_design_A": None,
            "reason": "입력 형식 오류로 계산 불가(I_load/ambient/parallel/design_margin)",
        }

    if parallel <= 0:
        parallel = 1
    if dm <= 0:
        dm = 1.25

    table_used, profile_used = _resolve_table(table, table_profile, standard)

    k_mat, k_ins, k_inst, k_temp, k_group = _correction_factors(
        material, insulation, install, ambient, parallel
    )

    I_design = I_load * dm

    if str(mode).upper() == "MANUAL":
        if section_mm2_input is None:
            return {
                "status": "계산 불가",
                "section_mm2_used": None,
                "parallel": parallel,
                "I_allow_total": None,
                "I_allow_single": None,
                "k_temp": float(k_temp),
                "table_profile_used": profile_used,
                "design_margin_used": float(dm),
                "I_design_A": float(I_design),
                "reason": "수동 입력 모드인데 단면적(S) 미입력으로 계산 불가",
            }
        try:
            S_in = float(section_mm2_input)
        except Exception:
            return {
                "status": "계산 불가",
                "section_mm2_used": None,
                "parallel": parallel,
                "I_allow_total": None,
                "I_allow_single": None,
                "k_temp": float(k_temp),
                "table_profile_used": profile_used,
                "design_margin_used": float(dm),
                "I_design_A": float(I_design),
                "reason": "단면적(S) 형식 오류로 계산 불가",
            }
        if S_in <= 0:
            return {
                "status": "계산 불가",
                "section_mm2_used": None,
                "parallel": parallel,
                "I_allow_total": None,
                "I_allow_single": None,
                "k_temp": float(k_temp),
                "table_profile_used": profile_used,
                "design_margin_used": float(dm),
                "I_design_A": float(I_design),
                "reason": "단면적(S)은 0보다 커야 합니다.",
            }

        table_sorted = sorted(table_used, key=lambda x: x[0])
        base_allow = None
        mm2_for_base = None
        for mm2, allow in table_sorted:
            if S_in <= mm2:
                mm2_for_base = mm2
                base_allow = allow
                break
        if base_allow is None:
            mm2_for_base = table_sorted[-1][0]
            base_allow = table_sorted[-1][1]

        single_allow = base_allow * k_mat * k_ins * k_inst * k_temp
        total_allow = single_allow * parallel * k_group

        ok = (I_design <= total_allow)
        status = "적합" if ok else "부적합"
        reason = (
            "수동 입력 모드(자동선정 OFF)\n"
            f"- 목표 설계전류 I_design = I_load×여유계수 = {I_load:.0f}×{dm:.2f} = {I_design:.0f} A\n"
            f"- S(입력)={S_in:.0f}mm² / 테이블환산={mm2_for_base}mm² ({profile_used})\n"
            f"- 병렬 {parallel} × 집합계수 {k_group:.2f}\n"
            f"- 온도보정 k_temp={k_temp:.3f}\n"
            f"- 총 허용전류: {total_allow:.0f} A"
        )

        return {
            "status": status,
            "section_mm2_used": float(S_in),
            "parallel": parallel,
            "I_allow_total": float(total_allow),
            "I_allow_single": float(single_allow),
            "k_temp": float(k_temp),
            "table_profile_used": profile_used,
            "design_margin_used": float(dm),
            "I_design_A": float(I_design),
            "reason": reason,
        }

    chosen_S = None
    chosen_single = None
    chosen_total = None

    for mm2, base_allow in sorted(table_used, key=lambda x: x[0]):
        single_allow = base_allow * k_mat * k_ins * k_inst * k_temp
        total_allow = single_allow * parallel * k_group
        if I_design <= total_allow:
            chosen_S = mm2
            chosen_single = float(single_allow)
            chosen_total = float(total_allow)
            break

    if chosen_S is None:
        max_mm2, max_base = sorted(table_used, key=lambda x: x[0])[-1]
        max_single = max_base * k_mat * k_ins * k_inst * k_temp
        max_total = max_single * parallel * k_group
        return {
            "status": "부적합",
            "section_mm2_used": float(max_mm2),
            "parallel": parallel,
            "I_allow_total": float(max_total),
            "I_allow_single": float(max_single),
            "k_temp": float(k_temp),
            "table_profile_used": profile_used,
            "design_margin_used": float(dm),
            "I_design_A": float(I_design),
            "reason": (
                "자동선정 모드: 설계여유계수 포함 기준 미달\n"
                f"- 목표 설계전류 I_design = {I_design:.0f} A (I_load {I_load:.0f}×{dm:.2f})\n"
                f"- 최대 후보: {max_mm2}mm² ({profile_used})\n"
                f"- 병렬 {parallel} × 집합계수 {k_group:.2f}\n"
                f"- 온도보정 k_temp={k_temp:.3f}\n"
                f"- 총 허용전류: {max_total:.0f} A"
            ),
        }

    return {
        "status": "적합",
        "section_mm2_used": float(chosen_S),
        "parallel": parallel,
        "I_allow_total": float(chosen_total),
        "I_allow_single": float(chosen_single),
        "k_temp": float(k_temp),
        "table_profile_used": profile_used,
        "design_margin_used": float(dm),
        "I_design_A": float(I_design),
        "reason": (
            "자동선정 모드: 설계여유계수 포함 기준 만족\n"
            f"- 목표 설계전류 I_design = {I_design:.0f} A (I_load {I_load:.0f}×{dm:.2f})\n"
            f"- 선정 S: {chosen_S}mm² ({profile_used})\n"
            f"- 병렬 {parallel} × 집합계수 {k_group:.2f}\n"
            f"- 온도보정 k_temp={k_temp:.3f}\n"
            f"- 총 허용전류: {chosen_total:.0f} A"
        ),
    }


def thermal_adiabatic_check(
    I_sc_A,
    t_clear_s,
    section_mm2_used,
    material,
    insulation,
    standard,
    t_clear_input=None,
    t_trip_est=None,
    t_clear_policy="NONE",
):
    if t_clear_s is None:
        return {"status": "계산 불가", "reason": "입력 누락으로 계산 불가: 차단시간(t_used) 미확정", "detail": None}

    if section_mm2_used is None:
        return {"status": "계산 불가", "reason": "입력 누락으로 계산 불가: 최종 케이블 단면적(S) 미확정", "detail": None}

    try:
        I_sc_A = float(I_sc_A)
        t = float(t_clear_s)
        S = float(section_mm2_used)
    except Exception:
        return {"status": "계산 불가", "reason": "입력 형식 오류로 계산 불가(Isc/t_used/S)", "detail": None}

    if t <= 0:
        return {"status": "계산 불가", "reason": "차단시간(t_used)은 0보다 커야 합니다.", "detail": None}
    if S <= 0:
        return {"status": "계산 불가", "reason": "단면적(S)은 0보다 커야 합니다.", "detail": None}

    if material is None or insulation is None:
        return {"status": "계산 불가", "reason": "입력 누락으로 계산 불가: 케이블 재질/절연 정보 없음", "detail": None}

    k_table = {
        ("Cu", "PVC"): 115.0,
        ("Cu", "XLPE"): 143.0,
        ("Al", "PVC"): 76.0,
        ("Al", "XLPE"): 94.0,
    }
    k = k_table.get((material, insulation))
    if k is None:
        return {"status": "계산 불가", "reason": "k 값 매핑 불가(재질/절연 조합)", "detail": None}

    lhs = I_sc_A * math.sqrt(t)
    rhs = k * S

    status = "적합" if lhs <= rhs else "부적합"

    input_txt = "-" if t_clear_input is None else f"{float(t_clear_input):.3f}s"
    tcc_txt = "-" if t_trip_est is None else f"{float(t_trip_est):.3f}s"

    return {
        "status": status,
        "reason": (
            "단열(adiabatic) 열적 검토 결과\n"
            f"- I·√t_used = {lhs:,.0f}\n"
            f"- k·S = {rhs:,.0f}  (k={k}, S={S:.0f}mm²)\n"
            f"- t_clear 입력 = {input_txt}\n"
            f"- TCC 추정 = {tcc_txt}\n"
            f"- t_used = {t:.3f}s ({t_clear_policy})"
        ),
        "detail": {"lhs": lhs, "rhs": rhs, "k": k, "S": S, "t_used": t, "t_clear_input": t_clear_input, "t_trip_est": t_trip_est},
    }


def cable_allowable_hard_op(
    I_load,
    material,
    insulation,
    install,
    parallel,
    mode="AUTO",
    section_mm2_input=None,
    ambient_op=None,
    standard="KESC",
    table_profile=None,
    design_margin=1.25,
):
    hard = cable_allowable_current_adv(
        I_load=I_load,
        material=material,
        insulation=insulation,
        install=install,
        ambient=30.0,
        parallel=parallel,
        mode=mode,
        section_mm2_input=section_mm2_input,
        standard=standard,
        table_profile=table_profile,
        design_margin=design_margin,
    )

    if ambient_op is None:
        op = {
            "status": "평가 불가",
            "reason": "운영 온도 데이터 없음(기상/수동 미확정)",
            "ambient": None,
            "k_temp": None,
            "I_allow_total": None,
            "I_allow_single": None,
            "table_profile_used": hard.get("table_profile_used"),
        }
        return hard, op

    try:
        ambient_op = float(ambient_op)
    except Exception:
        op = {
            "status": "평가 불가",
            "reason": "운영 온도 형식 오류",
            "ambient": None,
            "k_temp": None,
            "I_allow_total": None,
            "I_allow_single": None,
            "table_profile_used": hard.get("table_profile_used"),
        }
        return hard, op

    op_raw = cable_allowable_current_adv(
        I_load=I_load,
        material=material,
        insulation=insulation,
        install=install,
        ambient=ambient_op,
        parallel=parallel,
        mode=mode,
        section_mm2_input=section_mm2_input,
        standard=standard,
        table_profile=table_profile,
        design_margin=design_margin,
    )

    op = {
        "status": "규정 충족" if op_raw["status"] == "적합" else ("규정 미달" if op_raw["status"] == "부적합" else "평가 불가"),
        "ambient": ambient_op,
        "k_temp": op_raw.get("k_temp"),
        "I_allow_total": op_raw.get("I_allow_total"),
        "I_allow_single": op_raw.get("I_allow_single"),
        "table_profile_used": op_raw.get("table_profile_used"),
        "reason": op_raw.get("reason"),
    }
    return hard, op
