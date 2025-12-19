# db_save.py
from db import get_conn
from datetime import datetime

def save_assessment(
    asset_id,
    In_a,
    Isc_ka,
    breaker_ok,
    hard_final,
    risk_internal,
    risk_external
):
    conn = get_conn()
    cur = conn.cursor()

    risk_final = risk_internal + risk_external

    cur.execute("""
    INSERT INTO assessments (
        asset_id, In_a, Isc_ka, breaker_ok,
        hard_final, risk_internal, risk_external,
        risk_final, run_ts
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        asset_id, In_a, Isc_ka, int(breaker_ok),
        hard_final, risk_internal, risk_external,
        risk_final, datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()
