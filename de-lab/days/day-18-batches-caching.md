# Day 18 · Scale and cost: Message Batches + prompt caching

**Level:** 3 Automate · **Time:** 75 min · **Claude concepts:** Message Batches API (50% price, async), prompt caching (`cache_control`, cache reads), JSON-schema output, idempotent result loading

## Scenario
Day 16 cost was fine for 20 tickets. Production gets 10,000+ tickets a day, nobody needs answers in real time, and finance asks what this will cost per month.

## Goal
Classify all 300 tickets in one batch job with a cached classification guide, load results idempotently, and estimate the monthly cost.

## Steps to implement
1. Prove caching works first (notebook `03_claude_api_playground.ipynb`, cell 3): the second request should show `cache_read_input_tokens > 0`.
2. Read `de-lab/reference/python/day18_batch_tickets.py`:
   - the long guide sits in `system` with `cache_control: {"type": "ephemeral"}` and is byte-identical in every request
   - each request has a `custom_id` = ticket id
   - output is forced into a JSON schema with `output_config.format`
3. Submit: `python de-lab/reference/python/day18_batch_tickets.py submit`. Note the batch id.
4. Collect (it can take minutes): `python ... collect <batch_id>`. Results arrive in **any order**; the script keys them by `custom_id` and upserts (`INSERT OR REPLACE`), so re-collecting is safe.
5. Compare `tickets_batch` with Day 16's `tickets_structured` on the overlapping 20 tickets. Any disagreements? Which is right?
6. Ask Claude Code: `Using the usage numbers, estimate monthly cost for 10,000 tickets/day with and without batch and caching.`

## Core learnings
- Batch = same quality, half price, results within hours. Use it for anything not user-facing: backfills, enrichment, nightly classification.
- Caching rewards **stable prefixes**: put fixed instructions first, varying input last. A timestamp in the system prompt silently kills the cache.
- Always key async results by id, never by position, and load them idempotently.
- Cost is an engineering requirement. Measure tokens, then choose model / effort / batch / cache.

## Done when
300 classified tickets are in `tickets_batch`, and you have a monthly cost estimate with the saving from batch + cache.
