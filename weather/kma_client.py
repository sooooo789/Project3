import os
import json
import urllib.parse
import urllib.request
from datetime import datetime


def now_kst_base_date_time():
    now = datetime.now()
    base_date = now.strftime("%Y%m%d")
    base_time = now.strftime("%H00")
    return base_date, base_time


def fetch_kma_ultra_srt_ncst(base_date: str, base_time: str, nx: int, ny: int):
    service_key = os.getenv("KMA_SERVICE_KEY")
    if not service_key:
        return None, "NO_KEY"

    endpoint = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"
    params = {
        "serviceKey": service_key,
        "pageNo": "1",
        "numOfRows": "1000",
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": base_time,
        "nx": str(nx),
        "ny": str(ny),
    }

    url = endpoint + "?" + urllib.parse.urlencode(params, doseq=True)

    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            raw = resp.read().decode("utf-8")
            data = json.loads(raw)
            return data, "OK"
    except Exception as e:
        return None, f"ERR:{e}"


def parse_temp_humidity(json_data):
    if not json_data:
        return None, None

    try:
        items = json_data["response"]["body"]["items"]["item"]
    except Exception:
        return None, None

    temp = None
    hum = None
    for it in items:
        cat = it.get("category")
        val = it.get("obsrValue")
        if cat == "T1H":
            try:
                temp = float(val)
            except Exception:
                pass
        elif cat == "REH":
            try:
                hum = float(val)
            except Exception:
                pass

    return temp, hum
