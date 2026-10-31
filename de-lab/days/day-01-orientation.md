# Day 1 · Orientation: Claude Code as your onboarding buddy

**Level:** 1 Foundations · **Time:** 45 min · **Claude concepts:** the agentic loop, context, `@` file mentions, asking vs. doing

## Scenario
You joined the data team of an Indian food-delivery company on Monday. There is a DuckDB warehouse, a dbt project, an "agent" demo, and no handover. Your lead wants you to explain the platform in tomorrow's stand-up.

## Goal
Build an accurate mental model of the repo and the warehouse in under an hour **without reading every file yourself**, and verify what Claude tells you.

## Steps to implement
1. Open a terminal in the repo root and start Claude Code: `claude`.
2. Ask broad questions first, so Claude explores on its own:
   - `Explain this repository to a data engineer. What are the moving parts and how does data flow?`
   - `What are the tables in warehouse.duckdb, what is the grain of each, and how do they join?`
3. Narrow down with `@` mentions so Claude reads exactly the file you mean:
   - `@dbt_project/models/marts/fct_orders.sql why is net_revenue defined this way?`
4. Watch what it does: every file read and command run shows up. That is the **agentic loop**: plan → use a tool → read the result → decide again.
5. Verify one claim yourself in `de-lab/notebooks/00_warehouse_tour.ipynb` (for example, the row count of `orders`).
6. Ask Claude to draft your stand-up note: `Write 5 bullets I can say in stand-up about how this platform works.`

## Core learnings
- Claude Code is an **agent**, not a chatbot: it reads files and runs commands to answer, so answers are grounded in *your* repo.
- Start broad, then narrow with `@file`. Vague questions are fine for exploration; precise ones are better for changes.
- Claude automatically reads `CLAUDE.md` at startup: that is why it already knows the revenue rule. You will write your own on Day 2.
- Always verify one number yourself. Trust grows from checking, not from fluent answers.

## Done when
You can draw `cities ──< restaurants ──< orders >── customers` and explain why `SUM(amount)` is not revenue.
