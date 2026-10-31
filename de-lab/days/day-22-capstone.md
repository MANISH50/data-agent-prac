# Day 22 · Capstone: the autonomous data on-call

**Level:** 4 Production agents · **Time:** half a day · **Claude concepts:** everything: memory, skills, hooks, subagents, MCP, headless, API, structured outputs, Agent SDK, CI, evals

## Scenario
It's Monday, 22 Oct. Over the weekend: the 20 Oct file never arrived, 18 Oct drifted, 19 Oct has orphans, tickets are piling up. Design the system so that next weekend **no human is needed** until there's a decision to make.

## Goal
An end-to-end, scheduled, least-privilege workflow that detects, fixes what's safe, escalates what isn't, and leaves an audit trail.

## Steps to implement
1. **Design first (plan mode).** Ask Claude to draw the architecture with you:
   detect (Day 14 headless job + Day 4 checker) → diagnose (Day 17/19 agent) → fix safe issues on a branch (Day 19) → open a PR reviewed in CI (Day 20) → classify tickets for the affected orders (Day 18) → incident note.
2. **Decide the autonomy boundary.** Write in `de-lab/CLAUDE.md` what the system may do alone (quarantine rows, map known renames, open PRs) and what needs a human (merging, deleting data, contacting partners).
3. **Enforce it.** Hooks (Day 9) block anything outside the boundary; `allowed_tools` and `permission_mode` restrict the SDK agent.
4. **Build it.** Use subagents in parallel: one for the detector, one for the doctor, one for the ticket job. Review each with `sql-reviewer`.
5. **Measure it.** Extend the eval (Day 21) with incident scenarios: regenerate landing data, break it in a known way, check the system's verdicts.
6. **Run a fire drill.** Delete `de-lab/lab.duckdb`, regenerate the landing files, run the whole thing from cron. Time it, cost it.
7. Write a one-page runbook: what runs when, what it costs, how to stop it, who gets paged.

## Core learnings
- Real automation = **deterministic scaffolding** (schedules, checks, tests, hooks) + **agentic steps** where judgement is needed.
- The autonomy boundary is a product decision. Write it down, then enforce it in code.
- Every autonomous action needs an audit trail: branch, PR, report, cost.
- Where to go next: hosted agents that run on Anthropic's infrastructure on a schedule (Claude Managed Agents), MCP servers for your real systems (Postgres, Airflow, dbt Cloud), and evals in CI.

## Done when
A fresh fire drill ends with: a PR fixing the drift, a quarantine summary, classified tickets, an incident note, and no human action until review.
