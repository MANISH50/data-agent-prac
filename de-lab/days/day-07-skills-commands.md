# Day 7 · Skills and slash commands: package your repeatable work

**Level:** 2 Customize · **Time:** 60 min · **Claude concepts:** skills (`.claude/skills/<name>/SKILL.md`), custom slash commands (`.claude/commands/*.md`), `$ARGUMENTS`, frontmatter `description`

## Scenario
Every morning you type the same long prompt: "check the new landing files for duplicates, nulls, bad timestamps…". Your teammate types a slightly different one and misses half the checks.

## Goal
Turn the morning checks into a team skill `/dq-check` and a `/daily-standup` command that anyone on the team gets by pulling the repo.

## Steps to implement
1. Create the skill:
   `mkdir -p .claude/skills/dq-check` and ask Claude to write `.claude/skills/dq-check/SKILL.md` with frontmatter `name` and `description`, and a body listing the checks and the report format. (Reference: `de-lab/reference/claude-config/skills/dq-check/SKILL.md`.)
2. Restart Claude Code. Run `/dq-check de-lab/data/landing/orders/orders_2026-10-19.csv`.
3. Test **automatic** use: in a fresh session ask `Is the 17 Oct file OK to load?` without naming the skill. Claude picks it because the `description` matches. If it doesn't, sharpen the description.
4. Create a simple command: copy `de-lab/reference/claude-config/commands/daily-standup.md` to `.claude/commands/` and run `/daily-standup blocked on schema drift`.
5. Commit `.claude/skills` and `.claude/commands` so the whole team gets them.

## Core learnings
- A **skill** is a folder with instructions (plus optional scripts or reference files) that Claude loads **only when relevant**, so it costs nothing until used. The `description` decides when it triggers.
- A **slash command** is a saved prompt you call by name; `$ARGUMENTS` receives what you type after it.
- Skills turn tribal knowledge into versioned, reviewable team assets. Put the "how we do X here" in skills and the "facts about this repo" in `CLAUDE.md`.

## Done when
`/dq-check` gives the same report format for you and your teammate, and Claude uses it without being asked.
