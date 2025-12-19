import numpy as np
from scipy.stats import genextreme

def fit_evt(data):
    params = genextreme.fit(data)
    return params
