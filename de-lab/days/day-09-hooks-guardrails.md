# Day 9 · Hooks: guardrails that always run

**Level:** 2 Customize · **Time:** 75 min · **Claude concepts:** hooks (`PreToolUse`, `PostToolUse`, `Stop`, `SessionStart`), matchers, exit code 2, `$CLAUDE_PROJECT_DIR`

## Scenario
A colleague's session ran `DELETE FROM stg_orders` while "cleaning up". Another session edited a dbt model and left broken Jinja that only failed in the nightly run. `CLAUDE.md` rules are advice; you need enforcement.

## Goal
Add two hooks: one that **blocks** destructive actions on the warehouse, one that **validates** dbt files right after Claude edits them.

## Steps to implement
1. Copy the reference hooks:
   ```bash
   mkdir -p .claude/hooks
   cp de-lab/reference/claude-config/hooks/* .claude/hooks/
   ```
2. Read `guard_warehouse.py`. A hook receives the pending tool call as JSON on stdin (`tool_name`, `tool_input`). Exit **2** blocks the call and shows stderr to Claude; exit 0 lets it continue.
3. Test it without Claude:
   ```bash
   echo '{"tool_name":"Bash","tool_input":{"command":"rm warehouse.duckdb"}}' | python3 .claude/hooks/guard_warehouse.py; echo $?
   ```
4. Register both hooks in `.claude/settings.json` (merge the `hooks` block from `de-lab/reference/claude-config/settings.json`).
5. Start Claude and try to break things: `Delete all rows from stg_orders in de-lab/lab.duckdb.` Watch the block, and how Claude adapts.
6. Ask Claude to introduce a typo in `fct_orders.sql`. The `PostToolUse` hook runs `dbt parse` and feeds the error back; Claude fixes it on its own.
7. Stretch: add a `SessionStart` hook that prints today's landing files, so every session starts with fresh context.

## Core learnings
- Hooks are **deterministic**: they run every time, whatever the model decides. Use them for rules that must never break.
- `PreToolUse` = gate (block or allow). `PostToolUse` = check and give feedback. `Stop` = "don't finish until tests pass". `SessionStart` = inject context.
- Matchers select tools: `"Bash"`, `"Write|Edit"`, `"mcp__lab__.*"`.
- Keep hooks fast and simple. They run on every matching call.

## Done when
Destructive commands are blocked with a clear reason, and a broken dbt edit is auto-detected and fixed.
