# Day 6 · Git with Claude: branches, commits, reviews and rewinding mistakes

**Level:** 1 Foundations · **Time:** 60 min · **Claude concepts:** git workflows, `/code-review`, checkpoints and `/rewind` (Esc Esc), `!` bash mode

## Scenario
The partner team sends a nested JSON menu feed (`restaurant_menus.json`). You need a flat `stg_menu_items` table, built on a branch, reviewed and committed properly. Halfway through, Claude goes in a direction you don't like.

## Goal
Ship a reviewed change through git with Claude, and learn to undo safely.

## Steps to implement
1. `Create a branch feature/menu-items.` (Claude runs git for you.)
2. `Add a step to de-lab/pipeline/ingest.py that flattens restaurant_menus.json into stg_menu_items (restaurant_id, item_id, item_name, price_inr, currency, tags as a list, available). Use DuckDB unnest.`
3. Deliberately steer it wrong: `Actually, use pandas and json_normalize instead.` Let it edit.
4. Now rewind: press **Esc twice** (or `/rewind`) and pick the checkpoint before the pandas change. Restore code and conversation. Checkpoints cover Claude's file edits, not external side effects like database writes.
5. Run a quick shell command without leaving Claude: `!python de-lab/pipeline/ingest.py`.
6. Ask for a review before committing: `/code-review`. Fix what matters.
7. `Commit with a clear message.` Read the message; Claude writes it from the diff.

## Core learnings
- Claude handles git the way you would: branch, diff, commit, and (with GitHub access) PRs.
- Checkpoints make experimentation cheap: try an idea, rewind if it's wrong.
- A review step before every commit catches the obvious mistakes; reviewing is a separate prompt with a separate mindset.
- `!` runs a command yourself and puts the output in Claude's context.

## Done when
`stg_menu_items` has 180 rows, the change is committed on its branch, and you have used rewind once.
