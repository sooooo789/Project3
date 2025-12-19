def evt_to_sentence(evt_prob, return_level):
    """
    evt_prob     : 설계 초과 확률 (0~1)
    return_level : GEV 기준 재현주기 레벨 (A, kW 등)
    """

    if evt_prob < 0.01:
        return (
            f"EVT 분석 결과, 극치 발생 확률은 "
            f"{evt_prob*100:.2f}%로 매우 낮으며 "
            f"설계 안정 영역으로 판단됩니다."
        )

    elif evt_prob < 0.05:
        return (
            f"EVT 분석 결과, 극치 발생 확률은 "
            f"{evt_prob*100:.2f}% 수준으로 "
            f"주의가 필요한 경계 영역입니다."
        )

    else:
        return (
            f"EVT 분석 결과, 극치 발생 확률이 "
            f"{evt_prob*100:.2f}%로 높아 "
            f"재현수준 {return_level:.1f} 이상 피크에 "
            f"대한 설계 보강이 요구됩니다."
        )
