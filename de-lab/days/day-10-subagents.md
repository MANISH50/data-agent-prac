# Day 10 · Subagents: a specialist SQL reviewer with its own context

**Level:** 2 Customize · **Time:** 60 min · **Claude concepts:** subagents (`.claude/agents/*.md`), tool restrictions, model choice per agent, parallel delegation, `/agents`

## Scenario
Reviews keep catching the same business-logic bugs (GST, refunds, city joins). You want a reviewer that knows the business rules deeply, can't edit code, and doesn't clutter your main session's context.

## Goal
Create a `sql-reviewer` subagent and use it on every SQL change.

## Steps to implement
1. Run `/agents` and create a project agent, or copy the reference:
   `mkdir -p .claude/agents && cp de-lab/reference/claude-config/agents/sql-reviewer.md .claude/agents/`
2. Read its frontmatter: `tools: Read, Grep, Glob, Bash` (no Edit/Write, so it can only review) and `model: sonnet`.
3. Write a deliberately buggy query: `Write de-lab/sql/revenue_by_city.sql: revenue per city for September using SUM(amount) and customers.city_id.`
4. Delegate: `Use the sql-reviewer agent to review de-lab/sql/revenue_by_city.sql.` It runs in its **own context window** and returns only its findings.
5. Parallel delegation: `Have sql-reviewer review every .sql file in de-lab/sql and dbt_project/models in parallel, one subagent per folder.`
6. Ask the main session to apply the fixes the reviewer found, then re-review.

## Core learnings
- A subagent is a separate Claude with its own system prompt, tools and context window. The main session only sees its summary, so long investigations don't flood your context.
- Restrict tools to the job: reviewers shouldn't edit; explorers shouldn't run commands.
- The `description` tells the main agent when to delegate ("use proactively after any SQL change").
- Pick cheaper/faster models for narrow, high-volume roles.

## Done when
The reviewer finds both planted bugs in `revenue_by_city.sql` without being told what they are.
