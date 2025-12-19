# analysis/risk_score.py

def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


def operation_risk_level(total_score):
    s = float(total_score)
    if s >= 70:
        return "높음"
    if s >= 40:
        return "중간"
    return "낮음"


def calculate_operation_risk(
    evt_prob,
    max_duration,
    duration_limit,
    tcc_margin,
    breaker_ok,
    hard_status
):
    """
    운전 위험도(참고 지표)

    핵심 룰:
    - Hard Engineering이 '적합'이 아니면 보호(TCC) 점수는 N/A 처리
      (설비 판정 미확정 상태에서 보호 만점/0점이 뜨는 논리 뒤집힘 방지)

    protection_score:
      - Icu 부적합(breaker_ok=False) → 0점 (단, hard_status=='적합'인 경우에만 의미 있음)
      - hard_status!='적합' → N/A
      - tcc_margin None → N/A
      - 가능 → margin 낮을수록 점수↑ (0~20)

    총점:
      - 보호가 N/A면 EVT+시간(최대 80)을 100으로 환산
    """

    # EVT(0~40)
    evt_p = _clamp(float(evt_prob), 0.0, 1.0)
    evt_score = 40.0 * evt_p

    # 시간(0~40)
    dl = float(duration_limit) if float(duration_limit) > 0 else 1.0
    ratio = _clamp(float(max_duration) / dl, 0.0, 2.0)
    time_score = 40.0 * (ratio / 2.0)

    protection_score = None
    protection_note = ""

    # Hard 미확정이면 보호 점수는 N/A
    if hard_status != "적합":
        protection_score = None
        protection_note = "설비 판정 미확정(적합 아님) → 보호(TCC) 점수 N/A"
    else:
        if not breaker_ok:
            protection_score = 0.0
            protection_note = "Icu 부적합 → 보호(TCC) 점수 0점 처리"
        else:
            if tcc_margin is None:
                protection_score = None
                protection_note = "TCC 파라미터 부족 → 보호(TCC) 점수 N/A"
            else:
                m = _clamp(float(tcc_margin), 0.0, 1.0)
                protection_score = 20.0 * (1.0 - m)
                protection_note = "TCC 기반 점수(여유도 낮을수록 점수 증가)"

    if protection_score is None:
        total = (evt_score + time_score) / 80.0 * 100.0
        total = _clamp(total, 0.0, 100.0)
        return {
            "total": total,
            "evt_score": evt_score,
            "time_score": time_score,
            "protection_score": None,
            "protection_note": protection_note,
            "note": "보호 점수 N/A로 EVT+시간만 환산",
        }

    total = evt_score + time_score + protection_score
    total = _clamp(total, 0.0, 100.0)
    return {
        "total": total,
        "evt_score": evt_score,
        "time_score": time_score,
        "protection_score": protection_score,
        "protection_note": protection_note,
        "note": "",
    }
