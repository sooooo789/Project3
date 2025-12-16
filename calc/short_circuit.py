import math


def calc_short_circuit(capacity_kva, voltage_kv, impedance_percent):
    z = impedance_percent / 100
    isc = capacity_kva / (math.sqrt(3) * voltage_kv * z)

    reason = (
        f"변압기 용량 {capacity_kva}kVA, "
        f"전압 {voltage_kv}kV, "
        f"임피던스 {impedance_percent}% 기준 단락전류 계산"
    )

    return isc, "계산 완료", reason
