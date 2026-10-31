"""
dq_check.py  -  reference solution for Day 4: profile and validate landing order files

RUN IT (from the repo root)
  python de-lab/reference/python/dq_check.py                         every landing file
  python de-lab/reference/python/dq_check.py path/to/orders_X.csv    one file
  add --json to get machine-readable output (used by the headless job on Day 14)
Exit code 1 if any blocking check fails, so it can gate a pipeline.
"""
import datetime as dt
import glob
import json
import os
import re
import sys

import duckdb

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
EXPECTED = ["order_id", "customer_id", "restaurant_id", "order_ts", "status", "amount", "promo_value",
            "payment_method", "cancel_reason"]
db = duckdb.connect()
db.execute(f"ATTACH '{ROOT}/warehouse.duckdb' AS wh (READ_ONLY)")


def check_file(path):
    src = f"read_csv('{path}', all_varchar=true)"
    file_date = re.search(r"\d{4}-\d{2}-\d{2}", os.path.basename(path)).group()
    header = [c[0] for c in db.execute(f"DESCRIBE SELECT * FROM {src}").fetchall()]
    results = []

    def add(check, failing, example, severity):
        results.append({"check": check, "failing_rows": failing, "severity": severity, "example": example})

    drift = sorted(set(header) ^ set(EXPECTED))
    add("schema matches contract", len(drift), ", ".join(drift) or None, "block")
    amount_col = "amount" if "amount" in header else ("order_amount" if "order_amount" in header else None)

    def count(where, example_col):
        row = db.execute(f"SELECT COUNT(*), ANY_VALUE({example_col}) FROM {src} WHERE {where}").fetchone()
        return row[0], row[1]

    total = db.execute(f"SELECT COUNT(*) FROM {src}").fetchone()[0]
    dups = total - db.execute(f"SELECT COUNT(DISTINCT order_id) FROM {src}").fetchone()[0]
    add("duplicate order_id", dups, None, "warn")
    add("missing customer_id", *count("customer_id IS NULL OR customer_id = ''", "order_id"), "block")
    add("unparseable order_ts", *count("TRY_STRPTIME(order_ts, '%Y-%m-%d %H:%M:%S') IS NULL", "order_ts"), "block")
    add("order_ts outside file date", *count(f"TRY_STRPTIME(order_ts, '%Y-%m-%d %H:%M:%S')::DATE <> DATE '{file_date}'", "order_ts"), "warn")
    if amount_col:
        add("negative amount", *count(f"TRY_CAST({amount_col} AS DOUBLE) < 0", amount_col), "block")
    add("status not lower-case delivered/cancelled", *count("status NOT IN ('delivered', 'cancelled')", "status"), "warn")
    add("orphan restaurant_id", *count("TRY_CAST(restaurant_id AS INTEGER) NOT IN (SELECT restaurant_id FROM wh.restaurants)", "restaurant_id"), "block")
    return {"file": os.path.basename(path), "rows": total, "checks": results,
            "status": "FAIL" if any(r["failing_rows"] and r["severity"] == "block" for r in results) else "PASS"}


def missing_days(paths):
    dates = sorted(dt.date.fromisoformat(re.search(r"\d{4}-\d{2}-\d{2}", p).group()) for p in paths)
    expected = {dates[0] + dt.timedelta(days=i) for i in range((dates[-1] - dates[0]).days + 1)}
    return sorted(str(d) for d in expected - set(dates))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    paths = args or sorted(glob.glob(f"{ROOT}/de-lab/data/landing/orders/orders_*.csv"))
    report = {"files": [check_file(p) for p in paths], "missing_days": missing_days(paths) if not args else []}
    failed = any(f["status"] == "FAIL" for f in report["files"]) or report["missing_days"]

    if "--json" in sys.argv:
        print(json.dumps(report, indent=2, default=str))
    else:
        for f in report["files"]:
            print(f"\n{f['file']}  ({f['rows']:,} rows)  {f['status']}")
            for r in f["checks"]:
                if r["failing_rows"]:
                    print(f"   [{r['severity']:5}] {r['check']:42} {r['failing_rows']:>4}   e.g. {r['example']}")
        if report["missing_days"]:
            print(f"\nMISSING FILES for: {', '.join(report['missing_days'])}")
    sys.exit(1 if failed else 0)
