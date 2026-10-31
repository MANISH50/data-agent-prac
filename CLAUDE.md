# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A teaching demo (DataVidhya video "What is a data agent...") of an LLM data agent over a synthetic Indian food-delivery warehouse in DuckDB. The code is deliberately short, heavily commented, and meant to be read on camera — keep that style (plain sectioned scripts, no classes/frameworks, no extra abstraction).

## Commands

```bash
pip install -r requirements.txt                 # duckdb, anthropic, rich
export ANTHROPIC_API_KEY=...

python agent.py "What was our revenue last month?"            # raw tables only
python agent.py "What was our revenue last month?" --context  # + dbt definitions (needs dbt build first)
python agent.py "..." --pause                                 # stop after each step
python chatbot.py "..."                                       # no-tools baseline
python check_answers.py                                       # ground-truth numbers from answers.sql
python explore_warehouse.py [orders|traps|ui]                 # inspect the warehouse
python build_warehouse.py                                     # regenerate warehouse.duckdb (normally never needed)

# dbt (Part 3 / --context mode); always run from dbt_project/ with the local profile
pip install -r requirements-dbt.txt
cd dbt_project && dbt build --profiles-dir .                  # builds models + runs schema.yml tests
dbt test --profiles-dir . --select fct_orders                 # tests for one model
DBT_PROFILES_DIR=. mf query --metrics revenue --group-by metric_time__month
```

There is no linter or unit-test suite; `dbt build` tests and `check_answers.py` are the checks. Model defaults to `claude-sonnet-5-5`, overridable via `DATA_AGENT_MODEL`.

## Architecture

- **`agent.py`** — single-file tool-use loop (max 15 turns) over the Anthropic Messages API. Tools are plain Python functions in the `TOOLS` dict, with matching JSON specs in `TOOL_SPECS` (built by `tool_spec`); both must be updated together. Tool exceptions are returned to Claude as `ERROR: ...` text so it can self-correct. All rendering goes through `show.py` (no logic there; it maps steps to PLAN/LOOK/WRITE/RUN/CHECK/ANSWER boxes and handles `--pause`).
- **Two connection modes:** default opens `warehouse.duckdb` read-only. `--context` opens `dbt_project/analytics.duckdb` (created by `dbt build`, gitignored) and attaches the raw warehouse as `raw`, and adds a `get_business_definitions` tool that returns `models/marts/schema.yml` + `semantic_models.yml` verbatim — so those YAML descriptions are effectively agent prompt content.
- **dbt layering:** `sources.yml` (raw db, attached via `profiles.yml`) → `staging/` views (`stg_orders` relabels refunded orders as `refunded`, joins GST/refunds) → `marts/fct_orders` table with `net_revenue` → MetricFlow metrics in `semantic_models.yml`.

## Invariants that tie files together

- **The traps are intentional.** In raw data, `orders.amount` includes GST and is pre-promo, GST lives in `order_taxes`, refunded orders still say `delivered`, and cancelled orders have amounts. Revenue = delivered and not refunded, minus promo, minus GST — defined *only* in the dbt project. Don't "fix" the raw tables or leak this rule into the raw-mode prompt; the demo depends on the agent failing without context.
- **Fixed "today" = 2026-10-15** (`TODAY` in `agent.py`; also assumed in `answers.sql`, `explore_warehouse.py` and README): last month = Sept 2026, last week = 5–11 Oct 2026. Data runs 2026-04-01 to 2026-10-14.
- **Data is deterministic** (seeds 7 and 1007 in `build_warehouse.py`). README quotes exact answers (Mumbai Sept orders 6,171; Sept revenue ₹78,09,309; Mumbai rain-week drop). Changing the generator, seeds or `RAIN_DAYS` changes these and requires updating `answers.sql` and README. `warehouse.duckdb` is committed as a binary.
- **Read-only access.** Every connection to `warehouse.duckdb` is read-only so the agent, explorer UI and dbt can run at the same time. Avoid `duckdb -ui warehouse.duckdb` (takes a write lock).
- `check_answers.py` splits `answers.sql` on `;` and needs each query to have a `-- Q...` title comment line.
- `de-lab/` is a 28-day practice curriculum plus a field guide (`de-lab/playbook/`) built on this demo (see `de-lab/README.md`). It writes only to `de-lab/lab.duckdb` (git-ignored); its landing data is generated deterministically by `de-lab/scripts/make_landing_data.py` and its notebooks by `de-lab/scripts/build_notebooks.py --execute`. `de-lab/reference/` holds solutions and example Claude config (hooks, skill, subagent) that is intentionally *not* active until copied into `.claude/`.
- `mcp/` is the no-code variant (Claude Desktop + `mcp-server-motherduck` via `uvx`); the config path placeholder must be replaced with an absolute path.
