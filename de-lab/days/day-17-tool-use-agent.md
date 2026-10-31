# Day 17 · Tool use: build your own data-quality agent

**Level:** 3 Automate · **Time:** 90 min · **Claude concepts:** tool use / function calling, the agent loop, the SDK Tool Runner (`@beta_tool`), tool design, errors as feedback

## Scenario
The Day 4 checker only checks what you thought of. You want an agent that can *investigate*: look at a file, form a hypothesis, query, and come back with a verdict per file: LOAD, LOAD WITH FIX or BLOCK.

## Goal
Build an agent with three small read-only tools and compare it with the hand-written loop in `agent.py`.

## Steps to implement
1. Re-read `agent.py` section 5: the manual loop (call → `tool_use` → run tool → send `tool_result` → repeat).
2. Read `de-lab/reference/python/day17_dq_agent_tool_runner.py`. The tools are plain functions with `@beta_tool`; the schema comes from type hints and the docstring. `client.beta.messages.tool_runner(...)` runs the loop for you.
3. Run it: `python de-lab/reference/python/day17_dq_agent_tool_runner.py "Is orders_2026-10-19.csv safe to load?"`
   Watch the tool calls it chooses.
4. Tool design exercise: `run_sql` only allows SELECT. Ask Claude Code: *what else could go wrong with this tool?* (huge results, slow queries, path traversal in `preview_file`.) Harden one.
5. Add a fourth tool `count_by_day(file_name)` and see whether the agent uses it without prompting.
6. Run the full check: `... "Check all landing files. Which ones are safe to load today?"`. Compare its verdicts with the answer key.

## Core learnings
- An agent = model + tools + loop. The model decides **which** tool; your code decides **what is allowed** and runs it.
- Good tools are small, safe, well-described and return text the model can read. The docstring is the tool's prompt.
- Return errors as tool results: the model reads them and fixes its own mistakes.
- Tool Runner = less boilerplate. A manual loop = full control (approval gates, custom logging). Know both.

## Done when
The agent independently finds the orphan restaurants and upper-case statuses in 19 Oct and gives a verdict for every file.
