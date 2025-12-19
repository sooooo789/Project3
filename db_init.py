from db import get_conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # ---------- assets ----------
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS assets (
            asset_id            INTEGER PRIMARY KEY AUTOINCREMENT,
            site_code           TEXT NOT NULL DEFAULT 'DEFAULT',
            voltage_kv          REAL,
            transformer_kva     REAL,
            transformer_z_pct   REAL,
            breaker_model       TEXT,
            breaker_icu_ka      REAL,
            cable_material      TEXT,
            cable_insulation    TEXT,
            cable_install_method TEXT,
            ambient_temp_c      REAL,
            parallel_count      INTEGER,
            cable_s_mm2         REAL,
            created_at          TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )

    # ---------- assessments ----------
    # hard_status: '적합'/'부적합'/'조건 미충족' 등 텍스트
    # risk_internal/external/final: NULL 허용 (없으면 NULL)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS assessments (
            assessment_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id            INTEGER NOT NULL,
            run_ts              TEXT NOT NULL DEFAULT (datetime('now')),

            -- 핵심 결과
            In_a                REAL,
            Isc_ka              REAL,
            breaker_ok          INTEGER, -- 1/0/NULL
            hard_status         TEXT,

            -- 위험도(운전 리스크) 점수: 내부/외부/최종
            risk_internal       REAL,
            risk_external       REAL,
            risk_final          REAL,

            -- 분석 메타(선택)
            evt_method          TEXT,
            evt_exceed_prob     REAL,
            observed_exceed     REAL,
            duration_max_s      REAL,
            dt_s                REAL,

            -- TCC(선택)
            tcc_available       INTEGER,
            tcc_margin          REAL,
            t_clear_used_s      REAL,

            note                TEXT,

            FOREIGN KEY(asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE
        );
        """
    )

    # ---------- weather_snapshot ----------
    # 기상청/기타 기상 스냅샷 저장용 (운전 위험도 보정 레이어)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS weather_snapshot (
            snapshot_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            site_code     TEXT NOT NULL,
            obs_ts        TEXT NOT NULL,
            temp_c        REAL,
            humidity_pct  REAL,
            raw_json      TEXT,
            created_at    TEXT NOT NULL DEFAULT (datetime('now'))
        );
CREATE INDEX IF NOT EXISTS idx_weather_site_ts ON weather_snapshot(site_code, obs_ts DESC);
        """
    )

    # ---------- kpx_snapshot ----------
    # KPX 전력수급/예측 스냅샷 저장용 (운전 위험도 보정 레이어)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS kpx_snapshot (
            snapshot_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            base_date       TEXT NOT NULL,   -- YYYYMMDD 등
            base_time       TEXT,            -- HHMM 등(있으면)
            metric_name     TEXT,            -- 예: forecast1dMax, reserveMargin 등
            metric_value    REAL,
            unit            TEXT,
            raw_json        TEXT,
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )

    # ---------- indexes ----------
    cur.execute("CREATE INDEX IF NOT EXISTS idx_assets_site ON assets(site_code);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_assess_asset_ts ON assessments(asset_id, run_ts DESC);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_weather_site_ts ON weather_snapshot(site_code, obs_ts DESC);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_kpx_date_time ON kpx_snapshot(base_date, base_time);")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("완료: powercalc.db 스키마 생성/업데이트 OK")
