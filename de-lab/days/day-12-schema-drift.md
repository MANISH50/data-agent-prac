# Day 12 · Debugging a broken pipeline: schema drift

**Level:** 2 Customize · **Time:** 60 min · **Claude concepts:** feeding errors and logs to Claude, root-cause before fix, piping input (`cat log | claude -p`), asking for a regression test

## Scenario
6:30 am alert: the loader failed on `orders_2026-10-18.csv`. Upstream renamed `amount` → `order_amount` and added `delivery_fee` without telling anyone. Dashboards for 18 Oct are empty.

## Goal
Find the root cause, make the loader handle known renames, keep unknown new columns instead of dropping them, and add a test so this is caught next time.

## Steps to implement
1. Reproduce: make your loader strict (fail on unexpected columns) and run it. Save the error: `python de-lab/pipeline/ingest.py 2> de-lab/reports/ingest_error.log`.
2. Give Claude the evidence, not your theory:
   `cat de-lab/reports/ingest_error.log | claude -p "Explain the root cause of this pipeline failure in 3 lines"`
3. In an interactive session: `Fix the loader: map known renames from a RENAMES dict (order_amount -> amount), store unknown extra columns as JSON in _extra, and fail loudly if a required column is missing. Then add a regression test with a tiny drifted CSV fixture.`
4. Ask Claude to explain the trade-off: *map silently vs fail vs quarantine the whole file.* Decide and write the decision into `de-lab/CLAUDE.md`.
5. Re-run the loader and confirm 18 Oct now has ~823 rows in `stg_orders`, and `_extra` holds `delivery_fee`.

## Core learnings
- Paste the real error and data, not a paraphrase. Claude is much better with evidence.
- Ask for root cause first, fix second. A fix without a diagnosis tends to be a workaround.
- `claude -p` reads from stdin: useful for one-off log analysis in scripts.
- Every incident should end with a regression test and a written decision.

## Done when
The drifted file loads, a missing required column still fails loudly, and the test passes.
