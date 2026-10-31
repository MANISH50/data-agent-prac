# Day 23 · Measure first: where do the tokens go?

**Level:** 5 Tokens & context engineering · **Time:** 60 min · **Claude concepts:** tokens, context window, `usage` fields, `count_tokens`, `/context` and `/cost` in Claude Code, per-turn re-sending

## Scenario
Finance flags the AI bill: the data agent used for city-head questions costs far more than expected. Nobody knows whether the cost is the model, the prompt, the tools or the number of turns. "Use a cheaper model" is everyone's first guess, and usually the wrong first move.

## Goal
Produce a per-turn token profile of one agent question and a context inventory of the repo, so every later optimisation is measured against a baseline.

## Steps to implement
1. **The mental model.** An agent loop re-sends the *whole* conversation on every turn: system prompt + tool definitions + every previous tool call and result. Turn 8 pays for turns 1–7 again. Output tokens cost ~5× input tokens.
2. **Context inventory (free):** `python de-lab/reference/python/context_budget.py`. Note the size of `CLAUDE.md` and what pasting one landing CSV would cost (~13K tokens).
3. **Size a request without calling the model:** `python de-lab/reference/python/token_lab_agent.py "What was our revenue last month?" --dry-run`. Compare the size of a `describe_table` result with a 100-row `run_sql` result.
4. **Baseline profile (costs a few cents):**
   `python de-lab/reference/python/token_lab_agent.py "What was our revenue last month?"`
   Read the table: input tokens per turn should *grow* every turn. Write down turns, total input, total output and cost in `de-lab/reports/token_journal.md`.
5. **In Claude Code:** run `/context` to see what fills the current session's context window (system, tools, MCP tools, memory files, messages) and `/cost` for the session's spend.
6. Answer in your journal: what share of input was *re-sent history* vs *new information*?

## Core learnings
- Tokens ≈ ¾ of a word for English; SQL and numbers tokenise less efficiently. Measure with `count_tokens`, don't guess.
- `usage` has four numbers that matter: `input_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`, `output_tokens`. Log all four.
- In agent loops, cost grows roughly with **turns × context size**. Fewer turns and smaller tool results usually beat a cheaper model.
- Optimise against a baseline, one change at a time (the Day 21 discipline applied to cost).

## Done when
You have a baseline row (turns, input, output, cost) for 3 questions in `token_journal.md`.
