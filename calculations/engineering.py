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


# ============================================================
# 케이블 기준 테이블(프로파일 기반)
# - 단위: (단면적 mm², 기준 허용전류 A)
# - 기준조건 가정(샘플): 30℃, XLPE 90℃, 공기중/트레이 계열
# ============================================================
def cable_table_base(profile: str = "IEC_CONSERVATIVE"):
    """
    profile
      - IEC_CONSERVATIVE : 보수(다심/보수조건 느낌. 값 낮음)
      - IEC_REALISTIC_1C : 현실(단심 1C 공기중/트레이 flat formation 느낌. 값 큼)

    주의:
      - 이 테이블은 '기준값'이고, 실제 평가는 보정계수로 조정한다.
    """
    p = str(profile).upper().strip()

    if p == "IEC_REALISTIC_1C":
        return [
            (25, 190),
            (35, 235),
            (50, 285),
            (70, 355),
            (95, 430),
            (120, 490),
            (150, 560),
            (185, 640),
            (240, 780),
            (300, 900),
            (400, 1080),
            (500, 1250),
            (630, 1450),
        ]

    return [
        (25, 130),
        (35, 160),
        (50, 195),
        (70, 245),
        (95, 300),
        (120, 345),
        (150, 400),
        (185, 455),
        (240, 540),
        (300, 630),
        (400, 750),
        (500, 860),
        (630, 1000),
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
    """
    30℃ 기준의 간이 온도 보정(형님 버전 유지)
    - 30℃ 이하: 1.0
    - 30℃ 초과: 1%/℃ 감소, 하한 0.70
    """
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
    """
    table 우선.
    table이 None이면 table_profile 우선.
    table_profile도 None이면:
      - IEC: IEC_CONSERVATIVE
      - KESC: IEC_CONSERVATIVE (기본은 보수로 동일 적용)
    """
    if table is not None:
        return table, (table_profile or "CUSTOM")

    prof = table_profile
    if prof is None:
        st = str(standard).upper()
        prof = "IEC_CONSERVATIVE" if st in ("IEC", "KESC") else "IEC_CONSERVATIVE"

    return cable_table_base(profile=prof), prof


def cable_allowable_current_adv(
    I_load,
    material,
    insulation,
    install,
    ambient,
    parallel,
    mode="AUTO",                # "AUTO" or "MANUAL"
    section_mm2_input=None,     # MANUAL일 때 사용
    table=None,
    standard="KESC",
    table_profile=None          # "IEC_CONSERVATIVE"/"IEC_REALISTIC_1C"
):
    """
    status:
      - '계산 불가' : 입력 누락으로 계산 불가
      - '부적합'   : 계산 결과 기준 미달
      - '적합'     : 기준 만족

    반환 키:
      status, section_mm2_used, parallel, I_allow_total, I_allow_single, k_temp, table_profile_used, reason
    """
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
            "reason": f"입력 누락으로 계산 불가: {', '.join(missing)} 미입력",
        }

    try:
        I_load = float(I_load)
        ambient = float(ambient)
        parallel = int(parallel)
    except Exception:
        return {
            "status": "계산 불가",
            "section_mm2_used": None,
            "parallel": None,
            "I_allow_total": None,
            "I_allow_single": None,
            "k_temp": None,
            "table_profile_used": None,
            "reason": "입력 형식 오류로 계산 불가(부하전류/주위온도/병렬 케이블 수)",
        }

    if parallel <= 0:
        parallel = 1

    table_used, profile_used = _resolve_table(table, table_profile, standard)

    k_mat, k_ins, k_inst, k_temp, k_group = _correction_factors(
        material, insulation, install, ambient, parallel
    )

    # -------- MANUAL --------
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
                "reason": "단면적(S)은 0보다 커야 합니다.",
            }

        # 테이블에서 가장 가까운 상위(mm2) 허용전류를 기준값으로 사용(간이)
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

        if I_load <= total_allow:
            status = "적합"
            reason = (
                "수동 입력 모드(자동선정 OFF): 입력 단면적(S) 기준으로 허용전류 ≥ 부하전류\n"
                f"- S(입력)={S_in:.0f}mm² / 테이블환산={mm2_for_base}mm² ({profile_used})\n"
                f"- 병렬 {parallel} × 집합계수 {k_group:.2f}\n"
                f"- 온도보정 k_temp={k_temp:.3f}\n"
                f"- 총 허용전류: {total_allow:.0f} A, 부하전류: {I_load:.0f} A"
            )
        else:
            status = "부적합"
            reason = (
                "수동 입력 모드(자동선정 OFF): 계산 결과 기준 미달(부하전류 과다)\n"
                f"- S(입력)={S_in:.0f}mm² / 테이블환산={mm2_for_base}mm² ({profile_used})\n"
                f"- 병렬 {parallel} × 집합계수 {k_group:.2f}\n"
                f"- 온도보정 k_temp={k_temp:.3f}\n"
                f"- 총 허용전류: {total_allow:.0f} A, 부하전류: {I_load:.0f} A"
            )

        return {
            "status": status,
            "section_mm2_used": float(S_in),
            "parallel": parallel,
            "I_allow_total": float(total_allow),
            "I_allow_single": float(single_allow),
            "k_temp": float(k_temp),
            "table_profile_used": profile_used,
            "reason": reason,
        }

    # -------- AUTO --------
    chosen_S = None
    chosen_single = None
    chosen_total = None

    for mm2, base_allow in sorted(table_used, key=lambda x: x[0]):
        single_allow = base_allow * k_mat * k_ins * k_inst * k_temp
        total_allow = single_allow * parallel * k_group
        if I_load <= total_allow:
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
            "reason": (
                "자동선정 모드: 계산 결과 기준 미달(부하전류 과다)\n"
                f"- 최대 후보: {max_mm2}mm² ({profile_used})\n"
                f"- 병렬 {parallel} × 집합계수 {k_group:.2f}\n"
                f"- 온도보정 k_temp={k_temp:.3f}\n"
                f"- 총 허용전류: {max_total:.0f} A, 부하전류: {I_load:.0f} A"
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
        "reason": (
            "자동선정 모드: 계산 결과 기준 만족(적합)\n"
            f"- 선정 S: {chosen_S}mm² ({profile_used})\n"
            f"- 병렬 {parallel} × 집합계수 {k_group:.2f}\n"
            f"- 온도보정 k_temp={k_temp:.3f}\n"
            f"- 총 허용전류: {chosen_total:.0f} A, 부하전류: {I_load:.0f} A"
        ),
    }


