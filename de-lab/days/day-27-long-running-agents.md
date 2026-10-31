# Day 27 · Long-running agents: context editing, compaction, memory and task budgets

**Level:** 5 Tokens & context engineering · **Time:** 90 min · **Claude concepts:** context window limits, context editing (`clear_tool_uses`), server-side compaction, external memory (notes files, memory tool), task budgets, checkpointing work outside the context

## Scenario
A backfill agent must validate ~200 daily partitions (1 Apr – 14 Oct). Each partition means 3–4 tool calls with results. By partition 60 the context is huge, every turn is slow and expensive, and early findings are getting lost.

## Goal
Design an agent that can run for hundreds of tool calls with a bounded context, without forgetting results.

## Steps to implement
1. **Do the maths first.** 200 partitions × 4 calls × ~600 tokens per result ≈ 480K tokens of tool results, re-sent on every turn. Even with a 1M window, that is slow and expensive long before it is full.
2. **Context editing:** run `token_lab_agent.py ... --clear-tools` on a long question (e.g. *"Check every week since April for days with fewer than 70% of the trailing 7-day average orders"*). The API clears old tool results once context grows; the model keeps its conclusions. Compare input tokens with and without.
3. **Keep results outside the context.** Ask Claude Code to write a backfill agent (manual loop or Tool Runner) where each partition's verdict is written to `lab.duckdb.backfill_results` by a tool, and the model only keeps a one-line running summary. The table is the memory, not the chat.
4. **Chunk the work.** Process partitions in batches of 14 days, each a fresh conversation seeded with a short summary of earlier batches. Compare cost and quality with one giant conversation.
5. **Compaction:** for conversational, open-ended sessions, enable server-side compaction (beta `compact-2026-01-12`, `context_management={"edits": [{"type": "compact_20260112"}]}`) and always append the full `response.content` back so compaction blocks survive.
6. **Task budgets:** give the agent a token budget (`output_config.task_budget`, beta) so it paces itself and wraps up instead of being cut off.
7. Write a design note: when do you use context editing vs compaction vs external memory vs chunking?

## Core learnings
- **Context editing** clears stale tool results (cheap, keeps the conversation). **Compaction** summarises history (for long open-ended sessions). **External memory** (tables, files) persists results beyond any context. **Chunking** bounds context by design.
- For batch-like work (backfills, many partitions), chunking + external memory is the most predictable and the cheapest.
- The model should hold *conclusions*, your systems should hold *data*.
- The same ideas apply to Claude Code: `/compact`, subagents, and notes files (Day 24).

## Done when
A 200-partition validation completes with bounded per-turn input tokens and every verdict stored in a table.
