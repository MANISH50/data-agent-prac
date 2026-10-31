# 1 · Ingestion and sources

SQL below runs in `duckdb de-lab/lab.duckdb` after `ATTACH 'warehouse.duckdb' AS wh (READ_ONLY);` and the Day 5 load.

---

## Late-arriving data
**Symptom** Yesterday's numbers change today; a daily total is lower than the source system's.
**Why** Offline queues, mobile apps syncing late, retries, upstream backfills. Event time ≠ load time.
**Diagnose**
```sql
SELECT _source_file, order_date, COUNT(*) AS rows
FROM stg_orders WHERE is_late_arriving GROUP BY ALL ORDER BY ALL;
```
**Fix** Keep both timestamps (event time + `_loaded_at`). Incremental models re-process a **lookback window** (e.g. last 3 days) with delete+insert or merge on the key. Report "as of" times on dashboards.
**With Claude** `Our incremental model uses order_date = current_date. List every way late data breaks it, then rewrite it with a 3-day lookback and a test comparing it to a full recompute.`
**Prevent** A test that alerts when late rows exceed x% of a day; documented restatement policy ("numbers final after D+3").
**Practise** Day 13 (30 late rows for 19 Oct in the 21 Oct file).

## Schema drift
**Symptom** Load fails with "column not found", or worse, succeeds with a column full of NULLs.
**Why** Producers rename, add, retype or reorder columns without notice.
**Diagnose** `head -1 de-lab/data/landing/orders/*.csv` (compare headers), then:
```sql
-- with union_by_name, a column that is NULL for a whole file is a renamed or missing column
SELECT filename, COUNT(*) AS rows, COUNT(amount) AS has_amount, COUNT(order_amount) AS has_order_amount
FROM read_csv('de-lab/data/landing/orders/*.csv', all_varchar=true, union_by_name=true, filename=true)
GROUP BY 1 ORDER BY 1;
```
**Fix** Contract check at the boundary: required columns must exist (fail loudly), known renames are mapped explicitly, unknown new columns are kept (e.g. JSON `_extra`) not dropped. Never let type inference decide.
**With Claude** `Here is the failing file header and our expected schema. Classify each difference as rename / new / missing / type change and update the RENAMES map and the contract test.`
**Prevent** Data contract with the producer (owner, schema, change process); a CI check on the schema of the first file of each day; a hook-free alert in the loader.
**Practise** Day 12 (`amount` → `order_amount`, new `delivery_fee` on 18 Oct).

## Duplicates and re-sent data
**Symptom** Totals jump; `COUNT(*)` ≠ `COUNT(DISTINCT id)`.
**Why** At-least-once delivery, retries, producers re-sending batches, overlapping extract windows.
**Diagnose**
```sql
SELECT _source_file, order_id, COUNT(*) AS copies,
       COUNT(DISTINCT (customer_id, restaurant_id, order_ts, amount)) AS distinct_versions
FROM raw_orders GROUP BY ALL HAVING COUNT(*) > 1 ORDER BY copies DESC LIMIT 10;
```
**Fix** Decide the dedup rule per source: exact duplicates → collapse; same key, different content → keep the latest by a reliable version/updated_at, and log the conflict. `QUALIFY row_number() OVER (PARTITION BY key ORDER BY version DESC) = 1`.
**With Claude** `Find duplicate order_ids across raw_orders and tell me whether they are exact copies or conflicting versions. Propose the dedup rule and the test.`
**Prevent** `unique` test on the key in staging; monitor the duplicate rate per file.
**Practise** Day 4–5 (25 re-sent rows on 16 Oct).

## Missing partitions
**Symptom** A day is flat zero; nobody noticed for a week.
**Why** Upstream job failed, file landed in the wrong folder, credentials expired, a holiday-skip bug.
**Diagnose**
```sql
SELECT d::DATE AS missing_day
FROM generate_series(DATE '2026-10-15', DATE '2026-10-21', INTERVAL 1 DAY) t(d)
ANTI JOIN (SELECT DISTINCT order_date FROM stg_orders) s ON s.order_date = t.d::DATE;
```
**Fix** Treat "no data" as an error, not as zero. Pause downstream publishing for that day; ask the producer to re-send; mark the day as incomplete on dashboards.
**With Claude** `Write a freshness/completeness check that fails if any expected daily partition has no file or < 50% of the trailing average rows. Add it to the nightly headless job.`
**Prevent** Completeness test (Day 8), expected-arrival SLA per source, alert on absence, not just on failure.
**Practise** Day 14 (20 Oct never arrives).

