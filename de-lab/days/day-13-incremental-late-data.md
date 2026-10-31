# Day 13 · Incremental models and late-arriving data

**Level:** 2 Customize · **Time:** 90 min · **Claude concepts:** large refactors with plan mode, asking Claude for edge cases, verifying with counts before/after, `--continue` / `--resume` sessions

## Scenario
`orders_2026-10-21.csv` contains 30 orders placed on 19 Oct (the app's offline queue flushed late). A full reload every day is getting slow, so the team wants an incremental dbt model, but a naive "only load today's partition" would lose those 30 orders.

## Goal
Build an incremental `fct_orders_daily` in dbt that handles late-arriving rows correctly and is safe to re-run.

## Steps to implement
1. Plan mode: `Design an incremental dbt model over lab stg_orders: daily orders and revenue per city. It must pick up late-arriving rows (order_date older than the load date) and be idempotent. Compare incremental strategies on DuckDB (append, delete+insert, merge) and lookback windows.`
2. Ask for edge cases **before** code: `List the 8 ways this could produce wrong numbers.` Keep the list; it becomes your test plan.
3. Implement. Run a full refresh, record counts per day, then simulate the daily run with only the 21 Oct file and confirm 19 Oct's count went **up** by 30.
4. Re-run twice: counts must not change (idempotency).
5. Session continuity: quit, then `claude --continue` to resume exactly where you left off. Use `claude --resume` to pick an older session.
6. Add a test that compares the incremental model with a full recompute for the last 7 days.

## Core learnings
- Late data is the norm, not the exception. Always ask "what if this arrives tomorrow?".
- Asking Claude for failure modes first produces better code and an instant test plan.
- Before/after counts are the cheapest correctness proof in data engineering. Make Claude show them.
- `--continue` / `--resume` keep long refactors across days without re-explaining context.

## Done when
19 Oct shows the late 30 orders after the incremental run, and incremental = full recompute.
