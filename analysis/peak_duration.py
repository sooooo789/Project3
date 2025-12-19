import numpy as np


def peak_duration_analysis(series, limit, dt=1.0):
    durations = []
    current = 0

    for v in series:
        if v >= limit:
            current += dt
        else:
            if current > 0:
                durations.append(current)
                current = 0

    if current > 0:
        durations.append(current)

    return np.array(durations)


def duration_to_sentence(durations, limit_time):
    if len(durations) == 0:
        return "설계 한계를 초과하는 지속 부하는 관측되지 않았습니다."

    over = durations[durations > limit_time]

    if len(over) == 0:
        return (
            f"설계 기준 지속시간 {limit_time:.1f}s를 "
            f"초과하는 부하는 발생하지 않았습니다."
        )
    else:
        return (
            f"설계 기준 {limit_time:.1f}s 초과 피크가 "
            f"{len(over)}회 발생했으며, "
            f"최대 지속시간은 {over.max():.1f}s입니다."
        )