## Orphan keys
**Symptom** Joins silently drop rows; revenue by city ≠ total revenue.
**Why** Dimension not yet loaded, test data in prod, deleted reference rows, ID ranges from another system.
**Diagnose**
```sql
SELECT o.restaurant_id, COUNT(*) AS rows
FROM (SELECT TRY_CAST(restaurant_id AS INTEGER) AS restaurant_id FROM raw_orders) o
ANTI JOIN wh.restaurants r USING (restaurant_id) GROUP BY 1 ORDER BY 2 DESC;
```
**Fix** Quarantine or attach to an "unknown" member (`-1`) so totals still add up; re-process when the dimension arrives.
**With Claude** `Compare total revenue with the sum of revenue by city and explain the gap with the exact rows causing it.`
**Prevent** `relationships` tests; reconciliation test "sum by dimension = total".
**Practise** Day 4 / 8 (restaurant_ids 9001–9099 on 19 Oct).

## Malformed files
**Symptom** Parser errors on line 48,213; strange characters (`Ã©`); columns shifted by one.
**Why** Wrong encoding, unescaped delimiters/quotes in free text, truncated uploads, BOM, Excel exports.
**Diagnose** `head -c 300 file | xxd | head` · `file -i file.csv` · in DuckDB: `read_csv(..., all_varchar=true, ignore_errors=true, store_rejects=true)` then `FROM reject_errors`.
**Fix** Read as text with explicit delimiter/quote/encoding; route bad lines to a rejects table with the line number; never "skip errors" silently.
**With Claude** `Here are the first 20 lines and the parser error. Identify the encoding/quoting problem and write a robust read_csv call plus a rejects report.`
**Prevent** File-level checks before load: size > 0, row count vs manifest, checksum, header match.

## Timezones and DST
**Symptom** Orders at 11:30 pm land on the wrong day; hourly charts have a hole or a double hour twice a year.
**Why** Mixing UTC and local time, naive timestamps, servers in different regions, DST in source countries.
**Diagnose**
```sql
SELECT hour(order_ts) AS h, COUNT(*) FROM stg_orders GROUP BY 1 ORDER BY 1;
```
**Fix** Store UTC (`TIMESTAMPTZ`), convert to business timezone (`Asia/Kolkata`) only in marts; define the business day explicitly.
**With Claude** `Audit every timestamp column in the repo: is it UTC or local, and where do we convert? Output a table and the risky queries.`
**Prevent** Naming convention (`_utc`, `_ist`), one conversion layer, tests on day boundaries.

## CDC: updates and hard deletes
**Symptom** Cancelled orders still show as delivered; deleted customers still appear.
**Why** Extracts that only append, missing delete events, soft vs hard delete confusion.
**Fix** Use change data capture with operation type (I/U/D) and source LSN/version; apply with `MERGE`; keep a history table if needed (SCD2).
**With Claude** `Design a MERGE that applies a CDC feed with op in (I,U,D) and out-of-order events using a version column. Include tests for an update arriving before its insert.`
**Prevent** Reconcile counts with the source periodically (full snapshot vs CDC result).

## Upstream APIs: pagination and throttling
**Symptom** Exactly 1,000 rows every day; 429 errors; partial loads after timeouts.
**Why** Default page size, missing pagination, rate limits, no retry/backoff, no checkpointing.
**Fix** Paginate until the cursor ends; exponential backoff with jitter on 429/5xx; checkpoint the cursor; make each page idempotent.
**With Claude** `Write an extractor for this API doc with cursor pagination, retries with backoff, checkpointing to a state file, and a test with a fake server that returns 429 twice.`
**Prevent** Alert when the row count equals a round page size; record page counts per run.

## Small files
**Symptom** Queries slow down over months although data volume is modest; thousands of tiny files.
**Why** Streaming or per-event writes, hourly partitions with little data, many small appends.
**Fix** Compaction job that rewrites partitions into larger files; partition by day not hour; batch writes.
**With Claude** `List partitions with more than 50 files under 1 MB and write a compaction script that is safe to re-run.`
**Prevent** Monitor files per partition and average file size.
