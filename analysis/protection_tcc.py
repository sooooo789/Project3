import numpy as np


def tcc_curve(I, pickup, TMS):
    """
    IEC Standard Inverse (SI) 곡선
    I: 전류 배열
    pickup: 픽업전류
    TMS: Time Multiplier Setting
    """
    return TMS * 0.14 / ((I / pickup) ** 0.02 - 1)


def tcc_protection_margin(
    peak_current,
    peak_duration,
    pickup,
    TMS
):
    """
    보호계전 여유도 계산
    반환값: 0~1 (1에 가까울수록 안전)
    """
    if peak_current <= pickup:
        return 1.0

    t_trip = tcc_curve(
        np.array([peak_current]),
        pickup,
        TMS
    )[0]

    if peak_duration >= t_trip:
        return 0.0

    margin = 1.0 - (peak_duration / t_trip)
    return max(min(margin, 1.0), 0.0)
