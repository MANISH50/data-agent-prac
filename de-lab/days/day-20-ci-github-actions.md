# Day 20 · Claude in CI: automated dbt reviews on every pull request

**Level:** 4 Production agents · **Time:** 75 min · **Claude concepts:** Claude Code GitHub Actions (`anthropics/claude-code-action`), `@claude` mentions on PRs, `/install-github-app`, secrets, CI permissions

## Scenario
Reviews are the bottleneck: dbt PRs wait a day for a senior engineer, who mostly repeats the same comments (refunds, GST, missing tests). You want every PR reviewed against the business rules within minutes, and an `@claude` helper on any PR.

## Goal
Add a GitHub Actions workflow that runs `dbt build` and a Claude review on every PR touching dbt.

## Steps to implement
1. In Claude Code, run `/install-github-app`. It installs the Claude GitHub App and adds the `ANTHROPIC_API_KEY` repo secret.
2. Copy the workflow: `mkdir -p .github/workflows && cp de-lab/reference/claude-config/github-workflow-claude-dbt-review.yml .github/workflows/claude-dbt-review.yml`.
3. Read it: job 1 runs `dbt build` (deterministic checks), job 2 runs Claude with a review prompt. Permissions are minimal (`contents: read`, `pull-requests: write`).
4. Open a PR that introduces a bug, for example `SUM(checkout_value_incl_gst)` as revenue in a new model. Watch Claude leave inline comments.
5. In the PR, comment `@claude add a not_null test for the new column and push it.` Watch it commit to the PR branch.
6. Decide as a team: should Claude's review be required, or advisory? Write it in `CLAUDE.md`.

## Core learnings
- The same Claude that helps you locally can run in CI with the repo's `CLAUDE.md` as its rulebook.
- Deterministic checks (dbt build, tests) and an AI review complement each other. Keep both.
- CI agents get least privilege through workflow `permissions` and secrets, never personal tokens.
- `@claude` turns PR comments into tasks: small fixes no longer need a context switch.

## Done when
A buggy PR gets an accurate inline review comment within minutes, and `@claude` can push a fix.
