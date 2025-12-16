# calc/thermal.py

def calc_thermal(
    load_current: float,
    allowable_current: float,
    peak_duration_hour: float | None = None,
):
    """
    load_current: 부하 전류 (A)
    allowable_current: 케이블 허용 전류 (A)
    peak_duration_hour: 피크 지속시간 (hour), 없으면 기본 판단
    """

    load_ratio = load_current / allowable_current

    # 기본 판정
    if load_ratio <= 0.8:
        status = "정상"
    elif load_ratio <= 1.0:
        status = "경고"
    else:
        status = "위험"

    # 피크 지속시간 보정
    if peak_duration_hour is not None:
        if load_ratio > 0.9 and peak_duration_hour >= 2:
            status = "위험"

    reason = (
        f"부하전류 {load_current}A / 허용전류 {allowable_current}A "
        f"(부하율 {load_ratio:.2f}) 기준 열상승 판단"
    )

    if peak_duration_hour is not None:
        reason += f", 피크 지속시간 {peak_duration_hour}시간 반영"

    return {
        "load_ratio": load_ratio,
        "status": status,
        "reason": reason,
    }
