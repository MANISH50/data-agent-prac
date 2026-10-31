# Day 21 · Evals: measure your agent instead of trusting it

**Level:** 4 Production agents · **Time:** 75 min · **Claude concepts:** evals, ground truth, comparing variants (prompt / context / model / effort), regression testing for prompts

## Scenario
Your manager asks: *"Is the data agent good enough to give to the city heads?"* "It seemed fine when I tried it" is not an answer. Neither is a single demo.

## Goal
Build a small eval that scores `agent.py` against SQL ground truth in raw mode and `--context` mode, and use it to decide what to ship.

## Steps to implement
1. Build the dbt context first: `cd dbt_project && dbt build --profiles-dir . && cd ..`.
2. Read `de-lab/reference/python/day21_eval_agent.py`: each case = a question + the SQL that computes the true answer; the agent's first number after `ANSWER` is compared within 0.1%.
3. Start cheap: `python de-lab/reference/python/day21_eval_agent.py --limit 1` (every run costs tokens).
4. Run the full eval. Expect raw mode to fail the revenue and AOV questions and `--context` mode to pass them. That is the whole point of the demo, now measured.
5. Add 5 cases of your own (e.g. refund rate per city, cancellation rate in the Mumbai rain week). Write the truth SQL first, verify it with `check_answers.py`-style SQL.
6. Change one thing at a time (system prompt, model via `DATA_AGENT_MODEL`, a new tool) and re-run. Keep a results table in `de-lab/reports/evals.md`.

## Core learnings
- An eval is a fixed question set with known answers, run the same way every time. It turns "feels better" into a number.
- Your warehouse is the perfect ground-truth source: SQL is cheap and exact.
- Change one variable per run; otherwise you can't tell what helped.
- Evals are regression tests for prompts. Run them before shipping any prompt or model change.

## Done when
You can say "raw: x/8, with context: y/8" and justify which version to ship.
