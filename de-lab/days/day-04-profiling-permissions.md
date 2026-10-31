# Day 4 · Profiling new data, and controlling what Claude may run

**Level:** 1 Foundations · **Time:** 60 min · **Claude concepts:** permission prompts, permission modes, `/permissions`, allow/deny rules in `.claude/settings.json`, reviewing diffs

## Scenario
Six new order files (15–21 Oct) landed in `de-lab/data/landing/orders/`. Before anyone loads them, you must know what is wrong with them.

## Goal
Build a reusable data-quality checker `de-lab/pipeline/dq_check.py` with Claude, while learning to control which commands Claude can run unattended.

## Steps to implement
1. Profile first, by hand, in `de-lab/notebooks/01_landing_zone_profiling.ipynb`. Write down what looks odd.
2. Ask Claude to build the checker:
   `Create de-lab/pipeline/dq_check.py. For each landing CSV (read with all_varchar=true) check: schema vs the expected order columns, duplicate order_id, null customer_id, unparseable order_ts, order date different from file date, negative amount, status not in (delivered, cancelled), restaurant_id missing from warehouse restaurants. Also report missing days. Print a table per file and exit 1 on any blocking failure. Support --json.`
3. When Claude asks permission to run `python ...`, read the command before you approve. Choose "don't ask again" only for commands you're happy to run unattended.
4. Run `/permissions` and look at what you allowed. Then make it permanent and shared in `.claude/settings.json`:
   ```json
   { "permissions": {
       "allow": ["Bash(python de-lab/*)", "Bash(python3 de-lab/*)", "Bash(git diff *)"],
       "deny":  ["Read(./.env)", "Bash(rm -rf *)"] } }
   ```
5. Press `Shift+Tab` to cycle permission modes (default → accept edits → plan) and notice the indicator.
6. Compare your output with the answer key in `de-lab/reference/landing_answer_key.md`, and the reference solution `de-lab/reference/python/dq_check.py`.

## Core learnings
- Claude asks before running anything with side effects; **allow rules** remove friction for safe commands, **deny rules** block dangerous ones even when you approve too quickly.
- Settings layers: `~/.claude/settings.json` (you) → `.claude/settings.json` (team, committed) → `.claude/settings.local.json` (you, this repo).
- Accept-edits mode is for when you trust the direction; default mode is for when you want to review every step.
- Read data as text first. Type coercion hides exactly the defects you are looking for.

## Done when
`python de-lab/pipeline/dq_check.py` finds every planted problem (the answer key lists 9 of them) and exits 1.
