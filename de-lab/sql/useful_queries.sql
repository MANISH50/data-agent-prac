-- useful_queries.sql  -  copy-paste snippets for the lab (DuckDB dialect)
-- Open the CLI read-only:   duckdb -readonly warehouse.duckdb
-- Or the lab sandbox:       duckdb de-lab/lab.duckdb      (then: ATTACH 'warehouse.duckdb' AS wh (READ_ONLY);)

-- ── Discover ──────────────────────────────────────────────────────────────
SHOW ALL TABLES;
DESCRIBE orders;
SUMMARIZE orders;                                   -- min/max/nulls/distinct for every column
SELECT * FROM duckdb_constraints();                 -- keys (there are none: the raw app has no constraints)

-- ── Read landing files without loading them ──────────────────────────────
SELECT * FROM read_csv('de-lab/data/landing/orders/*.csv', all_varchar = true, union_by_name = true, filename = true) LIMIT 5;
SELECT * FROM read_json('de-lab/data/landing/support_tickets.jsonl') LIMIT 5;
SELECT unnest(restaurants, recursive := true) FROM read_json('de-lab/data/landing/restaurant_menus.json') LIMIT 5;

-- ── Data-quality patterns ─────────────────────────────────────────────────
-- duplicates
SELECT order_id, COUNT(*) FROM orders GROUP BY 1 HAVING COUNT(*) > 1;
-- orphans (FK check)
SELECT o.* FROM orders o ANTI JOIN restaurants r USING (restaurant_id);
-- freshness: newest data and lag
SELECT MAX(order_ts) AS newest, DATE '2026-10-15' - MAX(order_ts)::DATE AS days_behind FROM orders;
-- gaps in a daily series
SELECT d::DATE AS missing_day
FROM generate_series(DATE '2026-04-01', DATE '2026-10-14', INTERVAL 1 DAY) t(d)
ANTI JOIN (SELECT DISTINCT order_ts::DATE AS day FROM orders) o ON o.day = t.d;
-- volume anomaly: day vs trailing 7-day average
SELECT day, orders, ROUND(orders / AVG(orders) OVER w, 2) AS ratio_to_7d_avg
FROM (SELECT order_ts::DATE AS day, COUNT(*) AS orders FROM orders GROUP BY 1)
WINDOW w AS (ORDER BY day ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING)
QUALIFY ratio_to_7d_avg < 0.7 ORDER BY day;

-- ── Business metrics (the correct way) ───────────────────────────────────
-- revenue = delivered AND not refunded, minus promo, minus GST
SELECT date_trunc('month', o.order_ts) AS month,
       SUM(o.amount - o.promo_value - t.gst) AS revenue
FROM orders o JOIN order_taxes t USING (order_id) LEFT JOIN refunds f USING (order_id)
WHERE o.status = 'delivered' AND f.order_id IS NULL
GROUP BY 1 ORDER BY 1;

-- ── Modelling patterns ────────────────────────────────────────────────────
-- latest record per key (dedup)
SELECT * FROM orders QUALIFY row_number() OVER (PARTITION BY order_id ORDER BY order_ts DESC) = 1;
-- customer cohorts by signup month
SELECT date_trunc('month', c.signup_date) AS cohort, date_trunc('month', o.order_ts) AS month, COUNT(DISTINCT c.customer_id) AS active
FROM customers c JOIN orders o USING (customer_id) GROUP BY ALL ORDER BY ALL;
-- pivot: orders per city per status
PIVOT (SELECT c.city_name, o.status FROM orders o JOIN restaurants r USING (restaurant_id) JOIN cities c USING (city_id))
ON status USING COUNT(*);
