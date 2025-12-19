import os
import requests
from datetime import date
from dotenv import load_dotenv

load_dotenv()

KMA_KEY = os.getenv("c99800d527c0551e229e390c3708c487432952b607ff90ab1c0806e456cd3c8f")
KPX_KEY = os.getenv("DATA_GO_KPX_KEY")

if not KMA_KEY:
    raise RuntimeError("DATA_GO_KMA_KEY가 없습니다. .env에 넣어주세요.")
if not KPX_KEY:
    raise RuntimeError("DATA_GO_KPX_KEY가 없습니다. .env에 넣어주세요.")


def _get_json(url: str, params: dict) -> dict:
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    # 일부 공공API는 Content-Type이 애매할 수 있어서 try/except
    try:
        return r.json()
    except Exception:
        return {"raw_text": r.text}


# -------------------------
# KMA: ASOS 일자료(기온/습도)
# -------------------------
def kma_asos_daily(stn_id: int, start: date, end: date) -> list[dict]:
    url = "http://apis.data.go.kr/1360000/AsosDalyInfoService/getWthrDataList"
    params = {
        "serviceKey": KMA_KEY,
        "pageNo": 1,
        "numOfRows": 999,
        "dataType": "JSON",
        "dataCd": "ASOS",
        "dateCd": "DAY",
        "stnIds": str(stn_id),
        "startDt": start.strftime("%Y%m%d"),
        "endDt": end.strftime("%Y%m%d"),
    }
    data = _get_json(url, params)
    items = (
        data.get("response", {})
            .get("body", {})
            .get("items", {})
            .get("item", [])
    )
    if isinstance(items, dict):
        items = [items]
    return items


def _to_float(v):
    try:
        return float(v)
    except Exception:
        return None


def normalize_kma_daily(row: dict) -> dict:
    # taAvg: 평균기온, hmAvg: 평균상대습도 (응답 키가 다르면 row 확인해서 맞춰야 함)
    return {
        "ymd": row.get("tm"),
        "temp_c": _to_float(row.get("taAvg")),
        "humidity_pct": _to_float(row.get("hmAvg")),
        "station_id": row.get("stnId"),
        "station_name": row.get("stnNm"),
        "raw": row,
    }


# -------------------------
# KPX: 전력수급 예보(1일 최대)
# -------------------------
def kpx_forecast_1d_max(base_date_yyyymmdd: str) -> dict:
    endpoint = "https://openapi.kpx.or.kr/openapi/forecast1dMaxBaseDate/getForecast1dMaxBaseDate"
    params = {
        "serviceKey": KPX_KEY,
        "baseDate": base_date_yyyymmdd,
    }
    return _get_json(endpoint, params)


def extract_kpx_forecast(payload: dict) -> dict:
    """
    KPX 응답 구조는 서비스별로 다를 수 있음.
    우선 raw를 저장하고, 실제 키는 한번 출력해서 확인 후 정확히 매핑하는게 안전.
    """
    return {"raw": payload}


# -------------------------
# 외생 리스크 점수(0~20) 예시
# - Hard 판정에는 절대 사용하지 않음
# -------------------------
def calc_external_risk_score(temp_c, humidity_pct, kpx_payload: dict) -> tuple[float, dict]:
    score = 0.0
    detail = {
        "temp_risk": 0.0,
        "humidity_risk": 0.0,
        "grid_risk": 0.0,
        "note": "전력수급 정보는 운전 위험도 보정에만 사용"
    }

    if temp_c is not None and temp_c >= 35.0:
        detail["temp_risk"] = 5.0
        score += 5.0
    elif temp_c is not None and temp_c >= 30.0:
        detail["temp_risk"] = 2.0
        score += 2.0

    if humidity_pct is not None and humidity_pct >= 80.0:
        detail["humidity_risk"] = 2.0
        score += 2.0

    # KPX는 응답 키 확정 전까지는 점수 반영 보류가 안전
    # (키를 모른 채로 반영하면 오히려 버그/논리 혼선)
    # 형님이 응답 샘플을 한번 보내주면 여기서 grid_risk를 확정 매핑해 줄게.
    detail["grid_risk"] = 0.0

    score = max(0.0, min(20.0, score))
    return score, detail


def build_external_snapshot(site_code: str, ts_iso: str, kma_daily_row: dict, kpx_payload: dict) -> dict:
    temp_c = kma_daily_row.get("temp_c")
    humidity_pct = kma_daily_row.get("humidity_pct")

    external_score, detail = calc_external_risk_score(temp_c, humidity_pct, kpx_payload)

    return {
        "site_code": site_code,
        "ts": ts_iso,
        "temp_c": temp_c,
        "humidity_pct": humidity_pct,
        "kpx_raw": kpx_payload,              # 그대로 저장(재현성)
        "external_risk_score": external_score,
        "external_risk_detail": detail,      # 이유도 같이 저장
    }


if __name__ == "__main__":
    # 예시 실행
    stn_id = 108  # 서울 ASOS 예시
    d = date(2025, 1, 15)

    kma_rows = kma_asos_daily(stn_id, d, d)
    kma_norm = normalize_kma_daily(kma_rows[0]) if kma_rows else {"temp_c": None, "humidity_pct": None}

    kpx = kpx_forecast_1d_max(d.strftime("%Y%m%d"))

    snap = build_external_snapshot(
        site_code="SITE-SEOUL",
        ts_iso=d.isoformat(),
        kma_daily_row=kma_norm,
        kpx_payload=kpx
    )
    print(snap["external_risk_score"])
    print(snap["external_risk_detail"])
