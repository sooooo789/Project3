from db import get_conn
from db_init import init_db
from datetime import datetime

def seed_one_sample():
    conn = get_conn()
    cur = conn.cursor()

    # assets 1건 없으면 넣기
    cur.execute("SELECT asset_id FROM assets LIMIT 1;")
    row = cur.fetchone()
    if row is None:
        cur.execute("""
        INSERT INTO assets (site_code, transformer_kva, voltage_kv, z_pct)
        VALUES (?, ?, ?, ?);
        """, ("SITE-TEST", 1500.0, 0.4, 6.0))
        asset_id = cur.lastrowid
    else:
        asset_id = row[0]

    # external snapshot(기상) 1건 넣기(전력수급/KPX는 키 없으니 비움)
    cur.execute("""
    INSERT INTO external_risk_snapshot (site_code, ts, temp_c, humidity_pct, external_risk_score)
    VALUES (?, ?, ?, ?, ?);
    """, ("SITE-TEST", datetime.now().isoformat(), 33.0, 70.0, 2.0))
    # snapshot_id = cur.lastrowid  # 지금은 assessments에 굳이 연결 안 해도 됨

    # assessments 1건 넣기(예시 값)
    In_a = 2165.0
    Isc_ka = 36.1
    breaker_ok = 1
    hard_final = "조건미충족"  # 케이블/열상승 미입력 가정

    risk_internal = 62.0
    risk_external = 2.0
    risk_final = risk_internal + risk_external

    cur.execute("""
    INSERT INTO assessments (
        asset_id, In_a, Isc_ka, breaker_ok, hard_final,
        risk_internal, risk_external, risk_final, run_ts
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        asset_id, In_a, Isc_ka, breaker_ok, hard_final,
        risk_internal, risk_external, risk_final, datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()

def print_assessments():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM assessments ORDER BY assessment_id DESC;")
    rows = cur.fetchall()

    print("\n=== assessments (최신순) ===")
    for r in rows:
        print(r)

    conn.close()

if __name__ == "__main__":
    # 1) DB 만들기
    init_db()

    # 2) 샘플 1건 저장
    seed_one_sample()

    # 3) 조회 출력
    print_assessments()

    print("\n완료: powercalc.db 생성/저장/조회 OK")
