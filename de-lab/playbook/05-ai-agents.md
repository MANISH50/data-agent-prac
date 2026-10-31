# 5 · AI and agents in production

Problems specific to running Claude (or any LLM) inside data workflows.

---

## Confident wrong answers
**Symptom** The agent says revenue was ₹1.02 crore (the sum of amount), with nice SQL. It's wrong.
**Why** Missing business definitions, ambiguous questions, plausible but wrong joins, no verification step.
**Diagnose** Compare with ground truth (`check_answers.py`); read the SQL, not the prose; check which definition it assumed.
**Fix** Give the definitions (semantic layer, `schema.yml`, `CLAUDE.md`); require SQL + assumptions in every answer; add a self-check step ("does the sum by city equal the total?").
**With Claude** `Answer, then verify your answer with a second independent query and report both.`
**Prevent** Evals with ground truth before every change (Day 21); human review for numbers that go to leadership.
**Practise** The root demo: raw mode vs `--context`.

## Agent loops or stalls
**Symptom** The agent calls the same tool 12 times, or runs until the turn limit.
**Why** Tool errors that aren't informative, tool results too large to read, unclear success criteria, no limit.
**Fix** Clear error messages as tool results; truncated results with guidance ("aggregate instead"); explicit "done when" in the prompt; a turn limit and a task budget.
**With Claude** `Here is the transcript of a run that looped. Identify the turn where it went wrong and change the tool or prompt so it can't happen again.`
**Prevent** Turn limits (`max_turns`), spend caps (`--max-budget-usd`), monitoring of turns per task.

## Token cost blow-up
**Symptom** The agent bill grows faster than usage.
**Why** Context growth per turn, huge tool results, pasted data, no caching, discovery turns, chatty outputs, strongest model for every trivial task.
**Diagnose** Per-turn usage (`token_lab_agent.py`), `/context` and `/cost` in Claude Code, `context_budget.py`.
**Fix** In order: remove waste → cache stable prefixes → batch async work → shorter outputs → tune effort → change model with an eval. See [the cheat sheet](../guides/tokens-and-context.md).
**With Claude** `From de-lab/reports/token_runs.jsonl, find the 3 biggest cost drivers and propose fixes with expected savings.`
**Prevent** Cost per completed task as a tracked metric; budgets on unattended runs.
**Practise** Days 23–28.

## Context overflow
**Symptom** Long sessions get slow and forgetful; an agent hits the context limit mid-job.
**Why** Everything accumulates: file reads, query results, old attempts.
**Fix** Interactive: `/compact` with keep/drop instructions, `/clear` between tasks, subagents for exploration, notes files. Programmatic: context editing, compaction, external memory (tables), chunking.
**With Claude** `Before we continue, write our decisions and open questions to session_notes.md, then I'll /clear.`
**Prevent** Design long jobs as chunks with external state from the start (Day 27).

## Behaviour changes after model upgrades
**Symptom** After switching models, the classifier's category mix shifts or answers get longer.
**Why** Different models follow prompts differently; prompts tuned to an old model; parameters that changed meaning.
**Fix** Pin model ids in config; re-run evals on the new model before switching; adjust prompts and `effort` with measurements.
**With Claude** `Run the eval on both models and show per-case differences, then propose prompt changes for the cases that regressed.`
**Prevent** Model id in one config place; evals in CI for prompt and model changes.

## Rate limits and API errors
**Symptom** 429s during the nightly batch; occasional 5xx; jobs fail at row 4,000 of 10,000.
**Why** Bursty concurrency, no backoff, no checkpointing.
**Fix** The SDK retries 429/5xx with backoff (configurable `max_retries`); limit concurrency; checkpoint progress and resume; use the Batches API for large offline jobs. Check `stop_reason` (`refusal`, `max_tokens`) on every response.
**With Claude** `Make this enrichment job resumable: skip ids already in the output table, cap concurrency at 4, and log failures to a retry table.`
**Prevent** Idempotent, resumable jobs; alert on error rate, not on a single error.
