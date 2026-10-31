"""
token_lab_agent.py  -  Days 23-27: the same data agent, instrumented, with token optimisations you can switch on

It answers a warehouse question like ../../../agent.py, but prints the tokens of EVERY turn
(input, cache write, cache read, output) and the cost, so you can see where tokens go and
measure each optimisation on its own.

  baseline        agent.py's design: discover tables with tools, 3 sample rows, 50-row results
  --lean          schema digest in the system prompt (no discovery turns), terse tools,
                  results capped at 20 rows with a "N more rows" note, numbers rounded
  --cache         prompt caching: explicit breakpoint on the static system prompt + automatic
                  caching of the growing conversation
  --clear-tools   context editing: the API clears old tool results once context grows
  --dry-run       no API call: show how big each piece of context is, and compare tool
                  result sizes baseline vs lean (free, works without an API key)

RUN IT (from the repo root)
  python de-lab/reference/python/token_lab_agent.py "What was our revenue last month?" --dry-run
  python de-lab/reference/python/token_lab_agent.py "What was our revenue last month?"
  python de-lab/reference/python/token_lab_agent.py "What was our revenue last month?" --lean --cache
Each real run appends one line to de-lab/reports/token_runs.jsonl for comparison.
"""
import json
import os
import sys
import time

import duckdb

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
QUESTION = next((a for a in sys.argv[1:] if not a.startswith("--")), "What was our revenue last month?")
LEAN, CACHE, CLEAR, DRY = ("--lean" in sys.argv, "--cache" in sys.argv, "--clear-tools" in sys.argv, "--dry-run" in sys.argv)
MODEL = os.environ.get("LAB_MODEL", "claude-opus-5-5")
TODAY = "2026-10-15"

# USD per million tokens: input, output, cache read, cache write (5-minute TTL = 1.25x input).
# Check the current pricing page before quoting numbers to anyone.
PRICES = {"claude-opus-5-5": (4.00, 20.00, 0.20, 5.00), "claude-sonnet-5-5": (2.00, 10.00, 0.20, 2.50),
          "claude-haiku-5-5": (0.10, 0.50, 0.01, 0.125)}

db = duckdb.connect(f"{ROOT}/warehouse.duckdb", read_only=True)


