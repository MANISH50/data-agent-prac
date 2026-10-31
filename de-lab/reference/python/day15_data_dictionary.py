"""
day15_data_dictionary.py  -  Day 15: your first Claude API call from a pipeline

Scenario: nobody documented the warehouse. Generate a data dictionary (one markdown
section per table) from the real schema and sample rows, and save it to de-lab/docs/.

Concepts: Messages API, system prompt, effort, token counting before you spend,
usage/cost after, stop_reason checks, refusal fallbacks.

RUN IT (from the repo root)
  export ANTHROPIC_API_KEY=...
  python de-lab/reference/python/day15_data_dictionary.py [table ...]
  LAB_MODEL=claude-haiku-5-5 python ...      cheaper model for practice runs
"""
import os
import sys

import anthropic
import duckdb

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
MODEL = os.environ.get("LAB_MODEL", "claude-opus-5-5")
TABLES = sys.argv[1:] or ["cities", "restaurants", "customers", "orders", "order_taxes", "refunds"]

SYSTEM = """You are a senior data engineer writing a data dictionary for a food-delivery warehouse in India.
For the table you are given, write markdown with: a one-line purpose, the grain (what one row is),
a table of columns (name | type | meaning | example), likely join keys, and 'Gotchas' for anything
that looks misleading (units, taxes, statuses, nulls). Only state what the schema and sample rows support;
mark guesses with (assumed)."""

db = duckdb.connect(f"{ROOT}/warehouse.duckdb", read_only=True)
client = anthropic.Anthropic()
os.makedirs(f"{ROOT}/de-lab/docs", exist_ok=True)


def table_context(table):
    columns = db.execute(f"SELECT column_name, column_type FROM (DESCRIBE {table})").fetchall()
    sample = db.execute(f"SELECT * FROM {table} USING SAMPLE 5 ROWS").fetchall()
    stats = db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    return (f"Table: {table}\nRow count: {stats:,}\nColumns:\n"
            + "\n".join(f"- {c} {t}" for c, t in columns)
            + "\nSample rows:\n" + "\n".join(str(r) for r in sample))


total_in = total_out = 0
for table in TABLES:
    messages = [{"role": "user", "content": table_context(table)}]

    # 1. Know the cost before you spend it
    tokens = client.messages.count_tokens(model=MODEL, system=SYSTEM, messages=messages).input_tokens
    print(f"{table}: {tokens} input tokens")

    # 2. The call. Fallbacks: if a safety classifier declines, the API retries on a fallback model.
    response = client.beta.messages.create(
        model=MODEL,
        max_tokens=16000,
        system=SYSTEM,
        messages=messages,
        output_config={"effort": "low"},          # routine documentation work does not need deep thinking
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    )

    # 3. Always check WHY it stopped before trusting the content
    if response.stop_reason == "refusal":
        print(f"  refused: {response.stop_details}")
        continue
    if response.stop_reason == "max_tokens":
        print("  WARNING: output was cut off, raise max_tokens")

    text = "\n".join(b.text for b in response.content if b.type == "text")
    with open(f"{ROOT}/de-lab/docs/{table}.md", "w") as f:
        f.write(text + "\n")
    total_in += response.usage.input_tokens
    total_out += response.usage.output_tokens
    print(f"  wrote de-lab/docs/{table}.md  (in={response.usage.input_tokens}, out={response.usage.output_tokens})")

print(f"\nTotal tokens: input {total_in:,}, output {total_out:,}. Check the price per million tokens for {MODEL}.")
