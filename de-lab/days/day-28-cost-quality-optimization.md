# Day 28 · Cost vs quality: the optimisation playbook with numbers

**Level:** 5 Tokens & context engineering · **Time:** 90 min · **Claude concepts:** cost per completed task, model choice, `effort`, Batches, caching, output-token control, routing, measuring with evals

## Scenario
Leadership wants the data agent for all 6 city teams (≈ 2,000 questions/day) plus nightly ticket classification (10,000/day), with a monthly budget. You must present options with cost **and** accuracy, not opinions.

## Goal
Build a cost/quality table for the agent and the ticket job across levers, and recommend a configuration.

## Steps to implement
1. **Unit of measure:** cost per *completed, correct* task, not per request. A cheap run that needs a retry, or gives a wrong number, is not cheap.
2. **Order of levers** (free wins first, trade-offs last):
   1. remove waste: lean tools, aggregates, no pasted data (Day 25)
   2. caching for repeated prefixes (Day 26)
   3. Batches for anything not real-time (Day 18): 50% off
   4. control output: short answer formats, structured outputs instead of prose, sensible `max_tokens`
   5. `effort`: lower for routine classification, higher for hard analysis
   6. model choice, last, and only with an eval showing quality holds
3. For the agent, run the Day 21 eval in 4 configurations: baseline · lean · lean+cache · lean+cache+lower effort. Record accuracy, turns, tokens and cost per correct answer.
4. For tickets, compare on 50 tickets: real-time `parse` (Day 16) vs batch+cache (Day 18), and two models via `LAB_MODEL`. Spot-check accuracy against 20 hand labels.
5. **Routing:** could simple questions ("how many orders…") go to a cheaper configuration and hard ones ("why did revenue drop…") to the strongest? Measure before building it: often the strongest model at lower effort is simpler and as cheap.
6. Ask Claude Code to turn `de-lab/reports/token_runs.jsonl` into a cost table and a one-page recommendation with monthly totals.

## Core learnings
- Measure first, then optimise in order: waste → caching → batch → output size → effort → model.
- Quality is a constraint, not a variable: every cost change is validated by an eval.
- Output tokens are the expensive ones; ask for short, structured outputs.
- Cost is an architecture decision (real-time vs batch, one agent vs routing), not just a model setting.

## Done when
You have a recommendation like "lean+cache, batch for tickets: x% of baseline cost, same accuracy", with the numbers to back it.
