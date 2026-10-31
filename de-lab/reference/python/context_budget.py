"""
context_budget.py  -  Day 23: what does every request carry before the user even asks?

Lists the context sources in this repo (memory files, dbt docs the agent reads, tool
definitions, ...), their token size, and their share of the context window. With an API key
it uses the exact count_tokens endpoint (free to call); without one it estimates ~4 chars/token.

RUN IT (from the repo root)
  python de-lab/reference/python/context_budget.py
  python de-lab/reference/python/context_budget.py path/to/extra_file.md ...
"""
import glob
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
MODEL = os.environ.get("LAB_MODEL", "claude-opus-5-5")
WINDOW = 1_000_000                   # context window of current models; check the Models API for yours

SOURCES = {
    "CLAUDE.md (root, every Claude Code session)": ["CLAUDE.md"],
    "de-lab/CLAUDE.md (nested, when working in de-lab)": ["de-lab/CLAUDE.md"],
    "Skills (only frontmatter until used)": glob.glob(f"{ROOT}/.claude/skills/*/SKILL.md"),
    "agent.py --context: schema.yml + semantic_models.yml": ["dbt_project/models/marts/schema.yml",
                                                            "dbt_project/models/marts/semantic_models.yml"],
    "Ticket classification guide (Day 18 system prompt)": ["de-lab/reference/ticket_classification_guide.md"],
    "One landing CSV, if someone pastes it whole": ["de-lab/data/landing/orders/orders_2026-10-15.csv"],
}
for extra in sys.argv[1:]:
    SOURCES[extra] = [extra]

client = None
if os.environ.get("ANTHROPIC_API_KEY"):
    import anthropic
    client = anthropic.Anthropic()


def count(text):
    if not text:
        return 0
    if client:
        return client.messages.count_tokens(model=MODEL, messages=[{"role": "user", "content": text}]).input_tokens
    return len(text) // 4


print(f"{'source':55} {'tokens':>9} {'% window':>9}   ({'exact' if client else 'estimated'}, {MODEL})")
for label, paths in SOURCES.items():
    text = ""
    for p in paths:
        full = p if os.path.isabs(p) else os.path.join(ROOT, p)
        if os.path.exists(full):
            text += open(full, encoding="utf-8", errors="replace").read()
    tokens = count(text)
    note = "" if text else "  (not created yet)"
    print(f"{label:55} {tokens:>9,} {100 * tokens / WINDOW:>8.2f}%{note}")

print("""
How to read this:
- Everything in a request is re-sent on every turn of an agent loop. A 2,000-token memory file in a
  20-turn session is ~40,000 input tokens, unless it is cached.
- Pasting raw data is the most expensive habit: summarise or query it instead.
- Skills cost almost nothing until used; CLAUDE.md is loaded every session, so keep it short.""")
