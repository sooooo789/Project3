# calculations/engineering.py

import math
import re


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
    """
    임시(샘플) 허용전류 테이블 (단일 케이블/단일 회로 기준)

    주의:
    - 실제 허용전류는 케이블 구조(심수), 설치방법, 주위온도, 토양열저항, 집합/다회선,
      도체 허용온도, 표준(KESC/IEC) 및 제조사 카탈로그에 따라 크게 달라집니다.
    - 면접/포트폴리오에서는 '테이블이 외부 주입/교체 가능'한 구조가 중요합니다.
    - 형님 프로젝트에서는 여기 값을 “정확값”으로 주장하지 말고 “예시/임시”로 표기하는 게 안전합니다.

    아래 값은 '너무 작은 단면에서 끊기는 문제'를 막기 위해 범위를 넓힌 것입니다.
    """
    return [
        ("25mm²", 110),
        ("35mm²", 135),
        ("50mm²", 170),
        ("70mm²", 215),
        ("95mm²", 260),
        ("120mm²", 300),
        ("150mm²", 340),
        ("185mm²", 385),
        ("240mm²", 450),
        ("300mm²", 520),
        ("400mm²", 610),
        ("500mm²", 690),
        ("630mm²", 800),
    ]


def _group_factor(parallel: int) -> float:
    """
    병렬 회로(동일 경로 집합) 보정계수(간이)
    - parallel은 '병렬 케이블 수(회선 수)'로 해석
    - 실제 집합계수는 배치/간격/수에 따라 표로 교체 권장
    """
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


def cable_allowable_current_adv(I_load, material, insulation, install, ambient, parallel, table=None):
    """
    케이블 허용전류 판정(입력 누락/기준미달/적합 3단계)

    status:
      - '계산 불가' : 입력 누락으로 계산 자체가 불가
      - '부적합'   : 계산은 되었으나 기준 미달(성능 부족)
      - '적합'     : 계산 및 기준 만족

    반환 reason은 '왜 그런지'가 한 줄 이상으로 드러나게 구성
    """

    # 1) 입력 누락(계산 불가)
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
            "cable": None,
            "I_allow_total": None,
            "I_allow_single": None,
            "parallel": None,
            "reason": f"입력 누락으로 계산 불가: {', '.join(missing)} 미입력",
        }

    # 2) 타입 파싱
    try:
        I_load = float(I_load)
        ambient = float(ambient)
        parallel = int(parallel)
    except Exception:
        return {
            "status": "계산 불가",
            "cable": None,
            "I_allow_total": None,
            "I_allow_single": None,
            "parallel": None,
            "reason": "입력 형식 오류로 계산 불가(부하전류/주위온도/병렬 케이블 수)",
        }

    if parallel <= 0:
        parallel = 1

    # 3) 보정계수(간이)
    k_mat = 1.0 if material == "Cu" else 0.8
    k_ins = 1.0 if insulation == "XLPE" else 0.9

    if install == "트레이":
        k_inst = 1.0
    elif install == "덕트":
        k_inst = 0.85
    else:  # 매설
        k_inst = 0.75

    # 30°C 기준, 초과 시 감쇠(간이)
    if ambient <= 30:
        k_temp = 1.0
    else:
        k_temp = max(0.7, 1.0 - 0.01 * (ambient - 30.0))

    k_group = _group_factor(parallel)

    # 테이블 주입 가능
    if table is None:
        table = cable_table_base()

    # 4) 최소 단면부터 선택(만족하는 최소 케이블)
    chosen = None
    chosen_single = None
    chosen_total = None

    for name, base_allow in table:
        single_allow = base_allow * k_mat * k_ins * k_inst * k_temp
        total_allow = single_allow * parallel * k_group
        if I_load <= total_allow:
            chosen = name
            chosen_single = float(single_allow)
            chosen_total = float(total_allow)
            break

    # 5) 만족 못 하면 '부적합' 확정(성능 부족)
    if chosen is None:
        max_name, max_base = table[-1]
        max_single = max_base * k_mat * k_ins * k_inst * k_temp
        max_total = max_single * parallel * k_group

        return {
            "status": "부적합",
            "cable": max_name,
            "I_allow_total": float(max_total),
            "I_allow_single": float(max_single),
            "parallel": parallel,
            "reason": (
                "계산 결과 기준 미달(부하전류 과다): 최대 후보 구성으로도 허용전류가 부족합니다.\n"
                f"- 최대 후보: {max_name}\n"
                f"- 단일 허용전류(보정): {max_single:.0f} A\n"
                f"- 병렬 {parallel} × 집합계수 {k_group:.2f} → 총 허용전류: {max_total:.0f} A\n"
                f"- 부하전류: {I_load:.0f} A"
            ),
        }

    return {
        "status": "적합",
        "cable": chosen,
        "I_allow_total": chosen_total,
        "I_allow_single": chosen_single,
        "parallel": parallel,
        "reason": (
            "계산 결과 기준 만족(적합): 허용전류 ≥ 부하전류\n"
            f"- 선정: {chosen}\n"
            f"- 단일 허용전류(보정): {chosen_single:.0f} A\n"
            f"- 병렬 {parallel} × 집합계수 {k_group:.2f} → 총 허용전류: {chosen_total:.0f} A\n"
            f"(재질 {material}, 절연 {insulation}, 설치 {install}, 온도 {ambient:.0f}°C)"
        ),
    }


def _parse_mm2(cable_name: str):
    if not cable_name:
        return None
    m = re.search(r"(\d+)\s*mm", str(cable_name))
    if not m:
        return None
    return float(m.group(1))

def thermal_adiabatic_check(I_sc_A, t_clear_s, section_mm2, material, insulation, standard):
    """
    단락 시 열적(단열) 검토 간이식:
      I * sqrt(t) <= k * S

    status:
      - '계산 불가' : 입력 누락/해석 불가로 계산 불가
      - '부적합'   : 계산 결과 기준 미달
      - '적합'     : 계산 결과 기준 만족
    """
    if t_clear_s is None:
        return {"status": "계산 불가", "reason": "입력 누락으로 계산 불가: t_clear 미입력", "detail": None}

    if section_mm2 is None:
        return {"status": "계산 불가", "reason": "입력 누락으로 계산 불가: 케이블 단면적(S) 미입력", "detail": None}

    try:
        I_sc_A = float(I_sc_A)
        t = float(t_clear_s)
        S = float(section_mm2)
    except Exception:
        return {"status": "계산 불가", "reason": "입력 형식 오류로 계산 불가(Isc/t_clear/S)", "detail": None}

    if t <= 0:
        return {"status": "계산 불가", "reason": "t_clear는 0보다 커야 합니다.", "detail": None}
    if S <= 0:
        return {"status": "계산 불가", "reason": "단면적(S)은 0보다 커야 합니다.", "detail": None}

    if material is None or insulation is None:
        return {"status": "계산 불가", "reason": "입력 누락으로 계산 불가: 케이블 재질/절연 정보 없음", "detail": None}

    # 참고용 k 값(필요 시 표준값으로 교체)
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
            f"- t_clear = {t:.3f}s"
        ),
        "detail": {"lhs": lhs, "rhs": rhs, "k": k, "S": S, "t_clear": t},
    }
