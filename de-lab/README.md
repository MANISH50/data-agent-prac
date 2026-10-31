# de-lab · Daily hands-on: automating data engineering with Claude

A 28-day practice track for data engineers. Each day is one realistic scenario on the same
food-delivery platform, solved with Claude, from your first question in Claude Code to an
autonomous on-call agent running in CI, and then making all of it cheap and fast with
token and context-window engineering.

Every day has the same four parts: **Scenario · Goal · Steps to implement · Core learnings**.

Two references sit next to the daily track:

- **[The field guide](playbook/README.md)**: an A–Z dictionary of 36 real-world problems (late data,
  schema drift, double counting, 3 am failures, PII, prompt injection, token blow-ups...), each with
  symptom, root causes, diagnose queries, fix, how Claude helps, and prevention.
- **[Tokens & context cheat sheet](guides/tokens-and-context.md)**: every lever for cost, speed and
  context-window health, in Claude Code and in your own agents.

## The workspace

```
de-lab/
├── days/                 28 daily lessons (start here)
├── playbook/             field guide: real-world problems A–Z (ingestion, modelling, ops, governance, AI)
├── guides/               tokens & context cheat sheet
├── data/landing/         next week's raw data, deliberately messy
│   ├── orders/           one CSV per day, 15–21 Oct 2026 (one day missing, one drifted...)
│   ├── support_tickets.jsonl    300 free-text tickets (English + Hinglish)
│   └── restaurant_menus.json    nested partner feed
├── notebooks/            00 warehouse tour · 01 landing profiling · 02 lab tables · 03 Claude API playground
├── sql/useful_queries.sql   DuckDB snippets: discovery, DQ patterns, metrics, modelling
├── reference/            solutions (try first, peek later)
│   ├── python/           checker, loader, API / batch / tool-runner / Agent SDK / eval / token-lab scripts
│   ├── claude-config/    settings.json, hooks, skill, subagent, command, .mcp.json, GitHub workflow
│   └── landing_answer_key.md    every planted defect (spoilers)
├── scripts/              regenerate landing data and notebooks
├── pipeline/             YOUR code goes here (created on Day 4)
└── lab.duckdb            YOUR sandbox database (created on Day 5, git-ignored)
```

Two databases, one rule: **`warehouse.duckdb` is production and read-only. Everything you build writes to `de-lab/lab.duckdb`.**

## Setup (once)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r de-lab/requirements-lab.txt
pip install -r requirements-dbt.txt                 # from Day 8
npm install -g @anthropic-ai/claude-code            # Claude Code CLI, then run: claude
export ANTHROPIC_API_KEY=...                        # from Day 15 (API days)
jupyter lab de-lab/notebooks                        # optional
```

The landing data is committed. To rebuild it (identical output, fixed seed): `python de-lab/scripts/make_landing_data.py`.

## The roadmap

| Day | Scenario | Claude concepts |
|---|---|---|
| **Level 1 · Foundations: work with Claude Code** | | |
| [1](days/day-01-orientation.md) | New joiner: understand the platform in an hour | agentic loop, context, `@` mentions |
| [2](days/day-02-claude-md-memory.md) | Stop repeating team rules | `CLAUDE.md` hierarchy, `/memory`, `#` |
| [3](days/day-03-adhoc-sql.md) | Stakeholder questions before a 4 pm call | prompting with constraints, verification |
| [4](days/day-04-profiling-permissions.md) | New files landed: what's wrong with them? | permissions, allow/deny, modes |
| [5](days/day-05-plan-mode-ingestion.md) | Build an idempotent loader | plan mode, task lists, thinking |
| [6](days/day-06-git-review-rewind.md) | Flatten a nested JSON feed, ship it properly | git, `/code-review`, checkpoints, rewind |
| **Level 2 · Customize Claude for your team** | | |
| [7](days/day-07-skills-commands.md) | Same morning checks, every day | skills, slash commands |
| [8](days/day-08-dbt-tests.md) | Data contracts inside dbt | test-first prompting, feedback loops |
| [9](days/day-09-hooks-guardrails.md) | A session deleted production rows | hooks: PreToolUse / PostToolUse |
| [10](days/day-10-subagents.md) | Reviews keep missing business rules | subagents, tool restrictions |
| [11](days/day-11-mcp.md) | Plug your data systems into Claude | MCP servers, scopes |
| [12](days/day-12-schema-drift.md) | 6:30 am: the load failed | debugging with evidence, `claude -p` piping |
| [13](days/day-13-incremental-late-data.md) | Late-arriving orders vs incremental models | big refactors, edge cases, `--continue` |
| **Level 3 · Automate with headless Claude and the API** | | |
| [14](days/day-14-headless-scheduling.md) | A nightly DQ job with nobody watching | `claude -p`, allowed tools, budgets, cron, `/loop` |
| [15](days/day-15-claude-api-basics.md) | Auto-generate the data dictionary | Messages API, tokens, effort, stop reasons |
| [16](days/day-16-structured-outputs.md) | Free-text tickets → typed table | structured outputs, Pydantic |
| [17](days/day-17-tool-use-agent.md) | An agent that investigates bad files | tool use, Tool Runner, agent loop |
| [18](days/day-18-batches-caching.md) | 10,000 tickets a day, on budget | Batches API, prompt caching |
| **Level 4 · Production agents** | | |
| [19](days/day-19-agent-sdk.md) | A pipeline doctor that fixes the loader | Claude Agent SDK, custom MCP tools |
| [20](days/day-20-ci-github-actions.md) | Review every dbt PR in minutes | GitHub Actions, `@claude` |
| [21](days/day-21-evals.md) | "Is the agent good enough to ship?" | evals, ground truth, variants |
| [22](days/day-22-capstone.md) | Capstone: the autonomous data on-call | everything together |
| **Level 5 · Tokens & context engineering** | | |
| [23](days/day-23-measure-tokens.md) | "Why is the AI bill so high?" | tokens, `usage`, `count_tokens`, `/context`, `/cost` |
| [24](days/day-24-claude-code-context-hygiene.md) | A 3-hour session gets slow and forgetful | `/clear`, `/compact`, subagents, lean memory |
| [25](days/day-25-lean-tools.md) | Same answers, fewer turns and tokens | lean tools, schema up front, aggregate in SQL |
| [26](days/day-26-prompt-caching-deep-dive.md) | Paying full price for identical bytes | prompt caching, breakpoints, invalidators |
| [27](days/day-27-long-running-agents.md) | A 200-partition backfill agent | context editing, compaction, external memory, task budgets |
| [28](days/day-28-cost-quality-optimization.md) | A budget for 12,000 AI tasks a day | cost per correct task, lever order, routing |

