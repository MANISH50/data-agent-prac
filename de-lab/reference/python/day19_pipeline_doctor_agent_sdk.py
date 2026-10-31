"""
day19_pipeline_doctor_agent_sdk.py  -  Day 19: a pipeline-repair agent with the Claude Agent SDK

Scenario: the nightly load failed (schema drift, bad rows). Instead of a chat assistant, you embed
Claude Code itself in your own program: it can read files, run the checker, edit the loader and
re-run it, but only with the tools and permissions you grant.

Day 17 used the Tool Runner: YOU wrote every tool. The Agent SDK ships Claude Code's built-in
tools (Read, Edit, Bash, Grep, Glob...) plus the same agent loop, context management and
permissions. You add your own tools as an in-process MCP server.

Concepts: query(), ClaudeAgentOptions (allowed_tools, permission_mode, cwd, max_turns,
system_prompt), custom tools with @tool + create_sdk_mcp_server, mcp__<server>__<tool> naming,
reading ResultMessage for cost and outcome.

RUN IT (from the repo root)
  pip install claude-agent-sdk
  python de-lab/reference/python/day19_pipeline_doctor_agent_sdk.py
"""
import asyncio
import json
import os
import subprocess
from typing import Any

from claude_agent_sdk import (AssistantMessage, ClaudeAgentOptions, ResultMessage, TextBlock,
                              create_sdk_mcp_server, query, tool)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


@tool("run_dq_check", "Run the data-quality checker on all landing files and return its JSON report", {})
async def run_dq_check(args: dict[str, Any]) -> dict[str, Any]:
    out = subprocess.run(["python3", "de-lab/reference/python/dq_check.py", "--json"],
                         cwd=ROOT, capture_output=True, text=True)
    return {"content": [{"type": "text", "text": out.stdout[-15000:] or out.stderr}]}


@tool("lab_row_counts", "Row counts of raw_orders, quarantine_orders and stg_orders in de-lab/lab.duckdb", {})
async def lab_row_counts(args: dict[str, Any]) -> dict[str, Any]:
    import duckdb
    try:
        db = duckdb.connect(f"{ROOT}/de-lab/lab.duckdb", read_only=True)
        counts = {t: db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                  for t in ["raw_orders", "quarantine_orders", "stg_orders"]}
        return {"content": [{"type": "text", "text": json.dumps(counts)}]}
    except Exception as error:
        return {"content": [{"type": "text", "text": f"ERROR: {error}"}], "is_error": True}


lab_tools = create_sdk_mcp_server(name="lab", version="1.0.0", tools=[run_dq_check, lab_row_counts])

options = ClaudeAgentOptions(
    cwd=ROOT,
    system_prompt=("You are the data platform on-call engineer. Diagnose why the landing load is unhealthy, "
                   "fix the loader in de-lab/pipeline/ingest.py (create it from de-lab/reference/python/ingest_landing.py "
                   "if missing), re-run it and prove the fix with row counts. Never modify warehouse.duckdb or the "
                   "landing files. Finish with a short incident note: cause, fix, rows quarantined, follow-ups."),
    mcp_servers={"lab": lab_tools},
    # Auto-approved tools. Everything else is refused because of permission_mode="dontAsk".
    allowed_tools=["Read", "Grep", "Glob", "Edit", "Write",
                   "Bash(python3 de-lab/*)", "Bash(python de-lab/*)",
                   "mcp__lab__run_dq_check", "mcp__lab__lab_row_counts"],
    permission_mode="dontAsk",
    max_turns=30,
)


async def main():
    prompt = "Last night's landing load looks wrong. Investigate, fix and report."
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)
        elif isinstance(message, ResultMessage):
            print(f"\n--- done: {message.subtype}, turns={message.num_turns}, cost=${message.total_cost_usd}")


asyncio.run(main())
