# 2 · Modelling and correctness

SQL runs against `warehouse.duckdb` (read-only) unless it says otherwise.

---

## Metric definition disputes
**Symptom** Finance says revenue was ₹78 lakh, the product dashboard says ₹1.02 crore. Both are "right".
**Why** No single definition: gross vs net, with/without tax, refunds, cancellations, order date vs delivery date.
**Diagnose**
```sql
SELECT SUM(o.amount) AS gross_incl_gst_all,
       SUM(o.amount) FILTER (WHERE o.status = 'delivered') AS gross_delivered,
       SUM(o.amount - o.promo_value - t.gst) FILTER (WHERE o.status = 'delivered' AND f.order_id IS NULL) AS revenue
FROM orders o JOIN order_taxes t USING (order_id) LEFT JOIN refunds f USING (order_id)
WHERE o.order_ts >= '2026-09-01' AND o.order_ts < '2026-10-01';
```
**Fix** One owner, one definition, in one place (a semantic layer / dbt metric). Every dashboard and agent reads it from there. Show the waterfall from gross to net so people see why numbers differ.
**With Claude** `Find every place in the repo that computes revenue, list how each differs from the dbt metric, and propose a migration.`
**Prevent** Metrics in `semantic_models.yml`, descriptions in `schema.yml`, agents given those definitions (`agent.py --context`).
**Practise** Days 3, 21 and the root demo.

## Fan-out joins and double counting
**Symptom** Revenue doubles after joining a new table.
**Why** Joining a one-to-many table (refunds, items, events) before aggregating.
**Diagnose**
```sql
SELECT COUNT(*) AS rows_after_join, COUNT(DISTINCT o.order_id) AS orders
FROM orders o LEFT JOIN refunds f USING (order_id);   -- equal = safe; rows > orders = fan-out
```
**Fix** Aggregate the many side to the grain first, then join; or use `EXISTS` / `ANTI JOIN` for filters.
**With Claude** `Review this query for fan-out: state the grain of every table and where the grain changes.`
**Prevent** Document the grain of every model; `unique` test on the grain key of every mart. The `sql-reviewer` subagent (Day 10) checks this.

## Units, currency and tax
**Symptom** Numbers are off by 5%, by 100×, or mix ₹ and $.
**Why** Tax-inclusive vs exclusive amounts, paise vs rupees, multi-currency without conversion date.
**Fix** Column names carry units (`amount_incl_gst_inr`, `price_paise`); convert in staging; store currency and FX rate date with every converted value.
**With Claude** `Audit column names and descriptions for missing units or tax treatment and propose renames.`
**Prevent** Naming convention in `CLAUDE.md`; tests on ranges (e.g. AOV between ₹100 and ₹2,000).
**Practise** The GST trap in the root demo (`orders.amount` includes GST).

## Nulls in aggregates and joins
**Symptom** Averages look too high; rows vanish after a join; `NOT IN` returns nothing.
**Why** `AVG` ignores NULLs; NULL keys never match; `NOT IN (subquery with NULL)` is always unknown.
**Diagnose**
```sql
SELECT COUNT(*) AS rows, COUNT(cancel_reason) AS non_null, COUNT(*) - COUNT(cancel_reason) AS nulls FROM orders;
```
**Fix** Decide per column what NULL means (unknown, not applicable, zero) and encode it; use `ANTI JOIN` / `NOT EXISTS` instead of `NOT IN`.
**With Claude** `For each column of this model, tell me what NULL means and whether any aggregate treats it wrongly.`
**Prevent** `not_null` tests where NULL is a bug; documented meaning where it isn't.

## Slowly changing dimensions
**Symptom** Last year's revenue by city changed after a restaurant moved city.
**Why** Dimensions overwritten in place (SCD1) when history matters.
**Fix** SCD2: `valid_from`, `valid_to`, `is_current`; join facts on the key **and** the event time between validity dates. dbt snapshots do this.
**With Claude** `Convert restaurants into an SCD2 dbt snapshot and rewrite fct_orders to join the version valid at order time. Add a test that versions don't overlap.`
**Prevent** Decide SCD type per attribute at design time.

## Idempotency
**Symptom** A re-run after a failure doubles yesterday's data.
**Why** Plain `INSERT` loads; no unique key; partial writes without transactions.
**Diagnose** Run the job twice on the same input and compare counts (Day 5).
**Fix** Replace a partition/file as a unit inside a transaction (delete+insert), or `MERGE`/`INSERT OR REPLACE` on a key. Record what was loaded (`_source_file`).
**With Claude** `Prove this job is idempotent: run it twice in a scratch database and compare row counts and checksums per partition.`
**Prevent** Idempotency as a CI test for every loader.
**Practise** Day 5, Day 18 (`INSERT OR REPLACE` of batch results).

## Backfills and reprocessing
**Symptom** A logic fix must be applied to 2 years of history; the warehouse bill and the on-call nerves explode.
**Why** No partitioned reprocessing, no way to run old dates, no validation between old and new.
**Fix** Parameterise jobs by date range; backfill in chunks (e.g. a month at a time); write to a shadow table, compare with the old one, then swap.
**With Claude** `Plan a backfill of fct_orders for Apr–Oct in monthly chunks into fct_orders_v2, with a comparison report per month (rows, revenue, diff %) before the swap.`
**Prevent** Every job accepts `--start/--end`; diffs between versions are a standard report.
**Practise** Day 27 (chunked validation of 200 partitions).