## Your daily routine (about 60 minutes)

1. **5 min:** read the day's Scenario and Goal. Write down how *you* would solve it without Claude.
2. **40 min:** follow the Steps in Claude Code. Type the prompts, then change them. Read every command before approving it.
3. **10 min:** verify. Every day has a **Done when**. Prove it with a number, a test or a diff.
4. **5 min:** write one line in `de-lab/reports/journal.md`: what Claude did well, where you had to correct it, and one rule to add to `CLAUDE.md` or a skill.

## Progress

Copy into your journal and tick as you go:

```
L1  [ ] 1  [ ] 2  [ ] 3  [ ] 4  [ ] 5  [ ] 6
L2  [ ] 7  [ ] 8  [ ] 9  [ ] 10 [ ] 11 [ ] 12 [ ] 13
L3  [ ] 14 [ ] 15 [ ] 16 [ ] 17 [ ] 18
L4  [ ] 19 [ ] 20 [ ] 21 [ ] 22
L5  [ ] 23 [ ] 24 [ ] 25 [ ] 26 [ ] 27 [ ] 28
```

## Claude concepts covered

| Area | Concepts | Days |
|---|---|---|
| Claude Code basics | agentic loop, context, `@` mentions, `!` bash, plan mode, task lists, checkpoints / rewind, `--continue` / `--resume` | 1, 5, 6, 13 |
| Memory and rules | `CLAUDE.md` (user / project / nested / local), `/init`, `/memory`, `#` | 2 |
| Safety | permission prompts and modes, allow / deny rules, hooks, least privilege, budgets | 4, 9, 14, 19 |
| Reuse | skills, slash commands, subagents | 7, 10 |
| Integrations | MCP servers and scopes, GitHub app and Actions | 11, 20 |
| Automation | headless `claude -p`, JSON output, cron, `/loop` | 12, 14 |
| Claude API | Messages API, models, effort, token counting, stop reasons, refusal fallbacks | 15 |
| API features | structured outputs, tool use, Tool Runner, Batches, prompt caching | 16, 17, 18 |
| Agents | Claude Agent SDK, custom tools, autonomy boundaries | 19, 22 |
| Quality | verification, tests, evals | 3, 8, 21 |
| Tokens & context | token accounting, `/context` / `/cost`, `/compact` / `/clear`, lean tools, caching design and invalidators, context editing, compaction, external memory, task budgets, cost per correct task | 23–28 |
| Real-world readiness | field guide of 36 production problems, each with diagnose / fix / prevent | [playbook](playbook/README.md) |

## Cost notes

Days 1–14 and 24 use Claude Code with your subscription or API key. Days 15–28 call the API directly and
spend tokens: scripts default to `claude-opus-5-5`; set `LAB_MODEL=claude-haiku-5-5` for cheap practice
runs, and always start with a small `--limit` or a few rows. `token_lab_agent.py --dry-run` and
`context_budget.py` are free and need no API key.
