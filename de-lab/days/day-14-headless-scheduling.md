# Day 14 · Headless Claude: a nightly data-quality job with no human in the loop

**Level:** 3 Automate · **Time:** 60 min · **Claude concepts:** print mode `claude -p`, `--output-format json`, `--allowedTools`, `--permission-mode`, `--max-budget-usd`, cron / scheduled runs, `/loop`

## Scenario
Nobody should have to open a chat window at 6 am to find out that the 20 Oct file never arrived. You want a scheduled job that checks the landing zone, writes an incident report, and costs a few cents.

## Goal
Run Claude Code non-interactively from a shell script, with tightly scoped permissions and a spend cap, on a schedule.

## Steps to implement
1. Try print mode: `claude -p "How many CSV files are in de-lab/data/landing/orders? Answer with a number."`
2. Read `de-lab/reference/nightly_dq_headless.sh`. Note the three safety rails:
   - `--allowedTools` lists the **only** tools it can use unattended (the checker, Read, Write to `de-lab/reports/`)
   - `--max-budget-usd` caps spend
   - the prompt says what not to touch
3. Run it: `bash de-lab/reference/nightly_dq_headless.sh`. Open `de-lab/reports/dq_<date>.md` and the JSON result (it has `result`, `total_cost_usd`, `session_id`).
4. Remove a tool from `--allowedTools` and re-run. See how the run reports it couldn't do the step, instead of hanging on a prompt.
5. Schedule it: `crontab -e` → `15 6 * * * cd /path/to/repo && bash de-lab/reference/nightly_dq_headless.sh`.
6. Inside an interactive session, try `/loop 10m /dq-check` to re-run your skill on an interval while you work.

## Core learnings
- `claude -p` makes Claude Code a **command-line tool**: scriptable, pipeable, schedulable.
- Unattended runs must be least-privilege: explicit allowed tools, a budget, and a narrow prompt. There's no human to click "deny".
- JSON output lets other systems (Slack alerts, Airflow, CI) consume the result.
- Scheduling options grow with you: cron → `/loop` while you work → CI (Day 20) → hosted scheduled agents.

## Done when
A report appears every morning without you, and it flags the missing 20 Oct file.
