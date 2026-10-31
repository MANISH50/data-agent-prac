"""
day18_batch_tickets.py  -  Day 18: classify ALL tickets cheaply with Batches + prompt caching

Scenario: Day 16 worked for 20 tickets. Production has thousands per day and nobody is waiting
for the answer in real time. The Message Batches API runs requests asynchronously at 50% of the
price; a cached system prompt (the long classification guide) makes every request cheaper again.

Concepts: Message Batches (create, poll, results keyed by custom_id), prompt caching
(cache_control, cache_read_input_tokens), structured JSON output via output_config.format,
idempotent load of the results.

RUN IT (from the repo root)
  python de-lab/reference/python/day18_batch_tickets.py submit      creates the batch, prints its id
  python de-lab/reference/python/day18_batch_tickets.py collect ID  waits for it, loads results
"""
import json
import os
import sys
import time

import anthropic
import duckdb
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
MODEL = os.environ.get("LAB_MODEL", "claude-opus-5-5")
client = anthropic.Anthropic()

# A long, stable system prompt is what makes caching pay off. Keep it byte-identical across requests:
# no timestamps, no per-ticket text in here. (Below the model's minimum cacheable size it simply won't cache.)
GUIDE = open(f"{ROOT}/de-lab/reference/ticket_classification_guide.md").read()
SCHEMA = {
    "type": "object",
    "properties": {
        "order_id": {"type": ["integer", "null"]},
        "issue_type": {"type": "string", "enum": ["late_delivery", "missing_items", "wrong_order", "food_quality",
                                                    "rider_behaviour", "payment_issue", "other"]},
        "refund_requested": {"type": "boolean"},
        "refund_amount_inr": {"type": ["number", "null"]},
    },
    "required": ["order_id", "issue_type", "refund_requested", "refund_amount_inr"],
    "additionalProperties": False,
}


def submit():
    with open(f"{ROOT}/de-lab/data/landing/support_tickets.jsonl") as f:
        tickets = [json.loads(line) for line in f]
    requests = [
        Request(custom_id=t["ticket_id"], params=MessageCreateParamsNonStreaming(
            model=MODEL,
            max_tokens=2000,
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
            system=[{"type": "text", "text": GUIDE, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": t["body"]}],
        ))
        for t in tickets
    ]
    batch = client.messages.batches.create(requests=requests)
    print(f"Submitted {len(requests)} requests. Batch id: {batch.id}")
    print(f"Collect later with: python {sys.argv[0]} collect {batch.id}")


def collect(batch_id):
    while (batch := client.messages.batches.retrieve(batch_id)).processing_status != "ended":
        print(f"status={batch.processing_status} counts={batch.request_counts}")
        time.sleep(30)

    rows, cache_reads, failed = [], 0, 0
    for item in client.messages.batches.results(batch_id):      # results come in ANY order: key by custom_id
        if item.result.type != "succeeded":
            failed += 1
            continue
        msg = item.result.message
        cache_reads += msg.usage.cache_read_input_tokens or 0
        data = json.loads(next(b.text for b in msg.content if b.type == "text"))
        rows.append((item.custom_id, data["order_id"], data["issue_type"], data["refund_requested"], data["refund_amount_inr"]))

    lab = duckdb.connect(f"{ROOT}/de-lab/lab.duckdb")
    lab.execute("""CREATE TABLE IF NOT EXISTS tickets_batch (ticket_id VARCHAR PRIMARY KEY, order_id BIGINT,
                   issue_type VARCHAR, refund_requested BOOLEAN, refund_amount_inr DECIMAL(10,2))""")
    lab.executemany("INSERT OR REPLACE INTO tickets_batch VALUES (?, ?, ?, ?, ?)", rows)   # idempotent
    print(f"Loaded {len(rows)} rows, {failed} failed, cache-read tokens: {cache_reads:,}")
    print(lab.execute("SELECT issue_type, COUNT(*) FROM tickets_batch GROUP BY 1 ORDER BY 2 DESC").fetchall())


if __name__ == "__main__":
    if sys.argv[1:2] == ["submit"]:
        submit()
    elif sys.argv[1:2] == ["collect"] and len(sys.argv) == 3:
        collect(sys.argv[2])
    else:
        print(__doc__)
