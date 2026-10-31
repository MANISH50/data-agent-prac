# Day 2 · CLAUDE.md: teach Claude your team's rules once

**Level:** 1 Foundations · **Time:** 45 min · **Claude concepts:** `CLAUDE.md` (project / nested / user memory), `/init`, `/memory`, `#` quick memory

## Scenario
Yesterday Claude wrote a query that joined city through `customers.city_id` (wrong: the company uses the restaurant's city) and suggested writing into `warehouse.duckdb`. You don't want to repeat these corrections every session.

## Goal
Write a `de-lab/CLAUDE.md` that encodes the team's data conventions so every future session follows them.

## Steps to implement
1. Read the root `CLAUDE.md` (generated with `/init`). Note what it contains: commands, architecture, invariants.
2. Create a **nested** memory file for the lab. Ask Claude:
   `Create de-lab/CLAUDE.md with our data engineering conventions: warehouse.duckdb is read-only, all writes go to de-lab/lab.duckdb, landing files are read with all_varchar=true, city comes through restaurants, date filters are half-open ranges, table names are snake_case with raw_/stg_/fct_ prefixes, every load keeps _source_file and _loaded_at.`
3. Review the file and cut anything generic. Good memory is short and specific.
4. Add a rule on the fly: type `# Always show row counts before and after any transformation` in Claude Code. It asks which memory file to save it to.
5. Run `/memory` to see every memory file loaded in this session and open one to edit.
6. Test it: start a **new** session and ask `Write SQL for orders per city last month.` Check it joins through `restaurants`.

## Core learnings
- Memory hierarchy: `~/.claude/CLAUDE.md` (you, all projects) → `./CLAUDE.md` (team, committed) → nested `de-lab/CLAUDE.md` (loaded when Claude works in that folder) → `CLAUDE.local.md` (you, this project, not committed).
- Write rules as facts and constraints, not essays. Each line should change behaviour.
- `CLAUDE.md` is context, not enforcement. For rules that must never break, use hooks (Day 9) or permissions (Day 4).

## Done when
A fresh session follows your conventions without being told.
