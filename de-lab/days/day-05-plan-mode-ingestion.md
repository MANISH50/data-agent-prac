# Day 5 · Plan mode: design an idempotent ingestion pipeline before writing it

**Level:** 1 Foundations · **Time:** 90 min · **Claude concepts:** plan mode, task lists, iterating on a plan, extended thinking for design work

## Scenario
Now the files must be loaded into `de-lab/lab.duckdb` every day. The loader will be re-run after failures, so it must never double-load, and bad rows must not silently disappear.

## Goal
Use plan mode to agree a design with Claude, then implement `de-lab/pipeline/ingest.py` producing `raw_orders`, `quarantine_orders` and `stg_orders`.

## Steps to implement
1. Enter **plan mode** (`Shift+Tab` until it shows plan mode). Claude can read and think, but not edit.
2. Prompt:
   `Design a loader for de-lab/data/landing/orders into de-lab/lab.duckdb. Requirements: idempotent re-runs, lineage columns (_source_file, _loaded_at), raw layer keeps everything as text, bad rows go to quarantine with a reason, stg is typed and unique on order_id, both timestamp formats parse, status is normalised. Explain the trade-offs (delete+insert per file vs merge).`
3. Challenge the plan before approving: *What happens if the same order appears in two files? What if a file is re-sent with corrections?* Ask Claude to update the plan.
4. Approve the plan. Claude now creates a **task list** and works through it. Watch it tick off tasks.
5. Run it twice. Check that the row counts are identical the second time (idempotency):
   `python de-lab/pipeline/ingest.py && python de-lab/pipeline/ingest.py`
6. Inspect the result in `de-lab/notebooks/02_lab_tables.ipynb`. Reconcile: raw = quarantined + stg + duplicates.
7. Compare with `de-lab/reference/python/ingest_landing.py`.

## Core learnings
- Plan mode separates **thinking** from **doing**: cheap to change a plan, expensive to change code. Use it for anything with design trade-offs.
- Ask Claude to "think hard" or "ultrathink" for difficult design questions; it spends more reasoning on them.
- Data-engineering invariants to always ask for: idempotency, lineage, quarantine (never drop silently), reconciliation counts.

## Done when
Two runs produce the same counts, and every raw row is accounted for.