def thermal_adiabatic_check(I_sc_A, t_clear_s, section_mm2_used, material, insulation, standard):
    """
    단열(adiabatic) 열적 검토:
      I * sqrt(t) <= k * S

    t_clear 정책: 사용자 입력값(t_clear_s)만 사용
    """
    if t_clear_s is None:
        return {"status": "계산 불가", "reason": "입력 누락으로 계산 불가: t_clear 미입력", "detail": None}

    if section_mm2_used is None:
        return {"status": "계산 불가", "reason": "입력 누락으로 계산 불가: 최종 케이블 단면적(S) 미확정", "detail": None}

    try:
        I_sc_A = float(I_sc_A)
        t = float(t_clear_s)
        S = float(section_mm2_used)
    except Exception:
        return {"status": "계산 불가", "reason": "입력 형식 오류로 계산 불가(Isc/t_clear/S)", "detail": None}

    if t <= 0:
        return {"status": "계산 불가", "reason": "t_clear는 0보다 커야 합니다.", "detail": None}
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
    return {
        "status": status,
        "reason": (
            "단열(adiabatic) 열적 검토 결과\n"
            f"- I·√t = {lhs:,.0f}\n"
            f"- k·S = {rhs:,.0f}  (k={k}, S={S:.0f}mm²)\n"
            f"- t_clear(사용자입력) = {t:.3f}s"
        ),
        "detail": {"lhs": lhs, "rhs": rhs, "k": k, "S": S, "t_clear": t},
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
    table_profile=None
):
    """
    정답 구조 고정:
    - 설비 판정(Hard)        : 기준 온도(30℃) 고정
    - 운영 조건 보정(Optional): 기상/운영 온도로 허용전류 재평가
    """
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
    )

    op = {
        "status": "정상" if op_raw["status"] == "적합" else ("주의/부족" if op_raw["status"] == "부적합" else "평가 불가"),
        "ambient": ambient_op,
        "k_temp": op_raw.get("k_temp"),
        "I_allow_total": op_raw.get("I_allow_total"),
        "I_allow_single": op_raw.get("I_allow_single"),
        "table_profile_used": op_raw.get("table_profile_used"),
        "reason": op_raw.get("reason"),
    }
    return hard, op
