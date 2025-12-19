# utils/plot_config.py

import matplotlib
import matplotlib.pyplot as plt


def set_korean_font():
    """
    Matplotlib 한글 폰트 설정(Windows 우선: Malgun Gothic)
    """
    candidates = [
        "Malgun Gothic",      # Windows
        "AppleGothic",        # macOS
        "NanumGothic",        # Linux (설치 필요)
        "Noto Sans CJK KR",   # 설치 필요
        "Noto Sans KR",       # 설치 필요
    ]

    available = {f.name for f in matplotlib.font_manager.fontManager.ttflist}

    chosen = None
    for name in candidates:
        if name in available:
            chosen = name
            break

    if chosen:
        plt.rcParams["font.family"] = chosen

    plt.rcParams["axes.unicode_minus"] = False
