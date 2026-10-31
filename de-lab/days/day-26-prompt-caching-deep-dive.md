# Day 26 · Prompt caching deep dive: make the repeated part (almost) free

**Level:** 5 Tokens & context engineering · **Time:** 75 min · **Claude concepts:** prefix matching, render order (tools → system → messages), explicit vs automatic breakpoints, TTL (5 min / 1 h), minimum cacheable size, silent invalidators, cache-read economics

## Scenario
The agent runs 2,000 questions a day. Each request starts with the same tool definitions and system prompt, and inside a question each turn re-sends the growing conversation. You are paying full price to send identical bytes again and again.

## Goal
Turn on caching correctly, prove it with `cache_read_input_tokens`, and find what silently breaks it.

## Steps to implement
1. **How it works:** the cache key is the exact bytes of the prompt up to a breakpoint, in the order tools → system → messages. A one-byte change early invalidates everything after it. Reads cost a small fraction of normal input (on Claude Opus 5.5, $0.20 vs $4 per million); writes cost 1.25× (5-minute TTL) or 2× (1-hour TTL).
2. Read `--cache` in `token_lab_agent.py`: an **explicit breakpoint** on the static system block plus **top-level automatic caching**, which moves the breakpoint forward as the conversation grows. This is the standard pattern for agent loops.
3. Run `--lean --cache`. Turn 1 shows `c.write`, later turns show growing `c.read`. Compare cost with `--lean` alone.
4. **Minimum size:** the lean system prompt alone (~250 tokens) is below the model's minimum cacheable prefix (512 tokens on current models), so it only caches once tools + conversation pass the minimum. No error, just zero cache tokens. Check this in your numbers.
5. **Break it on purpose:** add `datetime.now()` to the system prompt and re-run twice: `cache_read` drops to 0. Other silent invalidators: random ids, `json.dumps` without `sort_keys`, tool lists that change per user, conditional prompt sections.
6. Grep your own Day 15–19 scripts for these patterns and fix them.
7. Calculate break-even for your traffic: with the 5-minute TTL two requests already pay off; bursty traffic with gaps > 5 min may need the 1-hour TTL.

## Core learnings
- Order prompts **stable → volatile**: tools, then system, then history, then the new question.
- Use explicit breakpoints at stability boundaries and automatic caching for the growing tail.
- Always verify with `usage.cache_read_input_tokens`; if it's 0 across repeated calls, something in the prefix is changing.
- Caching changes the economics of agents: long, rich system prompts become cheap if they are byte-stable.

## Done when
A multi-turn run shows cache reads on every turn after the first, and you found and fixed one invalidator in your own code.
