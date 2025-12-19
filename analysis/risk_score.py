# analysis/risk_score.py

def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


def calculate_operation_risk(
    evt_prob,
    max_duration,
    duration_limit,
    tcc_margin,
    breaker_ok,
    hard_status
):
    """
    위험도 점수(0~100)
    - 값이 높을수록 운전 리스크가 큼
    - 보호(TCC)는 '보호 부족 시'에만 위험 가중으로 반영 (0~20)
    """

    # ---------- EVT 위험(0~40): 확률이 높을수록 위험 증가 ----------
    try:
        p = float(evt_prob)
    except Exception:
        p = 0.0
    p = _clamp(p, 0.0, 1.0)
    evt_risk = 40.0 * p  # p=1이면 40점(최대 위험)

    # ---------- 지속시간 위험(0~40): 기준 초과할수록 위험 증가 ----------
    try:
        d = float(max_duration)
    except Exception:
        d = 0.0
    try:
        L = float(duration_limit)
    except Exception:
        L = 5.0
    if L <= 0:
        L = 5.0

    # d/L 비율 기반. 0이면 0점, L이면 40점, 2L 이상이면 40점(포화)
    ratio = _clamp(d / L, 0.0, 2.0)
    time_risk = 40.0 * _clamp(ratio / 1.0, 0.0, 1.0)

    # ---------- 보호(TCC) 위험(0~20): 보호 부족 시에만 위험 가중 ----------
    # 정책 고정:
    # - Hard 적합이 아니면 보호 위험 점수는 N/A (점수 제외)
    # - Icu 부적합이면 (breaker_ok=False) 보호 위험은 최대(20)
    # - TCC 평가 가능(tcc_margin 0~1)일 때: margin이 낮을수록 위험 증가
    protection_risk = None
    protection_note = ""

    if hard_status != "적합":
        protection_risk = None
        protection_note = "설비 판정이 '적합'으로 확정되지 않아 보호 위험 점수는 N/A(점수 제외) 처리"
    else:
        if breaker_ok is False:
            protection_risk = 20.0
            protection_note = "차단기 Icu 부적합 시 보호 부족으로 최대 위험 가중(20/20)"
        else:
            if tcc_margin is None:
                protection_risk = None
                protection_note = "TCC 파라미터/평가값 부족으로 보호 위험 점수는 N/A(점수 제외) 처리"
            else:
                try:
                    m = float(tcc_margin)
                except Exception:
                    m = None

                if m is None:
                    protection_risk = None
                    protection_note = "TCC 평가값 해석 불가로 보호 위험 점수는 N/A(점수 제외) 처리"
                else:
                    m = _clamp(m, 0.0, 1.0)
                    # m=1(여유 충분) -> 위험 0
                    # m=0(여유 없음) -> 위험 20
                    protection_risk = 20.0 * (1.0 - m)
                    protection_note = "보호 부족 시에만 위험 가중으로 반영(여유가 클수록 0에 수렴)"

    total = evt_risk + time_risk + (protection_risk if protection_risk is not None else 0.0)
    total = _clamp(total, 0.0, 100.0)

    note = (
        "본 점수는 위험도 점수로,\n"
        "값이 높을수록 운전 리스크가 큼을 의미합니다.\n"
        "보호(TCC) 점수는 보호 부족 시에만 위험 가중으로 반영됩니다."
    )

    return {
        "total": float(total),
        "evt_score": float(evt_risk),
        "time_score": float(time_risk),
        "protection_score": (None if protection_risk is None else float(protection_risk)),
        "protection_note": protection_note,
        "note": note,
    }


def operation_risk_level(score):
    """
    위험도 등급(표현은 예시. 필요하면 구간 바꾸면 됨)
    """
    try:
        s = float(score)
    except Exception:
        s = 0.0

    if s >= 80:
        return "매우 높음"
    if s >= 60:
        return "높음"
    if s >= 40:
        return "보통"
    if s >= 20:
        return "낮음"
    return "매우 낮음"
