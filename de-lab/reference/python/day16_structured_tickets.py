"""
day16_structured_tickets.py  -  Day 16: turn free text into a typed table (structured outputs)

Scenario: support tickets arrive as free text (English + Hinglish). The finance team wants a table:
ticket_id, order_id, issue_type, refund_requested, refund_amount, sentiment.

Concepts: structured outputs with a Pydantic schema (client.messages.parse), enums to control
categories, validating Claude's output against your own data (does the order exist?), loading
LLM output into DuckDB like any other source.

RUN IT (from the repo root)
  python de-lab/reference/python/day16_structured_tickets.py 20      first 20 tickets
"""
import json
import os
import sys
from enum import Enum
from typing import Optional

import anthropic
import duckdb
from pydantic import BaseModel, Field

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
MODEL = os.environ.get("LAB_MODEL", "claude-opus-5-5")
LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 20


class IssueType(str, Enum):
    late_delivery = "late_delivery"
    missing_items = "missing_items"
    wrong_order = "wrong_order"
    food_quality = "food_quality"
    rider_behaviour = "rider_behaviour"
    payment_issue = "payment_issue"
    other = "other"


class Ticket(BaseModel):
    order_id: Optional[int] = Field(description="The order id mentioned in the text, or null if none")
    issue_type: IssueType
    refund_requested: bool
    refund_amount_inr: Optional[float] = Field(description="Amount the customer asks for, null if not stated")
    sentiment: int = Field(description="1 = very angry ... 5 = calm")


client = anthropic.Anthropic()
lab = duckdb.connect(f"{ROOT}/de-lab/lab.duckdb")
lab.execute(f"ATTACH IF NOT EXISTS '{ROOT}/warehouse.duckdb' AS wh (READ_ONLY)")
known_orders = {r[0] for r in lab.execute(
    "SELECT order_id FROM stg_orders UNION SELECT order_id FROM wh.orders").fetchall()} \
    if lab.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'stg_orders'").fetchone()[0] \
    else set()

rows = []
with open(f"{ROOT}/de-lab/data/landing/support_tickets.jsonl") as f:
    tickets = [json.loads(line) for line in f][:LIMIT]

for t in tickets:
    response = client.messages.parse(
        model=MODEL,
        max_tokens=4000,
        system="Extract fields from a food-delivery support ticket. Text may be Hinglish. Never invent an order id.",
        messages=[{"role": "user", "content": t["body"]}],
        output_format=Ticket,
    )
    if response.stop_reason != "end_turn" or response.parsed_output is None:
        print(f"{t['ticket_id']}: skipped (stop_reason={response.stop_reason})")
        continue
    x = response.parsed_output
    order_known = x.order_id in known_orders if x.order_id else None    # never trust, always verify
    rows.append((t["ticket_id"], t["created_at"], x.order_id, x.issue_type.value, x.refund_requested,
                 x.refund_amount_inr, x.sentiment, order_known))
    print(f"{t['ticket_id']}: {x.issue_type.value:15} order={x.order_id} refund={x.refund_amount_inr} known={order_known}")

lab.execute("""CREATE OR REPLACE TABLE tickets_structured (ticket_id VARCHAR, created_at TIMESTAMP, order_id BIGINT,
               issue_type VARCHAR, refund_requested BOOLEAN, refund_amount_inr DECIMAL(10,2), sentiment INTEGER,
               order_exists BOOLEAN)""")
lab.executemany("INSERT INTO tickets_structured VALUES (?, ?, ?, ?, ?, ?, ?, ?)", rows)
print(lab.execute("SELECT issue_type, COUNT(*), SUM(refund_amount_inr) FROM tickets_structured GROUP BY 1 ORDER BY 2 DESC").fetchall())
