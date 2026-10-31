# Tokens & context: the cheat sheet

Keep this open while you work. Practised in Days 23–28.

## The five facts everything follows from

1. **Every request carries its whole context.** The API is stateless. In an agent loop, turn *n* re-sends turns 1…*n-1*: system prompt, tool definitions, every tool call and every tool result.
2. **Cost ≈ turns × context size**, plus output. Output tokens cost several times more than input tokens.
3. **More context is not better context.** Irrelevant tokens cost money and attention; buried facts get missed.
4. **Caching is a prefix match.** Identical leading bytes (tools → system → messages) are cheap to re-read; one changed byte early breaks everything after it.
5. **Measure, don't guess.** `count_tokens` before, `usage` after, `/context` and `/cost` in Claude Code.

## In Claude Code (interactive)

| Habit | Why | How |
|---|---|---|
| Check what's in context | You can't optimise what you can't see | `/context`, `/cost` |
| Clear between unrelated tasks | Old task = noise for the new one | `/clear` (save decisions to a file first) |
| Compact with intent | Auto-compaction doesn't know what matters to you | `/compact keep: decisions, failing files; drop: raw output` |
| Explore with subagents | Their reading stays in *their* window | "Use a subagent to find X and summarise in 10 lines" |
| Ask for aggregates | 500 rows → 5 lines | "Counts per file per defect, no rows" |
| Point, don't paste | Pasting data is the most expensive habit | `@path/file.sql`, or "query the file" instead of pasting it |
| Short `CLAUDE.md` | Loaded every session | Facts and rules only; move procedures into skills |
| Skills for procedures | Body loads only when used | `.claude/skills/<name>/SKILL.md` |
| Notes files for long work | Survive `/clear` and compaction | `session_notes.md`, plans, `CLAUDE.md` |
| Right model per task | Strong model for design, fast one for boilerplate | `/model` |

## In your own agents (API / SDK)

| Lever | Typical saving | Watch out |
|---|---|---|
| Schema / key rules in the system prompt instead of discovery turns | removes 2–4 turns | keep it deterministic (sorted) so it caches |
| Small tool results (aggregate in SQL, cap rows, round numbers) | 50–80% of tool-result tokens | say when you truncate, so the model can recover |
| Fewer, terser tools | tool defs are re-sent every turn | descriptions are still the tool's prompt: be precise |
| Prompt caching (explicit breakpoint on static system + automatic for the tail) | repeated prefix at a fraction of input price | prefix below the minimum (512 tokens on current models) silently won't cache |
| Batches API | 50% | async, results in any order: key by `custom_id` |
| Structured outputs / short answer formats | fewer output tokens, no parsing | still validate facts |
| Lower `effort` for routine work | fewer thinking + output tokens | measure accuracy; keep high for hard analysis |
| Context editing (`clear_tool_uses_20250919`) | caps growth in long tool loops | beta; model keeps conclusions, loses raw results |
| Compaction (`compact_20260112`) | long open-ended conversations | beta; append full `response.content` every turn |
| External memory (tables / files) + chunking | bounded context for any job length | design the summary you carry between chunks |
| Task budget | agent paces itself | beta; advisory, not a hard cap |
| Model choice | large | last lever, only with an eval showing quality holds |

## Silent cache invalidators (grep for these)

- `datetime.now()`, `time.time()`, dates in the system prompt (use a fixed date or put it after the breakpoint)
- `uuid4()`, request ids, user ids early in the prompt
- `json.dumps(...)` without `sort_keys=True`; iterating over a `set`
- tool lists built per user or per request; conditional `system += ...` sections
- switching model or top-level `effort` mid-conversation (caches are per model)

## Back-of-envelope formulas

```
agent cost  ≈ Σ_turns (system + tools + history_so_far) × input_price + Σ output × output_price
with cache  ≈ first write × 1.25 × input_price + later reads × cache_read_price + new tokens × input_price
monthly     = cost_per_correct_task × tasks_per_day × 30 / accuracy
```

## Order of operations when the bill is too high

1. Measure a baseline (tokens, turns, cost, **accuracy**) on a fixed eval.
2. Remove waste: pasted data, big tool results, discovery turns, chatty outputs.
3. Cache stable prefixes; verify `cache_read_input_tokens > 0`.
4. Move non-real-time work to Batches.
5. Tune `effort` per route.
6. Only then consider a different model, and re-run the eval.
