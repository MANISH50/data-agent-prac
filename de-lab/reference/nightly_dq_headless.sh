#!/usr/bin/env bash
# Day 14: run Claude Code headless (no chat window) as a nightly data-quality job.
#
#   -p                      print mode: run one prompt, print the result, exit
#   --output-format json    machine-readable result (includes the text, cost, session id)
#   --allowedTools          the ONLY tools it may use without asking; nothing else can run unattended
#   --max-budget-usd        hard spend cap so a confused run cannot loop forever
#
# Schedule it with cron (crontab -e):
#   15 6 * * * cd /path/to/data-agent-prac && bash de-lab/reference/nightly_dq_headless.sh
set -euo pipefail
cd "$(dirname "$0")/../.."
mkdir -p de-lab/reports
today=$(date +%F)

claude -p "Run python3 de-lab/reference/python/dq_check.py --json. Write a short markdown incident report to
de-lab/reports/dq_${today}.md: one line per file (PASS/FAIL + reason), missing days, and a recommended action.
Do not change any other file." \
  --allowedTools "Bash(python3 de-lab/reference/python/dq_check.py*)" "Read" "Write(de-lab/reports/**)" \
  --max-budget-usd 0.50 \
  --output-format json > "de-lab/reports/dq_${today}.json"

jq -r '.result' "de-lab/reports/dq_${today}.json"
echo "cost USD: $(jq -r '.total_cost_usd' "de-lab/reports/dq_${today}.json")"
