"""
build_notebooks.py  -  writes the lab notebooks in de-lab/notebooks/ (and runs them with --execute)

The notebooks are generated from this file so they stay small, reviewable and diff-friendly.
Edit the cells here, then rebuild:
  python de-lab/scripts/build_notebooks.py --execute
"""
import os
import sys

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "notebooks")

SETUP = '''import pathlib, duckdb
ROOT = next(p for p in [pathlib.Path.cwd(), *pathlib.Path.cwd().parents] if (p / "warehouse.duckdb").exists())
wh = duckdb.connect(str(ROOT / "warehouse.duckdb"), read_only=True)   # production: ALWAYS read-only
def q(sql, con=None):
    return (con or wh).sql(sql)'''

NOTEBOOKS = {
    "00_warehouse_tour.ipynb": [
        new_markdown_cell("# 00 · Warehouse tour\nThe production warehouse (`warehouse.duckdb`) of a food-delivery company. "
                          "Read-only. 6 tables, Apr–14 Oct 2026. Use this notebook on **Day 1** next to Claude Code."),
        new_code_cell(SETUP),
        new_markdown_cell("## Tables and row counts"),
        new_code_cell("q(\"\"\"SELECT table_name, estimated_size AS approx_rows, column_count\n"
                      "   FROM duckdb_tables() ORDER BY table_name\"\"\")"),
        new_markdown_cell("## How the tables connect\n```\ncities ──< restaurants ──< orders >── customers\n"
                          "                              ├── order_taxes  (GST, 1 row per order)\n"
                          "                              └── refunds      (only refunded orders)\n```\n"
                          "An order's **city comes through the restaurant**, not the customer."),
        new_code_cell("q(\"\"\"SELECT c.city_name, COUNT(*) AS orders\nFROM orders o JOIN restaurants r USING (restaurant_id) "
                      "JOIN cities c USING (city_id)\nGROUP BY 1 ORDER BY 2 DESC\"\"\")"),
        new_markdown_cell("## Orders per week (spot the Mumbai rain week, 5–11 Oct)"),
        new_code_cell("q(\"\"\"SELECT date_trunc('week', order_ts)::DATE AS week, COUNT(*) AS placed,\n"
                      "       COUNT(*) FILTER (WHERE status = 'cancelled') AS cancelled\nFROM orders o JOIN restaurants r USING (restaurant_id)\n"
                      "WHERE r.city_id = 1 AND order_ts >= '2026-09-01'\nGROUP BY 1 ORDER BY 1\"\"\")"),
        new_markdown_cell("## The revenue traps\n`amount` includes GST and is before promo; refunded orders still say `delivered`; "
                          "cancelled orders still have an amount. Compare the naive and correct numbers for September:"),
        new_code_cell("q(\"\"\"SELECT SUM(o.amount) AS naive_sum_amount,\n"
                      "  SUM(o.amount - o.promo_value - t.gst) FILTER (WHERE o.status = 'delivered' AND f.order_id IS NULL) AS revenue\n"
                      "FROM orders o JOIN order_taxes t USING (order_id) LEFT JOIN refunds f USING (order_id)\n"
                      "WHERE o.order_ts >= '2026-09-01' AND o.order_ts < '2026-10-01'\"\"\")"),
        new_markdown_cell("### Exercise\nAsk Claude Code: *“Using only warehouse.duckdb, which payment method has the highest refund rate?”* "
                          "Then verify its SQL here."),
        new_code_cell("# your verification query here\n"),
    ],
    "01_landing_zone_profiling.ipynb": [
        new_markdown_cell("# 01 · Landing zone profiling\nNew files for 15–21 Oct arrived in `de-lab/data/landing/`. "
                          "Before loading anything, profile them. **Days 4–5.** Always read as text first (`all_varchar=true`) "
                          "so DuckDB does not silently guess types."),
        new_code_cell(SETUP + "\nLANDING = ROOT / 'de-lab/data/landing'\nsorted(p.name for p in (LANDING / 'orders').glob('*.csv'))"),
        new_markdown_cell("## Header of every file: spot schema drift"),
        new_code_cell("for p in sorted((LANDING / 'orders').glob('*.csv')):\n"
                      "    cols = [c[0] for c in wh.sql(f\"DESCRIBE SELECT * FROM read_csv('{p}', all_varchar=true)\").fetchall()]\n"
                      "    print(p.name, cols)"),
        new_markdown_cell("## Row count vs distinct order_id per file: spot duplicates"),
        new_code_cell("q(f\"\"\"SELECT filename, COUNT(*) AS rows, COUNT(DISTINCT order_id) AS distinct_ids\n"
                      "FROM read_csv('{LANDING}/orders/*.csv', all_varchar=true, union_by_name=true, filename=true)\n"
                      "GROUP BY 1 ORDER BY 1\"\"\")"),
        new_markdown_cell("## SUMMARIZE one file\n`SUMMARIZE` gives min / max / nulls / distinct counts for every column in one line."),
        new_code_cell("q(f\"SUMMARIZE SELECT * FROM read_csv('{LANDING}/orders/orders_2026-10-17.csv')\")"),
        new_markdown_cell("## Exercises (find them, then ask Claude to write the check)\n"
                          "1. Which file has timestamps in a second format?\n2. Which rows have a restaurant_id that does not exist?\n"
                          "3. Which day is missing?\n4. Which rows arrived late (order date ≠ file date)?\n\n"
                          "Answer key: `de-lab/reference/landing_answer_key.md` (no peeking)."),
        new_code_cell("# your queries here\n"),
        new_markdown_cell("## Semi-structured: the nested menu feed (Day 6)"),
        new_code_cell("q(f\"\"\"SELECT r.restaurant_id, r.name, i.name AS item, i.price.amount AS price_inr, i.tags, i.available\n"
                      "FROM (SELECT unnest(restaurants) AS r FROM read_json('{LANDING}/restaurant_menus.json')),\n"
                      "     LATERAL (SELECT unnest(r.menu.items) AS i)\nLIMIT 10\"\"\")"),
        new_markdown_cell("## Free text: support tickets (Days 16, 18)"),
        new_code_cell("q(f\"SELECT channel, COUNT(*) FROM read_json('{LANDING}/support_tickets.jsonl') GROUP BY 1\")"),
    ],
    "02_lab_tables.ipynb": [
        new_markdown_cell("# 02 · Lab tables after the load\nRun the loader first (yours from Day 5, or the reference):\n"
                          "```bash\npython de-lab/reference/python/ingest_landing.py\n```\n"
                          "`de-lab/lab.duckdb` is **your** sandbox: write anything here. The warehouse is attached read-only as `wh`."),
        new_code_cell(SETUP + "\nlab = duckdb.connect(str(ROOT / 'de-lab/lab.duckdb'), read_only=True)\n"
                      "q(\"SELECT table_name, estimated_size AS approx_rows FROM duckdb_tables()\", lab)"),
        new_markdown_cell("## What got quarantined, and why"),
        new_code_cell("q(\"SELECT reject_reason, _source_file, COUNT(*) AS rows FROM quarantine_orders GROUP BY ALL ORDER BY rows DESC\", lab)"),
        new_markdown_cell("## Reconciliation: raw → stg (every row accounted for)"),
        new_code_cell("q(\"\"\"WITH c AS (SELECT (SELECT COUNT(*) FROM raw_orders) AS raw_rows,\n"
                      "                  (SELECT COUNT(*) FROM quarantine_orders) AS quarantined,\n"
                      "                  (SELECT COUNT(*) FROM stg_orders) AS stg_rows)\n"
                      "SELECT *, raw_rows - quarantined - stg_rows AS deduplicated FROM c\"\"\", lab)"),
        new_markdown_cell("## Daily orders, including the gap on 20 Oct and the late rows"),
        new_code_cell("q(\"\"\"SELECT order_date, COUNT(*) AS orders, COUNT(*) FILTER (WHERE is_late_arriving) AS late_rows\n"
                      "FROM stg_orders GROUP BY 1 ORDER BY 1\"\"\", lab)"),
        new_markdown_cell("### Exercise\nAsk Claude to add a dbt test that would have caught the missing 20 Oct partition."),
    ],
    "03_claude_api_playground.ipynb": [
        new_markdown_cell("# 03 · Claude API playground\nScratchpad for **Days 15–18**. Needs `ANTHROPIC_API_KEY`. Every cell that "
                          "calls the API costs real tokens: set `LAB_MODEL=claude-haiku-5-5` for cheap practice."),
        new_code_cell("import os, anthropic\nMODEL = os.environ.get('LAB_MODEL', 'claude-opus-5-5')\n"
                      "HAS_KEY = bool(os.environ.get('ANTHROPIC_API_KEY'))\nclient = anthropic.Anthropic() if HAS_KEY else None\n"
                      "print('model:', MODEL, '| API key set:', HAS_KEY)"),
        new_markdown_cell("## 1. One call"),
        new_code_cell("if HAS_KEY:\n    r = client.messages.create(model=MODEL, max_tokens=2000, output_config={'effort': 'low'},\n"
                      "        messages=[{'role': 'user', 'content': 'Explain SCD type 2 in 3 bullet points for a data engineer.'}])\n"
                      "    print(r.stop_reason, r.usage.input_tokens, r.usage.output_tokens)\n"
                      "    print(''.join(b.text for b in r.content if b.type == 'text'))"),
        new_markdown_cell("## 2. Structured output: SQL → lineage JSON"),
        new_code_cell("from pydantic import BaseModel\nclass Lineage(BaseModel):\n    source_tables: list[str]\n    output_columns: list[str]\n"
                      "    filters: list[str]\n\nSQL = open('../../dbt_project/models/marts/fct_orders.sql').read()\n"
                      "if HAS_KEY:\n    r = client.messages.parse(model=MODEL, max_tokens=4000, output_format=Lineage,\n"
                      "        messages=[{'role': 'user', 'content': 'Extract lineage from this dbt model:\\n' + SQL}])\n"
                      "    print(r.parsed_output)"),
        new_markdown_cell("## 3. Prompt caching check\nRun the same long-prefix request twice; the second should show `cache_read_input_tokens > 0`."),
        new_code_cell("GUIDE = open('../reference/ticket_classification_guide.md').read() * 3   # long, stable prefix\n"
                      "if HAS_KEY:\n    for i in range(2):\n        r = client.messages.create(model=MODEL, max_tokens=500, output_config={'effort': 'low'},\n"
                      "            system=[{'type': 'text', 'text': GUIDE, 'cache_control': {'type': 'ephemeral'}}],\n"
                      "            messages=[{'role': 'user', 'content': 'order 271002 was 50 min late'}])\n"
                      "        print(i, 'written:', r.usage.cache_creation_input_tokens, 'read:', r.usage.cache_read_input_tokens)"),
    ],
}

os.makedirs(OUT, exist_ok=True)
for name, cells in NOTEBOOKS.items():
    nb = new_notebook(cells=cells, metadata={"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"}})
    path = os.path.join(OUT, name)
    if "--execute" in sys.argv:
        from nbclient import NotebookClient
        NotebookClient(nb, timeout=120, resources={"metadata": {"path": OUT}}).execute()
    nbformat.write(nb, path)
    print("wrote", os.path.relpath(path))
