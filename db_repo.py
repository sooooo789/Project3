from db import get_conn

import sqlite3
from db import get_conn


def insert_weather_snapshot(site_code: str, obs_ts: str, temp_c=None, humidity_pct=None, raw_json=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO weather_snapshot (site_code, obs_ts, temp_c, humidity_pct, raw_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            str(site_code),
            str(obs_ts),
            float(temp_c) if temp_c is not None else None,
            float(humidity_pct) if humidity_pct is not None else None,
            raw_json,
        ),
    )
    conn.commit()
    sid = cur.lastrowid
    conn.close()
    return sid


def get_recent_avg_temp(site_code: str, limit_rows: int = 24):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT temp_c
        FROM weather_snapshot
        WHERE site_code = ?
          AND temp_c IS NOT NULL
        ORDER BY obs_ts DESC
        LIMIT ?
        """,
        (str(site_code), int(limit_rows)),
    )
    rows = cur.fetchall()
    conn.close()

    vals = []
    for r in rows:
        try:
            vals.append(float(r["temp_c"]))
        except Exception:
            pass

    if not vals:
        return None
    return sum(vals) / len(vals)

def ensure_asset(site_code: str, transformer_kva: float, voltage_kv: float, z_pct: float) -> int:
    conn = get_conn()
    cur = conn.cursor()

    # 같은 site_code + 변압기 3요소로 단순 매칭(필요하면 키 확장)
    cur.execute(
        """
        SELECT asset_id
        FROM assets
        WHERE site_code = ?
          AND transformer_kva = ?
          AND voltage_kv = ?
          AND transformer_z_pct = ?
        ORDER BY asset_id DESC
        LIMIT 1
        """,
        (site_code, transformer_kva, voltage_kv, z_pct),
    )
    row = cur.fetchone()
    if row:
        conn.close()
        return int(row["asset_id"])

    cur.execute(
        """
        INSERT INTO assets (site_code, transformer_kva, voltage_kv, transformer_z_pct)
        VALUES (?, ?, ?, ?)
        """,
        (site_code, transformer_kva, voltage_kv, z_pct),
    )
    conn.commit()
    asset_id = int(cur.lastrowid)
    conn.close()
    return asset_id


def insert_assessment(
    asset_id: int,
    In_a: float,
    Isc_ka: float,
    breaker_ok: bool,
    hard_final: str,
    risk_internal=None,
    risk_external=None,
    risk_final=None,
    dt_s=None,
) -> int:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO assessments (
            asset_id, In_a, Isc_ka, breaker_ok, hard_status,
            risk_internal, risk_external, risk_final,
            dt_s
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            int(asset_id),
            float(In_a) if In_a is not None else None,
            float(Isc_ka) if Isc_ka is not None else None,
            1 if breaker_ok is True else 0 if breaker_ok is False else None,
            str(hard_final) if hard_final is not None else None,
            float(risk_internal) if risk_internal is not None else None,
            float(risk_external) if risk_external is not None else None,
            float(risk_final) if risk_final is not None else None,
            float(dt_s) if dt_s is not None else None,
        ),
    )
    conn.commit()
    assessment_id = int(cur.lastrowid)
    conn.close()
    return assessment_id


def update_assessment_risk(assessment_id: int, risk_internal=None, risk_external=None, risk_final=None):
    conn = get_conn()
    cur = conn.cursor()

    # NULL 정책: 전달된 값이 None이면 컬럼을 NULL로 업데이트(또는 유지하고 싶으면 조건 변경)
    cur.execute(
        """
        UPDATE assessments
        SET risk_internal = ?,
            risk_external = ?,
            risk_final    = ?
        WHERE assessment_id = ?
        """,
        (
            float(risk_internal) if risk_internal is not None else None,
            float(risk_external) if risk_external is not None else None,
            float(risk_final) if risk_final is not None else None,
            int(assessment_id),
        ),
    )
    conn.commit()
    conn.close()


def get_last_two_assessments(asset_id: int):
    """
    return: list of rows
    each row includes: assessment_id, hard_status, risk_internal(or risk_final), run_ts
    """
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT assessment_id,
               hard_status,
               COALESCE(risk_final, risk_internal) AS risk_value,
               run_ts
        FROM assessments
        WHERE asset_id = ?
        ORDER BY run_ts DESC
        LIMIT 2
        """,
        (int(asset_id),),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def insert_weather_snapshot(site_code: str, obs_ts: str, temp_c=None, humidity_pct=None, wind_mps=None, raw_json=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO weather_snapshot (site_code, obs_ts, temp_c, humidity_pct, wind_mps, raw_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            str(site_code),
            str(obs_ts),
            float(temp_c) if temp_c is not None else None,
            float(humidity_pct) if humidity_pct is not None else None,
            float(wind_mps) if wind_mps is not None else None,
            raw_json,
        ),
    )
    conn.commit()
    sid = int(cur.lastrowid)
    conn.close()
    return sid

def get_recent_avg_temp(site_code: str, limit_rows: int = 24):
    """
    최근 저장된 weather_snapshot들에서 temp_c 평균을 반환.
    - 없으면 None
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT temp_c
        FROM weather_snapshot
        WHERE site_code = ?
          AND temp_c IS NOT NULL
        ORDER BY obs_ts DESC
        LIMIT ?
        """,
        (str(site_code), int(limit_rows)),
    )
    rows = cur.fetchall()
    conn.close()

    vals = [float(r["temp_c"]) for r in rows if r["temp_c"] is not None]
    if not vals:
        return None
    return sum(vals) / len(vals)

def insert_kpx_snapshot(base_date: str, base_time=None, metric_name=None, metric_value=None, unit=None, raw_json=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO kpx_snapshot (base_date, base_time, metric_name, metric_value, unit, raw_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            str(base_date),
            str(base_time) if base_time is not None else None,
            str(metric_name) if metric_name is not None else None,
            float(metric_value) if metric_value is not None else None,
            str(unit) if unit is not None else None,
            raw_json,
        ),
    )
    conn.commit()
    sid = int(cur.lastrowid)
    conn.close()
    return sid
