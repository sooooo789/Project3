import numpy as np
from scipy.stats import genextreme


def fit_gev(series, design_limit, return_period=50):
    """
    EVT (GEV) 분석
    - exceed_prob : 설계전류 초과 확률
    - return_level : N년 재현수준 (IEC 개념)
    """

    series = np.asarray(series)

    # GEV fitting
    shape, loc, scale = genextreme.fit(series)

    # 설계 한계 초과 확률
    exceed_prob = 1.0 - genextreme.cdf(
        design_limit, shape, loc, scale
    )

    # Return level (재현수준)
    return_level = genextreme.ppf(
        1.0 - 1.0 / return_period,
        shape,
        loc,
        scale
    )

    return {
        "shape": shape,
        "loc": loc,
        "scale": scale,
        "exceed_prob": float(exceed_prob),
        "return_level": float(return_level),
        "return_period": return_period
    }
