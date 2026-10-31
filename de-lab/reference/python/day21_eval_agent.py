"""
day21_eval_agent.py  -  Day 21: measure your agent instead of trusting it

Scenario: you changed the agent's prompt or added --context. Did it get better or worse?
An eval is a fixed set of questions with known answers, run the same way every time.

This runs ../../../agent.py on each question (raw mode and --context mode), pulls the first
number out of its final answer and compares it with the ground truth computed by SQL.

Concepts: evals, ground truth from your own warehouse, tolerance, comparing variants,
cost per run (each run spends real API tokens: start with --limit 1).

RUN IT (from the repo root)
  python de-lab/reference/python/day21_eval_agent.py --limit 1
  python de-lab/reference/python/day21_eval_agent.py               all questions, both modes
"""
import os
import re
import subprocess
import sys

import duckdb

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
db = duckdb.connect(f"{ROOT}/warehouse.duckdb", read_only=True)

SEPT = "o.order_ts >= '2026-09-01' AND o.order_ts < '2026-10-01'"
CASES = [
    ("How many orders did we get from Mumbai last month?",
     f"SELECT COUNT(*) FROM orders o JOIN restaurants r USING (restaurant_id) WHERE r.city_id = 1 AND {SEPT}"),
    ("What was our revenue last month?",
     f"""SELECT SUM(o.amount - o.promo_value - t.gst) FROM orders o JOIN order_taxes t USING (order_id)
         LEFT JOIN refunds f USING (order_id) WHERE o.status = 'delivered' AND f.order_id IS NULL AND {SEPT}"""),
    ("How many orders were cancelled in Delhi last month?",
     f"SELECT COUNT(*) FROM orders o JOIN restaurants r USING (restaurant_id) WHERE r.city_id = 3 AND o.status = 'cancelled' AND {SEPT}"),
    ("What was the average order value in Bengaluru last month?",
     f"""SELECT SUM(o.amount - o.promo_value - t.gst) / COUNT(*) FROM orders o JOIN restaurants r USING (restaurant_id)
         JOIN order_taxes t USING (order_id) LEFT JOIN refunds f USING (order_id)
         WHERE r.city_id = 2 AND o.status = 'delivered' AND f.order_id IS NULL AND {SEPT}"""),
]
limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else len(CASES)


def first_number(text):
    """'₹78,09,309' or '6,171' or '1234.5' -> float. Indian grouping commas are removed."""
    match = re.search(r"₹?\s*(\d[\d,]*(?:\.\d+)?)", text.split("ANSWER", 1)[-1])
    return float(match.group(1).replace(",", "")) if match else None


results = []
for question, truth_sql in CASES[:limit]:
    truth = float(db.execute(truth_sql).fetchone()[0])
    for mode in ([], ["--context"]):
        if mode and not os.path.exists(f"{ROOT}/dbt_project/analytics.duckdb"):
            continue                                       # run `dbt build` first to eval --context
        out = subprocess.run(["python3", "agent.py", question, *mode], cwd=ROOT, capture_output=True, text=True).stdout
        got = first_number(out)
        ok = got is not None and abs(got - truth) <= max(1.0, 0.001 * truth)   # 0.1% tolerance
        results.append(ok)
        print(f"{'PASS' if ok else 'FAIL'}  {'context' if mode else 'raw':7}  truth={truth:,.2f}  got={got}  {question}")

print(f"\nScore: {sum(results)}/{len(results)}")
