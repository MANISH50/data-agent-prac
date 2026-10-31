#!/usr/bin/env bash
# PostToolUse hook (Day 9): after Claude edits a dbt model or YAML, run `dbt parse`
# so broken Jinja/YAML is caught immediately. A PostToolUse hook cannot undo the edit,
# but exit code 2 shows stderr to Claude, which then fixes its own mistake.
file=$(jq -r '.tool_input.file_path // empty')
case "$file" in
  */dbt_project/*.sql|*/dbt_project/*.yml)
    cd "$CLAUDE_PROJECT_DIR/dbt_project" || exit 0
    if ! out=$(dbt parse --profiles-dir . 2>&1); then
      echo "dbt parse failed after editing $file:" >&2
      echo "$out" | tail -20 >&2
      exit 2
    fi
    ;;
esac
exit 0
