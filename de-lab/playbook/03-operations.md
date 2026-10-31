# 3 · Operations and reliability

---

## The 3 am pipeline failure
**Symptom** Pager goes off: the nightly load failed, dashboards are stale, stakeholders wake up in 4 hours.
**Why** Anything in chapter 1, plus infra (disk, credentials, dependency versions).
**Diagnose** In order: (1) what failed and since when (logs, last success), (2) what changed (code `git log`, upstream data, infra), (3) blast radius (which tables and dashboards are affected).
**Fix** Stabilise first (rerun, skip a bad partition, roll back a deploy), fix properly in daylight. Communicate early: "data for 18 Oct is delayed, ETA 10 am".
**With Claude** `cat logs/last_run.log | claude -p "Root cause in 3 lines, what changed, and the safest immediate action"`. In a session: `Diagnose from evidence first. Don't change code until we agree on the cause.`
**Prevent** Runbooks per pipeline, alerts with context (what, since when, link), postmortems that end in a test or a guardrail.
**Practise** Day 12, Day 19 (pipeline doctor), Day 22 (fire drill).

## Freshness and SLA breaches
**Symptom** "Is today's data in yet?" asked 20 times a morning.
**Why** No published SLA, no freshness monitoring, upstream delays invisible downstream.
**Diagnose**
```sql
SELECT MAX(order_ts) AS newest_event, DATE '2026-10-15' - MAX(order_ts)::DATE AS days_behind FROM orders;
```
**Fix** Freshness checks per source with warn/error thresholds (dbt `freshness`), surfaced on dashboards ("data as of …").
**With Claude** `Add dbt source freshness to every source with warn after 12h and error after 24h, and a /daily-standup line that reports it.`
**Prevent** SLAs agreed with consumers, monitored automatically (Day 14 headless job).

## Volume anomalies
**Symptom** Orders down 32% in a city one week. Real drop or broken pipeline?
**Why** Real-world events (rain, outage, festival) or data issues (missing file, filter bug, duplicate removal).
**Diagnose**
```sql
SELECT order_ts::DATE AS day, COUNT(*) AS orders,
       ROUND(COUNT(*) / AVG(COUNT(*)) OVER (ORDER BY order_ts::DATE ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING), 2) AS ratio_7d
FROM orders o JOIN restaurants r USING (restaurant_id) WHERE r.city_id = 1 AND order_ts >= '2026-09-20'
GROUP BY 1 ORDER BY 1;
```
**Fix** First rule out the pipeline (row counts by source file, rejects, dedup counts). Then explain with dimensions (status, cancel reason, restaurant, payment method).
**With Claude** `Orders in Mumbai dropped last week. First prove whether it is a data issue (loads, rejects, duplicates). If not, break the drop down by status and cancel_reason.`
**Prevent** Anomaly checks with seasonality-aware thresholds; annotations for known events.
**Practise** Root demo: Mumbai rain week, `python agent.py "Why did our orders drop in Mumbai last week?"`.

## Slow queries, skew and OOM
**Symptom** A model that took 2 minutes now takes 40; a join runs out of memory.
**Why** Data growth, a fan-out join, skewed keys (one restaurant with 30% of orders), missing filters/pruning, `SELECT *`.
**Diagnose** `EXPLAIN ANALYZE <query>` in DuckDB; check the largest operator and row counts per step; check key distribution:
```sql
SELECT restaurant_id, COUNT(*) AS orders, ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct
FROM orders GROUP BY 1 ORDER BY 2 DESC LIMIT 5;
```
**Fix** Filter and aggregate early, select only needed columns, pre-aggregate the many side, salt skewed keys, incremental models.
**With Claude** `Here is EXPLAIN ANALYZE output. Identify the bottleneck operator and propose two rewrites; benchmark both on the lab database.`
**Prevent** Track model runtimes over time (dbt `run_results.json`), alert on 2× regressions.

## Flaky tests and alert fatigue
**Symptom** Everyone ignores the data-quality channel because it is red every day.
**Why** Thresholds without context, tests on noisy metrics, warnings treated like errors, no owners.
**Fix** Every alert has an owner and an action; separate block vs warn; tune thresholds on history; delete tests nobody acts on.
**With Claude** `From the last 30 days of run_results, list tests that failed and passed without code changes (flaky) and propose new thresholds or severity.`
**Prevent** Review alert value quarterly: "did anyone act on this?".

## Warehouse cost blow-up
**Symptom** The cloud warehouse bill doubles in a month.
**Why** Full refreshes instead of incremental, dashboards polling every minute, runaway backfills, unpartitioned scans.
**Fix** Find the top queries by cost/bytes, make heavy models incremental, cache dashboard queries, schedule instead of poll.
**With Claude** `From this query-history export, group cost by model/user/dashboard and propose the 5 changes with the biggest saving.`
**Prevent** Cost per model as a monitored metric; budgets and alerts. (For LLM token costs see [chapter 5](05-ai-agents.md#token-cost-blow-up).)
