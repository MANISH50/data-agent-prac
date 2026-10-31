#!/usr/bin/env python3
"""
PreToolUse hook (Day 9): stop Claude from damaging the production warehouse.

Claude Code sends the pending tool call as JSON on stdin. If we exit with code 2,
the call is blocked and whatever we print to stderr is shown to Claude as the reason,
so it can change course. Exit 0 lets the normal permission flow continue.

Blocks:
  - any Write/Edit/Bash that targets warehouse.duckdb (the raw warehouse is read-only)
  - destructive SQL (DROP / TRUNCATE / DELETE without WHERE) in a Bash command
"""
import json
import re
import sys

event = json.load(sys.stdin)
tool = event.get("tool_name", "")
tool_input = event.get("tool_input", {})

if tool in ("Write", "Edit") and tool_input.get("file_path", "").endswith("warehouse.duckdb"):
    print("Blocked: warehouse.duckdb is the read-only source of truth. Write to de-lab/lab.duckdb instead.",
          file=sys.stderr)
    sys.exit(2)

if tool == "Bash":
    command = tool_input.get("command", "")
    if re.search(r"\b(rm|mv|cp)\b[^|;&]*warehouse\.duckdb", command):
        print("Blocked: do not move, copy over or delete warehouse.duckdb.", file=sys.stderr)
        sys.exit(2)
    if re.search(r"\b(DROP|TRUNCATE)\s+(TABLE|SCHEMA|DATABASE)\b", command, re.IGNORECASE):
        print("Blocked: destructive DDL. Ask the user before dropping objects.", file=sys.stderr)
        sys.exit(2)
    if re.search(r"\bDELETE\s+FROM\s+\w+\s*(;|\"|'|$)", command, re.IGNORECASE):
        print("Blocked: DELETE without a WHERE clause.", file=sys.stderr)
        sys.exit(2)

sys.exit(0)
