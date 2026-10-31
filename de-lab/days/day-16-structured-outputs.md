# Day 16 · Structured outputs: free text → typed table

**Level:** 3 Automate · **Time:** 75 min · **Claude concepts:** structured outputs (`client.messages.parse` + Pydantic, `output_config.format` JSON schema), enums, validation against your own data

## Scenario
Finance wants refund liability per issue type. The data is 300 support tickets in `support_tickets.jsonl`, free text, some in Hinglish: *"bhai order #270363 me paneer missing tha!! please refund 297"*.

## Goal
Extract `order_id, issue_type, refund_requested, refund_amount_inr, sentiment` from every ticket into `lab.duckdb.tickets_structured`, with values guaranteed to match the schema.

## Steps to implement
1. Look at the data in notebook `01_landing_zone_profiling.ipynb` (last cell).
2. Define the target as a Pydantic model with an `Enum` for `issue_type` (see `de-lab/reference/python/day16_structured_tickets.py`).
3. Call `client.messages.parse(..., output_format=Ticket)` and use `response.parsed_output`: a validated object, no JSON parsing or regex.
4. Run on 20 tickets: `python de-lab/reference/python/day16_structured_tickets.py 20`.
5. **Verify against your data:** does every extracted `order_id` exist in `stg_orders` or the warehouse? The script writes `order_exists`. Investigate the `False` rows: some tickets are about orders from the missing 20 Oct file.
6. Spot-check 10 rows by hand. Read `de-lab/reference/ticket_classification_guide.md` and decide whether a longer guide improves accuracy (you'll use it tomorrow).

## Core learnings
- Structured outputs guarantee **shape** (valid JSON, right types, allowed enum values), not **truth**. Always validate facts against your own tables.
- Enums turn fuzzy categories into a controlled vocabulary your dashboards can rely on.
- "Never invent an id" in the prompt plus `Optional[int]` in the schema gives the model a legal way to say "not present".
- LLM output is just another source: give it lineage, tests and quarantine like any feed.

## Done when
`tickets_structured` has 20 typed rows and you know which order ids could not be verified, and why.
