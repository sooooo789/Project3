
import numpy as np


def tcc_curve(I):
    """
    단순 IEC Inverse 계전 특성 (예시)
    """
    k = 0.14
    alpha = 0.02
    return k / ((I / 1.0) ** alpha - 1)


def relay_coordination(Isc, I_load):
    status = "정상"
    if Isc > I_load * 10:
        status = "즉시 차단 영역"
    return {"status": status}


def relay_coordination(I_sc, I_load):
    """
    간이 보호계전 판단 로직
    """
    pickup_current = 1.25 * I_load      # 과전류 계전 pickup
    instant_trip = 8.0 * I_load         # 순시요소

    result = {
        "pickup": pickup_current,
        "instant": instant_trip,
        "status": "정상"
    }

    if I_sc < pickup_current:
        result["status"] = "계전 미동작 위험"
    elif I_sc > instant_trip:
        result["status"] = "순시차단 영역"
    else:
        result["status"] = "시간지연 차단 영역"

    return result

def relay_coordination(Isc, I_load):
    if Isc > I_load * 10:
        return {"status": "협조 양호"}
    return {"status": "재검토 필요"}
