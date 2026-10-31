---
description: Summarise what changed in the data platform since yesterday (git, landing files, dbt test status)
---

Prepare my data-engineering stand-up note.

1. `git log --since="1 day ago" --oneline` — what changed in code.
2. List files in `de-lab/data/landing/orders/` and flag any missing day in the date sequence.
3. If `dbt_project/target/run_results.json` exists, summarise passed / failed / warned tests.
4. Write 3 sections, max 5 bullets each: **Yesterday**, **Today**, **Blockers**.

Extra context from me: $ARGUMENTS
