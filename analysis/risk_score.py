# analysis/risk_score.py
def calculate_operation_risk(
    evt_prob: float,
    max_duration: float,
    duration_limit: float,
    tcc_margin,
    breaker_ok: bool,
    hard_status,
    is_demo: bool = False,
):
    """
    반환:
      evt_score / time_score / protection_score / total / protection_note
    정책:
      - DEMO면 total=None로 두고 정량평가 비활성(그래프 UI 확인용)
      - 보호(TCC) 점수는 (설비 PASS) + (차단기 적합) + (tcc_margin 계산 가능)일 때만 반영
      - hard_status는 코드값(PASS/FAIL/NEED_MORE) 또는 텍스트(적합/부적합)를 모두 허용
    """
    def _clamp(x, lo, hi):
        return max(lo, min(hi, x))

    def _hard_is_pass(x):
        if x is None:
            return False
        s = str(x).strip().upper()
        if s == "PASS":
            return True
        if s in ("적합", "규정 충족"):
            return True
        return False

    evt_p = 0.0
    try:
        evt_p = float(evt_prob)
    except Exception:
        evt_p = 0.0
    evt_p = _clamp(evt_p, 0.0, 1.0)

    evt_score = _clamp(evt_p * 40.0, 0.0, 40.0)

    dur = 0.0
    try:
        dur = float(max_duration)
    except Exception:
        dur = 0.0
    lim = 1.0
    try:
        lim = float(duration_limit)
        if lim <= 0:
            lim = 1.0
    except Exception:
        lim = 1.0

    time_ratio = _clamp(dur / lim, 0.0, 1.0)
    time_score = time_ratio * 40.0

    protection_score = None
    protection_note = ""

    hard_pass = _hard_is_pass(hard_status)

    if not hard_pass:
        protection_score = None
        protection_note = "설비 PASS가 아니므로 보호(TCC) 점수는 반영하지 않음"
    elif not bool(breaker_ok):
        protection_score = None
        protection_note = "차단기 적합이 아니므로 보호(TCC) 점수는 반영하지 않음"
    else:
        try:
            if tcc_margin is None:
                raise ValueError("tcc_margin None")
            m = float(tcc_margin)
            protection_score = _clamp(m * 20.0, 0.0, 20.0)
            protection_note = "TCC 여유 기반 점수 반영"
        except Exception:
            protection_score = None
            protection_note = "TCC 계산 불가로 보호(TCC) 점수 N/A"

    if is_demo:
        total = None
    else:
        total_raw = evt_score + time_score + (protection_score if protection_score is not None else 0.0)
        total = _clamp(total_raw, 0.0, 100.0)

    return {
        "evt_score": float(evt_score),
        "time_score": float(time_score),
        "protection_score": (None if protection_score is None else float(protection_score)),
        "total": total,
        "protection_note": protection_note,
    }


def operation_risk_level(total_score):
    if total_score is None:
        return "참고(비활성)"
    try:
        s = float(total_score)
    except Exception:
        return "알 수 없음"
    if s >= 80:
        return "매우 높음"
    if s >= 60:
        return "높음"
    if s >= 40:
        return "보통"
    return "낮음"
