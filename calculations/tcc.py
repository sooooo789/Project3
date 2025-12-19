import numpy as np


def tcc_curve(I_pickup, curve_type="IEC"):
    I = np.logspace(np.log10(I_pickup * 1.1), np.log10(I_pickup * 20), 50)

    if curve_type == "IEC":
        t = 0.14 / ((I / I_pickup) ** 0.02 - 1)
    else:
        t = 13.5 / (I / I_pickup - 1)

    return I, t
