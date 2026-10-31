"""
day17_dq_agent_tool_runner.py  -  Day 17: a data-quality agent with the SDK Tool Runner

Scenario: every morning someone has to look at the new landing files, decide whether they are
safe to load, and explain why not. Give Claude tools and let it investigate.

Compare with ../../../agent.py, which writes the agent loop by hand. Here the SDK's tool runner
runs the loop: you only write the tools. Tool schemas come from the type hints + docstrings.

Concepts: tool use, tool design (small, safe, read-only), the agent loop, tool errors fed back
to the model, a final structured verdict.

RUN IT (from the repo root)
  python de-lab/reference/python/day17_dq_agent_tool_runner.py "Is orders_2026-10-19.csv safe to load?"
"""
import glob
import os
import sys

import anthropic
import duckdb
from anthropic import beta_tool

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
MODEL = os.environ.get("LAB_MODEL", "claude-opus-5-5")
LANDING = f"{ROOT}/de-lab/data/landing/orders"
QUESTION = sys.argv[1] if len(sys.argv) > 1 else "Check all landing files. Which ones are safe to load today?"

db = duckdb.connect()
db.execute(f"ATTACH '{ROOT}/warehouse.duckdb' AS wh (READ_ONLY)")


@beta_tool
def list_landing_files() -> str:
    """List the order files waiting in the landing zone, with their size in bytes."""
    return "\n".join(f"{os.path.basename(p)}  {os.path.getsize(p)} bytes" for p in sorted(glob.glob(f"{LANDING}/*.csv")))


@beta_tool
def preview_file(file_name: str, rows: int = 5) -> str:
    """Show the header and the first rows of one landing file, read as text.

    Args:
        file_name: File name only, e.g. orders_2026-10-17.csv
        rows: How many rows to show (max 20).
    """
    path = os.path.join(LANDING, os.path.basename(file_name))
    result = db.execute(f"SELECT * FROM read_csv('{path}', all_varchar=true) LIMIT {min(int(rows), 20)}")
    cols = [c[0] for c in result.description]
    return "\n".join([" | ".join(cols)] + [" | ".join(map(str, r)) for r in result.fetchall()])


@beta_tool
def run_sql(sql: str) -> str:
    """Run one read-only DuckDB query and return up to 50 rows.
    Landing files are read with read_csv('de-lab/data/landing/orders/<file>', all_varchar=true).
    The warehouse is attached as `wh` (tables wh.restaurants, wh.orders, ...).

    Args:
        sql: A single SELECT statement.
    """
    if not sql.lstrip().lower().startswith(("select", "with", "describe", "summarize")):
        return "ERROR: only SELECT / WITH / DESCRIBE / SUMMARIZE are allowed."
    try:
        os.chdir(ROOT)
        result = db.execute(sql)
        cols = [c[0] for c in result.description]
        return "\n".join([" | ".join(cols)] + [" | ".join(map(str, r)) for r in result.fetchmany(50)])
    except Exception as error:        # the model reads the error and fixes its own SQL
        return f"ERROR: {error}"


SYSTEM = """You are the on-call data engineer. Investigate landing order files before they are loaded.
Expected columns: order_id, customer_id, restaurant_id, order_ts (YYYY-MM-DD HH:MM:SS), status
(delivered|cancelled), amount, promo_value, payment_method, cancel_reason.
Check schema, duplicates, nulls, timestamp formats, negative amounts, orphan restaurant_ids, late rows
and missing days. Use evidence from your tools only. Finish with a table:
file | verdict (LOAD / LOAD WITH FIX / BLOCK) | reason | suggested fix."""

client = anthropic.Anthropic()
runner = client.beta.messages.tool_runner(
    model=MODEL,
    max_tokens=16000,
    system=SYSTEM,
    output_config={"effort": "medium"},
    tools=[list_landing_files, preview_file, run_sql],
    messages=[{"role": "user", "content": QUESTION}],
)

for message in runner:                       # one iteration per model turn
    for block in message.content:
        if block.type == "tool_use":
            print(f"-> {block.name}({block.input})")
        elif block.type == "text" and message.stop_reason != "tool_use":
            print("\n" + block.text)
