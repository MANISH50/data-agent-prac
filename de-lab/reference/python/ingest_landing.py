"""
ingest_landing.py  -  reference solution for Days 5, 12 and 13

Loads every landing CSV into de-lab/lab.duckdb, the way a production loader should:
  * idempotent      re-running loads nothing twice (each file is replaced as a unit)
  * lineage         every row keeps _source_file and _loaded_at
  * schema drift    known renames are mapped (order_amount -> amount); unknown extras are kept in _extra
  * quarantine      rows that break a blocking rule go to quarantine_orders with the reason, not into stg
  * dedup           exact duplicate rows are collapsed; order_id is unique in stg_orders

Tables written (lab.duckdb only; warehouse.duckdb is attached read-only):
  raw_orders         everything as text, exactly as it arrived (+ lineage)
  quarantine_orders  rejected rows + reject_reason
  stg_orders         clean, typed, one row per order_id

RUN IT (from the repo root)
  python de-lab/reference/python/ingest_landing.py
"""
import glob
import os

import duckdb

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
LANDING = f"{ROOT}/de-lab/data/landing/orders"
EXPECTED = ["order_id", "customer_id", "restaurant_id", "order_ts", "status", "amount", "promo_value",
            "payment_method", "cancel_reason"]
RENAMES = {"order_amount": "amount"}            # schema drift we have agreed to accept

db = duckdb.connect(f"{ROOT}/de-lab/lab.duckdb")
db.execute(f"ATTACH IF NOT EXISTS '{ROOT}/warehouse.duckdb' AS wh (READ_ONLY)")
db.execute(f"""CREATE TABLE IF NOT EXISTS raw_orders (
    {', '.join(c + ' VARCHAR' for c in EXPECTED)}, _extra VARCHAR, _source_file VARCHAR, _loaded_at TIMESTAMP)""")

# ---------------------------------------------------------------------------
# 1. RAW: load each file as text, map drifted columns, replace the file's rows (idempotent)
# ---------------------------------------------------------------------------
for path in sorted(glob.glob(f"{LANDING}/orders_*.csv")):
    name = os.path.basename(path)
    header = [c[0] for c in db.execute(f"DESCRIBE SELECT * FROM read_csv('{path}', all_varchar=true)").fetchall()]
    mapped = {col: RENAMES.get(col, col) for col in header}
    missing = [c for c in EXPECTED if c not in mapped.values()]
    if missing:
        raise SystemExit(f"{name}: missing required columns {missing}. Stop and talk to the source team.")
    extras = [col for col in header if mapped[col] not in EXPECTED]
    select = ", ".join(f'"{src}" AS {dst}' for src, dst in mapped.items() if dst in EXPECTED)
    extra_sql = ("to_json(struct_pack(" + ", ".join(f'"{c}" := "{c}"' for c in extras) + "))::VARCHAR") if extras else "NULL"
    if extras or any(src != dst for src, dst in mapped.items()):
        print(f"  schema drift in {name}: renamed={ {s: d for s, d in mapped.items() if s != d} } extra={extras}")

    db.execute("BEGIN")
    db.execute("DELETE FROM raw_orders WHERE _source_file = ?", [name])
    db.execute(f"""INSERT INTO raw_orders
                   SELECT {', '.join(EXPECTED)}, _extra, _source_file, _loaded_at FROM (
                     SELECT {select}, {extra_sql} AS _extra, '{name}' AS _source_file, now() AS _loaded_at
                     FROM read_csv('{path}', all_varchar=true))""")
    db.execute("COMMIT")

# ---------------------------------------------------------------------------
# 2. TYPE + VALIDATE: parse both timestamp formats, normalise status, flag blocking problems
# ---------------------------------------------------------------------------
db.execute("""
CREATE OR REPLACE TEMP VIEW typed AS
SELECT *,
       CASE WHEN customer_id IS NULL OR customer_id = '' THEN 'missing customer_id'
            WHEN order_ts_parsed IS NULL                 THEN 'unparseable order_ts'
            WHEN amount_num < 0                          THEN 'negative amount'
            WHEN r.restaurant_id IS NULL                 THEN 'orphan restaurant_id'
            WHEN status_norm NOT IN ('delivered', 'cancelled') THEN 'unknown status'
       END AS reject_reason
FROM (
  SELECT raw_orders.*,
         TRY_CAST(order_id AS BIGINT)                AS order_id_num,
         COALESCE(TRY_STRPTIME(order_ts, '%Y-%m-%d %H:%M:%S'),
                  TRY_STRPTIME(order_ts, '%d/%m/%Y %H:%M'))  AS order_ts_parsed,
         TRY_CAST(amount AS DECIMAL(10,2))            AS amount_num,
         lower(trim(status))                          AS status_norm
  FROM raw_orders
) t
LEFT JOIN wh.restaurants r ON r.restaurant_id = TRY_CAST(t.restaurant_id AS INTEGER)
""")

db.execute("""CREATE OR REPLACE TABLE quarantine_orders AS
              SELECT * EXCLUDE (order_id_num, order_ts_parsed, amount_num, status_norm)
              FROM typed WHERE reject_reason IS NOT NULL""")

# ---------------------------------------------------------------------------
# 3. STG: one row per order_id. If an order arrives twice, keep the latest load.
# ---------------------------------------------------------------------------
db.execute("""
CREATE OR REPLACE TABLE stg_orders AS
SELECT order_id_num                         AS order_id,
       TRY_CAST(customer_id AS INTEGER)     AS customer_id,
       TRY_CAST(restaurant_id AS INTEGER)   AS restaurant_id,
       order_ts_parsed                      AS order_ts,
       CAST(order_ts_parsed AS DATE)        AS order_date,
       status_norm                          AS status,
       amount_num                           AS amount,
       TRY_CAST(promo_value AS DECIMAL(10,2)) AS promo_value,
       payment_method,
       NULLIF(cancel_reason, '')            AS cancel_reason,
       _extra, _source_file, _loaded_at,
       CAST(order_ts_parsed AS DATE) < CAST(strptime(regexp_extract(_source_file, '\\d{4}-\\d{2}-\\d{2}'), '%Y-%m-%d') AS DATE)
                                            AS is_late_arriving
FROM typed
WHERE reject_reason IS NULL
QUALIFY row_number() OVER (PARTITION BY order_id_num ORDER BY _loaded_at DESC, _source_file DESC) = 1
""")

for table in ["raw_orders", "quarantine_orders", "stg_orders"]:
    print(f"{table:18} {db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]:>6,} rows")
print(db.execute("SELECT reject_reason, COUNT(*) FROM quarantine_orders GROUP BY 1 ORDER BY 2 DESC").fetchall())
print("late-arriving rows in stg:", db.execute("SELECT COUNT(*) FROM stg_orders WHERE is_late_arriving").fetchone()[0])
