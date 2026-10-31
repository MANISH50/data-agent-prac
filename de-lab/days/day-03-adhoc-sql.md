# Day 3 · Answering stakeholder questions with SQL (and checking the answers)

**Level:** 1 Foundations · **Time:** 45 min · **Claude concepts:** prompting with constraints, asking for the SQL + reasoning, verification loops

## Scenario
The city head of Mumbai pings you: *"Which 5 restaurants had the worst cancellation rate last month? And what was our average order value in Bengaluru?"* They need it before a 4 pm call.

## Goal
Get correct answers fast, and prove they are correct against a ground truth.

## Steps to implement
1. Ask with constraints, so the answer is checkable:
   `Using warehouse.duckdb (read-only), find the 5 Mumbai restaurants with the highest cancellation rate in September 2026, minimum 50 orders. Show the SQL, the result, and one line on assumptions.`
2. Ask the second question the naive way: `What was the average order value in Bengaluru last month?` Note what definition Claude picks.
3. Now compare with ground truth: `python check_answers.py` (Q4 and Q5). Does Claude's AOV match `correct_aov` or `naive_avg_amount_all_orders`?
4. If it is wrong, don't just correct the number; correct the **definition**: `AOV means revenue per delivered, non-refunded order, where revenue excludes GST and promo. Redo it.`
5. Ask Claude to save the final SQL as `de-lab/sql/stakeholder_2026_10_mumbai.sql` with a header comment (question, date, definition).
6. Run `python agent.py "What was the average order value in Bengaluru last month?"` and compare: the demo agent has no memory of your conventions, Claude Code has `CLAUDE.md`.

## Core learnings
- Ask for **SQL + result + assumptions** every time: you review logic, not just numbers.
- The model is only as right as the definition it is given. Ambiguous business terms (revenue, AOV, active user) are where agents fail.
- Ground-truth files like `answers.sql` are your first eval. You will automate this on Day 21.

## Done when
Both answers match `check_answers.py`, and the SQL is saved with its definition.
