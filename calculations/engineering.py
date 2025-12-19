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
    margin = 1.1 if standard == "IEC" else 1.0
    return "적합" if breaker_A >= I_sc_A * margin else "부적합"


def cable_table_base():
    # 임시(샘플) 테이블: 단일 케이블/단일 회로 기준
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


def _correction_factors(material, insulation, install, ambient, parallel):
    k_mat = 1.0 if material == "Cu" else 0.8
    k_ins = 1.0 if insulation == "XLPE" else 0.9

    if install == "트레이":
        k_inst = 1.0
    elif install == "덕트":
        k_inst = 0.85
    else:
        k_inst = 0.75

    if ambient <= 30:
        k_temp = 1.0
    else:
        k_temp = max(0.7, 1.0 - 0.01 * (ambient - 30.0))

    k_group = _group_factor(parallel)
    return k_mat, k_ins, k_inst, k_temp, k_group


def cable_allowable_current_adv(
    I_load,
    material,
    insulation,
    install,
    ambient,
    parallel,
    mode="AUTO",                # "AUTO" or "MANUAL"
    section_mm2_input=None,     # MANUAL일 때 사용
    table=None
):
    """
    status:
      - '계산 불가' : 입력 누락으로 계산 불가
      - '부적합'   : 계산 결과 기준 미달
      - '적합'     : 기준 만족

    핵심:
      - 열상승 계산에 사용할 S는 'section_mm2_used'로 단일화해서 반환
      - AUTO: 테이블에서 최소 적합 S를 자동 선택
      - MANUAL: 사용자가 준 S를 최종 S로 고정(자동선정 OFF)
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
            "reason": "입력 형식 오류로 계산 불가(부하전류/주위온도/병렬 케이블 수)",
        }

    if parallel <= 0:
        parallel = 1

    if table is None:
        table = cable_table_base()

    k_mat, k_ins, k_inst, k_temp, k_group = _correction_factors(
        material, insulation, install, ambient, parallel
    )

    # -------- MANUAL 모드 --------
    if str(mode).upper() == "MANUAL":
        if section_mm2_input is None:
            return {
                "status": "계산 불가",
                "section_mm2_used": None,
                "parallel": parallel,
                "I_allow_total": None,
                "I_allow_single": None,
                "reason": "수동 입력 모드인데 단면적(S) 미입력으로 계산 불가",
            }
        try:
            S = float(section_mm2_input)
        except Exception:
            return {
                "status": "계산 불가",
                "section_mm2_used": None,
                "parallel": parallel,
                "I_allow_total": None,
                "I_allow_single": None,
                "reason": "단면적(S) 형식 오류로 계산 불가",
            }
        if S <= 0:
            return {
                "status": "계산 불가",
                "section_mm2_used": None,
                "parallel": parallel,
                "I_allow_total": None,
                "I_allow_single": None,
                "reason": "단면적(S)은 0보다 커야 합니다.",
            }

        # 테이블에서 가장 가까운 상위 단면을 허용전류 기준으로 사용(간이)
        table_sorted = sorted(table, key=lambda x: x[0])
        base_allow = None
        for mm2, allow in table_sorted:
            if S <= mm2:
                base_allow = allow
                break
        if base_allow is None:
            # 입력 S가 테이블 최대보다 크면 최대값 사용(간이)
            base_allow = table_sorted[-1][1]

        single_allow = base_allow * k_mat * k_ins * k_inst * k_temp
        total_allow = single_allow * parallel * k_group

        if I_load <= total_allow:
            status = "적합"
            reason = (
                "수동 입력 모드(자동선정 OFF): 입력 단면적(S) 기준으로 허용전류 ≥ 부하전류\n"
                f"- S={S:.0f}mm²(테이블 환산 기준), 병렬 {parallel} × 집합계수 {k_group:.2f}\n"
                f"- 총 허용전류: {total_allow:.0f} A, 부하전류: {I_load:.0f} A"
            )
        else:
            status = "부적합"
            reason = (
                "수동 입력 모드(자동선정 OFF): 계산 결과 기준 미달(부하전류 과다)\n"
                f"- S={S:.0f}mm²(테이블 환산 기준), 병렬 {parallel} × 집합계수 {k_group:.2f}\n"
                f"- 총 허용전류: {total_allow:.0f} A, 부하전류: {I_load:.0f} A"
            )

        return {
            "status": status,
            "section_mm2_used": float(S),
            "parallel": parallel,
            "I_allow_total": float(total_allow),
            "I_allow_single": float(single_allow),
            "reason": reason,
        }

    # -------- AUTO 모드 --------
    chosen_S = None
    chosen_single = None
    chosen_total = None

    for mm2, base_allow in sorted(table, key=lambda x: x[0]):
        single_allow = base_allow * k_mat * k_ins * k_inst * k_temp
        total_allow = single_allow * parallel * k_group
        if I_load <= total_allow:
            chosen_S = mm2
            chosen_single = float(single_allow)
            chosen_total = float(total_allow)
            break

    if chosen_S is None:
        max_mm2, max_base = sorted(table, key=lambda x: x[0])[-1]
        max_single = max_base * k_mat * k_ins * k_inst * k_temp
        max_total = max_single * parallel * k_group
        return {
            "status": "부적합",
            "section_mm2_used": float(max_mm2),
            "parallel": parallel,
            "I_allow_total": float(max_total),
            "I_allow_single": float(max_single),
            "reason": (
                "자동선정 모드: 계산 결과 기준 미달(부하전류 과다)\n"
                f"- 최대 후보: {max_mm2}mm²\n"
                f"- 병렬 {parallel} × 집합계수 {k_group:.2f}\n"
                f"- 총 허용전류: {max_total:.0f} A, 부하전류: {I_load:.0f} A"
            ),
        }

    return {
        "status": "적합",
        "section_mm2_used": float(chosen_S),
        "parallel": parallel,
        "I_allow_total": float(chosen_total),
        "I_allow_single": float(chosen_single),
        "reason": (
            "자동선정 모드: 계산 결과 기준 만족(적합)\n"
            f"- 선정 S: {chosen_S}mm²\n"
            f"- 병렬 {parallel} × 집합계수 {k_group:.2f}\n"
            f"- 총 허용전류: {chosen_total:.0f} A, 부하전류: {I_load:.0f} A"
        ),
    }


def thermal_adiabatic_check(I_sc_A, t_clear_s, section_mm2_used, material, insulation, standard):
    """
    단열(adiabatic) 열적 검토:
      I * sqrt(t) <= k * S

    t_clear 정책: 사용자 입력값(t_clear_s)만 사용 (TCC 예상 차단시간은 참고용)
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
