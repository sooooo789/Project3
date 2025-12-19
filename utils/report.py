def generate_report(data, results):
    return (
        "[계산 보고서]\n\n"
        f"전압: {data['V']} kV\n"
        f"변압기 용량: {data['S']} kVA\n"
        f"부하전류: {data['I_load']} A\n\n"
        f"단락전류: {results['Isc']:.1f} A\n"
        f"차단기 판정: {results['breaker']}\n"
        f"케이블: {results['cable']}\n"
        f"열상승: {results['thermal']}\n"
        f"보호계전: {results.get('relay', 'N/A')}\n"
    )

def evaluate_risk(evt_risk, duration_risk, protection_mismatch):
    score = (
        evt_risk * 0.4 +
        duration_risk * 0.3 +
        protection_mismatch * 0.3
    )

    if score < 0.3:
        verdict = "안전"
    elif score < 0.6:
        verdict = "주의"
    else:
        verdict = "위험"

    return score, verdict
