def temperature_correction_factor_xlpe(temp_c: float) -> float:
    """
    IEC XLPE 케이블 주변온도 보정계수(대표 표)
    기준온도: 30℃
    """
    table = {
        20: 1.08,
        25: 1.04,
        30: 1.00,
        35: 0.96,
        40: 0.91,
        45: 0.87,
        50: 0.82,
    }

    if temp_c is None:
        return 1.0

    if temp_c <= 20:
        return table[20]
    if temp_c >= 50:
        return table[50]

    keys = sorted(table.keys())
    for i in range(len(keys) - 1):
        t1, t2 = keys[i], keys[i + 1]
        if t1 <= temp_c <= t2:
            k1, k2 = table[t1], table[t2]
            # 선형 보간
            return k1 + (k2 - k1) * (temp_c - t1) / (t2 - t1)

    return 1.0
