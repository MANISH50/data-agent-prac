# Day 11 · MCP: connect Claude to your data systems

**Level:** 2 Customize · **Time:** 60 min · **Claude concepts:** Model Context Protocol, `claude mcp add`, scopes (local / project `.mcp.json` / user), MCP tool naming `mcp__<server>__<tool>`, permissions on MCP tools

## Scenario
Running Python snippets to query DuckDB works, but it is clumsy. Your company also has Postgres, a BI tool and an issue tracker. MCP is the standard way to plug systems like these into Claude as tools.

## Goal
Connect the warehouse to Claude Code through the DuckDB/MotherDuck MCP server and use it for analysis, read-only.

## Steps to implement
1. Make sure `uvx` works (`pip install uv` or https://docs.astral.sh/uv/).
2. Add the server at **project** scope so the team shares it (writes `.mcp.json`):
   ```bash
   claude mcp add lab-duckdb --scope project -- uvx mcp-server-motherduck --db-path ./warehouse.duckdb
   ```
   (Compare with `de-lab/reference/claude-config/mcp.json`, and `mcp/` for the Claude Desktop version.)
3. In Claude, run `/mcp` to see the server and its tools.
4. Ask: `Using the lab-duckdb tools, which cuisine has the highest refund rate?` Note the tool names in the transcript: `mcp__lab-duckdb__...`.
5. Allow its read tools without prompts by adding `"mcp__lab-duckdb__*"`-style entries to `permissions.allow` (check the exact tool names in `/mcp`).
6. Discuss with Claude: *What other MCP servers would help our team?* (Postgres, GitHub, Slack, Jira, dbt Cloud...) Browse what exists before building your own.

## Core learnings
- MCP turns any system into tools Claude can call, with a standard protocol. Write a server once, use it from Claude Code, Claude Desktop, the Agent SDK and the API.
- Scope matters: `local` (just you), `project` (`.mcp.json`, committed), `user` (all your projects).
- MCP tools obey the same permission system and hooks as built-in tools. Matcher `mcp__lab-duckdb__.*` works in hooks.
- Prefer read-only connections for production data.

## Done when
Claude answers a warehouse question using only MCP tools, without writing Python.
