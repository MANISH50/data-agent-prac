# Day 24 · Context hygiene in Claude Code: long sessions that stay sharp

**Level:** 5 Tokens & context engineering · **Time:** 60 min · **Claude concepts:** `/clear`, `/compact <instructions>`, auto-compaction, subagents as context firewalls, lean `CLAUDE.md`, skills' lazy loading, targeted `@` mentions, `/model`

## Scenario
Three hours into a backfill investigation, Claude starts forgetting the decision you made at 10 am, re-reads files it already read, and responses slow down. The session holds 40 file reads, two huge query outputs and a pasted 800-row CSV.

## Goal
Learn the habits that keep a session's context small and relevant, and measure the difference with `/context`.

## Steps to implement
1. **Pollute on purpose.** In a session, ask Claude to `cat` a full landing CSV and dump `SELECT * FROM orders LIMIT 500`. Run `/context` and note the message tokens.
2. **Compact with intent:** `/compact keep: the decisions about dedup and timestamp parsing, the list of failing files; drop: raw query output`. Run `/context` again.
3. **Start fresh between tasks:** `/clear` when switching from "debug 18 Oct" to "write the menu model". Carry state across via a short note file instead: `Write what we decided to de-lab/reports/session_notes.md`.
4. **Firewall exploration with subagents.** Instead of reading 30 files in the main session: `Use a subagent to find every place revenue is computed in this repo and return a 10-line summary.` Compare `/context` before and after: only the summary lands in your context.
5. **Ask for aggregates, not rows:** `Don't show me rows. Give me counts per file per defect.`
6. **Trim always-loaded context.** Run `context_budget.py`. Move procedures from `CLAUDE.md` into skills (Day 7): a skill's body is loaded only when used.
7. **Pick the model per task** with `/model`: a fast, cheap model for renames and boilerplate; the strongest for design and debugging.

## Core learnings
- Context is a budget, not a bucket. Irrelevant tokens cost money **and** attention: models do worse when the important part is buried.
- `/compact` with explicit "keep / drop" instructions beats automatic compaction for long investigations.
- Subagents are the best context tool you have: they spend tokens in *their* window and return only the conclusion.
- Persist decisions in files (notes, `CLAUDE.md`, plans), not in chat history that will be compacted away.

## Done when
You can run a 2-hour session where `/context` never shows raw data dumps, and decisions survive a `/clear`.
