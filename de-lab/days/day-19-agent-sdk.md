# Day 19 · The Claude Agent SDK: embed Claude Code in your own pipeline tools

**Level:** 4 Production agents · **Time:** 90 min · **Claude concepts:** Agent SDK `query()`, `ClaudeAgentOptions`, built-in tools, custom tools via in-process MCP (`@tool`, `create_sdk_mcp_server`), `permission_mode`, `ResultMessage` cost

## Scenario
On-call is repetitive: the load breaks, someone runs the checker, patches the loader, re-runs, writes an incident note. You want a "pipeline doctor" program that does this, with exactly the permissions you choose.

## Goal
Build an agent with the Agent SDK that diagnoses the landing load, edits the loader in `de-lab/pipeline/`, re-runs it and writes an incident note.

## Steps to implement
1. `pip install claude-agent-sdk` (it uses the Claude Code CLI under the hood).
2. Read `de-lab/reference/python/day19_pipeline_doctor_agent_sdk.py`:
   - two custom tools (`run_dq_check`, `lab_row_counts`) bundled with `create_sdk_mcp_server`
   - tools are named `mcp__lab__run_dq_check`: `mcp__<server key>__<tool>`
   - `allowed_tools` lists what may run; `permission_mode="dontAsk"` refuses everything else instead of prompting
   - `cwd`, `system_prompt`, `max_turns`
3. Break the loader on purpose (remove the `order_amount` rename in your `de-lab/pipeline/ingest.py`).
4. Run the doctor: `python de-lab/reference/python/day19_pipeline_doctor_agent_sdk.py`. Watch it find and fix the drift.
5. Check `git diff`: did it change only what it should? Did it touch the landing files? (The guard hook from Day 9 still applies if it's in `.claude/settings.json`.)
6. Print `ResultMessage.total_cost_usd` and `num_turns`. Make a cost-per-incident note.

## Core learnings
- **Tool Runner (Day 17)** = you write every tool. **Agent SDK** = Claude Code's built-in tools (Read, Edit, Bash, Grep...), loop, context management and permissions, as a library.
- Custom tools are just MCP: the same tools could be served to Claude Desktop or Claude Code.
- An autonomous agent must be least-privilege by construction: explicit allowed tools, path-scoped Bash, a turn limit.
- Always review the diff of an autonomous run before merging.

## Done when
The doctor fixes the broken loader, proves it with row counts, and writes an incident note, in one command.
