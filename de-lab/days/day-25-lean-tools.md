# Day 25 · Lean tools and prompts: cut tokens per question without losing accuracy

**Level:** 5 Tokens & context engineering · **Time:** 75 min · **Claude concepts:** tool result size, tool description cost, schema-up-front vs discovery, aggregation push-down, truncation notes, accuracy vs tokens trade-off

## Scenario
Your Day 23 profile shows the agent spends 3–4 turns discovering tables, and every `run_sql` returns up to 50 rows the model mostly ignores. Those rows are then re-sent on every later turn.

## Goal
Make the agent answer the same questions in fewer turns and fewer tokens, **with the Day 21 eval score unchanged or better**.

## Steps to implement
1. Read the `--lean` branches in `de-lab/reference/python/token_lab_agent.py`:
   - **schema digest in the system prompt**: one deterministic line per table, so no `list_tables`/`describe_table` turns
   - **known business rules up front** (revenue, city join), the same idea as `agent.py --context`, in 3 lines
   - results capped at 20 rows with a note telling the model to **aggregate in SQL** instead of reading rows
   - shorter tool descriptions, fewer tools (tool definitions are sent on every turn too)
2. Compare: `python ... "What was our revenue last month?"` vs the same with `--lean`. Record turns, input, output, cost, and whether the number is correct.
3. Run 3 more questions both ways (Mumbai orders, Delhi cancellations, Bengaluru AOV). Put a table in `token_journal.md`.
4. Find the limit: cap results at 5 rows. Does accuracy drop? Where is the sweet spot?
5. Apply one lean idea to `agent.py` itself, and re-run the Day 21 eval to prove you didn't break it.

## Core learnings
- The cheapest token is the one you never send. **Push computation into SQL**: return aggregates, not rows.
- Discovery turns are expensive because every turn re-sends everything. Small, stable reference information (schema, key rules) belongs in the system prompt.
- Truncate tool output, but say so: "more rows not shown, aggregate instead" lets the model recover.
- Every optimisation needs an accuracy check. Lean but wrong is worse than expensive but right.

## Done when
Your journal shows lean mode with fewer turns and fewer tokens per question, and the same eval score.