def estimate_tokens(text):
    """Rough rule of thumb (~4 characters per token for English/SQL). Use count_tokens for real numbers."""
    return max(1, len(text) // 4)


# ---------------------------------------------------------------------------
# Tools. Same capabilities in both modes; lean mode returns far fewer tokens.
# ---------------------------------------------------------------------------
def fmt(value):
    if LEAN and isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def query_to_text(sql):
    max_rows = 20 if LEAN else 50
    result = db.execute(sql)
    columns = [c[0] for c in result.description]
    rows = result.fetchmany(max_rows + 1)
    lines = [" | ".join(columns)] + [" | ".join(fmt(v) for v in row) for row in rows[:max_rows]]
    if LEAN and len(rows) > max_rows:
        lines.append(f"... more rows not shown. Aggregate or add LIMIT instead of reading raw rows.")
    return "\n".join(lines)


def list_tables():
    return query_to_text("SELECT name FROM (SHOW ALL TABLES)" if LEAN else "SELECT database, schema, name FROM (SHOW ALL TABLES)")


def describe_table(table):
    columns = query_to_text(f"SELECT column_name, column_type FROM (DESCRIBE {table})")
    if LEAN:
        return columns
    return columns + "\n\nSample rows:\n" + query_to_text(f"SELECT * FROM {table} LIMIT 3")


def run_sql(sql):
    return query_to_text(sql)


TOOLS = {"list_tables": list_tables, "describe_table": describe_table, "run_sql": run_sql}


def spec(name, description, inputs=()):
    props = {k: {"type": "string"} for k in inputs}
    return {"name": name, "description": description,
            "input_schema": {"type": "object", "properties": props, "required": list(props)}}


if LEAN:
    TOOL_SPECS = [spec("run_sql", "Run one read-only DuckDB SELECT. Returns at most 20 rows; aggregate in SQL.", ["sql"]),
                  spec("describe_table", "Columns of one table.", ["table"])]
else:
    TOOL_SPECS = [spec("list_tables", "List every table in the warehouse."),
                  spec("describe_table", "Show the columns and 3 sample rows of one table.", ["table"]),
                  spec("run_sql", "Run one read-only DuckDB SQL query and get up to 50 rows back.", ["sql"])]


def schema_digest():
    """One compact line per table. Deterministic (sorted) so it never breaks the prompt cache."""
    lines = []
    for (table,) in db.execute("SELECT table_name FROM duckdb_tables() ORDER BY table_name").fetchall():
        cols = db.execute(f"SELECT column_name, column_type FROM (DESCRIBE {table})").fetchall()
        lines.append(f"{table}(" + ", ".join(f"{c} {t.split('(')[0]}" for c, t in cols) + ")")
    return "\n".join(lines)


BASE_INSTRUCTIONS = f"""You are a data analyst agent for a food delivery company in India. Today is {TODAY}.
You can only learn about the data through your tools. Work in a loop: plan, look at the tables
you need, write SQL, run it, then check if the result makes sense. If not, fix the SQL and run again.
When you are confident, give a short final answer: the number (Indian format, like 12,34,567),
one line on how you got it, and the final SQL in a sql code block."""

LEAN_INSTRUCTIONS = f"""Data analyst for an Indian food-delivery company. Today is {TODAY}. DuckDB warehouse schema:
{schema_digest()}
Joins: orders.restaurant_id -> restaurants -> cities (city of an order); order_taxes, refunds by order_id.
Revenue = delivered, not refunded, amount - promo_value - gst.
Write one aggregate query where possible. Answer: the number (Indian format), one line on method, final SQL."""

SYSTEM_TEXT = LEAN_INSTRUCTIONS if LEAN else BASE_INSTRUCTIONS


def dry_run():
    print(f"Question: {QUESTION}\nModel: {MODEL}   mode: {'lean' if LEAN else 'baseline'}\n")
    print(f"{'context piece':38} {'~tokens':>8}")
    print(f"{'system prompt':38} {estimate_tokens(SYSTEM_TEXT):>8}")
    print(f"{'tool definitions':38} {estimate_tokens(json.dumps(TOOL_SPECS)):>8}")
    print(f"{'question':38} {estimate_tokens(QUESTION):>8}")
    print("\nTool result sizes (what gets re-sent on every later turn):")
    sample_sql = "SELECT * FROM orders WHERE order_ts >= '2026-09-01' LIMIT 100"
    for label, fn, arg in [("describe_table('orders')", describe_table, ("orders",)),
                           ("run_sql(100 raw order rows)", run_sql, (sample_sql,))]:
        print(f"  {label:36} {estimate_tokens(fn(*arg)):>8}")
    print("\nRe-run with and without --lean to compare. Real runs report exact numbers from the API.")


def main():
    import anthropic
    client = anthropic.Anthropic()
    system = [{"type": "text", "text": SYSTEM_TEXT}]
    extra, betas = {}, []
    if CACHE:
        system[-1]["cache_control"] = {"type": "ephemeral"}      # static prefix: tools + system
        extra["cache_control"] = {"type": "ephemeral"}           # automatic: the growing conversation
    if CLEAR:
        betas.append("context-management-2025-06-27")
        extra["context_management"] = {"edits": [{"type": "clear_tool_uses_20250919"}]}
    create = client.beta.messages.create if betas else client.messages.create
    if betas:
        extra["betas"] = betas

    messages = [{"role": "user", "content": QUESTION}]
    totals = {"input": 0, "cache_write": 0, "cache_read": 0, "output": 0}
    print(f"{'turn':>4} {'input':>8} {'c.write':>8} {'c.read':>8} {'output':>7}  action")
    started = time.time()
    for turn in range(15):
        response = create(model=MODEL, max_tokens=16000, system=system, tools=TOOL_SPECS, messages=messages,
                          output_config={"effort": "medium"}, **extra)
        u = response.usage
        row = {"input": u.input_tokens, "cache_write": u.cache_creation_input_tokens or 0,
               "cache_read": u.cache_read_input_tokens or 0, "output": u.output_tokens}
        for k in totals:
            totals[k] += row[k]
        calls = [b for b in response.content if b.type == "tool_use"]
        action = ", ".join(f"{b.name}" for b in calls) or response.stop_reason
        print(f"{turn:>4} {row['input']:>8,} {row['cache_write']:>8,} {row['cache_read']:>8,} {row['output']:>7,}  {action}")
        messages.append({"role": "assistant", "content": response.content})
        if response.stop_reason != "tool_use":
            break
        results = []
        for b in calls:
            try:
                out = TOOLS[b.name](**b.input)
            except Exception as error:
                out = f"ERROR: {error}"
            results.append({"type": "tool_result", "tool_use_id": b.id, "content": out})
        messages.append({"role": "user", "content": results})

    p_in, p_out, p_read, p_write = PRICES.get(MODEL, PRICES["claude-opus-5-5"])
    cost = (totals["input"] * p_in + totals["output"] * p_out + totals["cache_read"] * p_read
            + totals["cache_write"] * p_write) / 1e6
    answer = "\n".join(b.text for b in response.content if b.type == "text")
    print(f"\nANSWER\n{answer}\n")
    print(f"turns={turn + 1}  input={totals['input']:,}  cache_write={totals['cache_write']:,}  "
          f"cache_read={totals['cache_read']:,}  output={totals['output']:,}  cost≈${cost:.4f}  {time.time() - started:.0f}s")

    os.makedirs(f"{ROOT}/de-lab/reports", exist_ok=True)
    with open(f"{ROOT}/de-lab/reports/token_runs.jsonl", "a") as f:
        f.write(json.dumps({"question": QUESTION, "model": MODEL, "lean": LEAN, "cache": CACHE, "clear_tools": CLEAR,
                            "turns": turn + 1, **totals, "cost_usd": round(cost, 5)}, sort_keys=True) + "\n")


if __name__ == "__main__":
    dry_run() if DRY else main()
