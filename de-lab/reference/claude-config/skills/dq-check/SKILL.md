---
name: dq-check
description: Run a data-quality check on a landing file or lab table (row counts, duplicates, nulls, bad types, orphan keys, freshness) and report findings as a table. Use when the user asks to profile, validate or check the quality of data in de-lab.
---

# Data-quality check

Target: `$ARGUMENTS` (a landing file path like `de-lab/data/landing/orders/orders_2026-10-17.csv`, or a table in `de-lab/lab.duckdb`). If empty, check every file in `de-lab/data/landing/orders/`.

## Steps

1. Read the target with DuckDB, always as text first so nothing is silently coerced:
   `read_csv('<file>', all_varchar=true)`. Never open `warehouse.duckdb` except with `read_only=True`.
2. Compare the header with the expected order schema:
   `order_id, customer_id, restaurant_id, order_ts, status, amount, promo_value, payment_method, cancel_reason`.
   Report any renamed, missing or extra column as **schema drift**.
3. Run these checks and count failing rows for each:
   - duplicate `order_id` (and whether the duplicates are exact copies)
   - null / empty `customer_id`, `restaurant_id`, `order_ts`
   - `order_ts` that does not parse as `%Y-%m-%d %H:%M:%S`
   - `order_ts` whose date differs from the date in the file name (late-arriving data)
   - `amount` < 0 or `promo_value` > `amount`
   - `status` not in (`delivered`, `cancelled`) — note case problems separately
   - `restaurant_id` not present in `warehouse.duckdb` → `restaurants` (orphans)
4. Use `python de-lab/scripts/dq_check.py <file>` if it exists; otherwise write the SQL inline.

## Output

A markdown table: `check | failing rows | example value | severity (block / warn)`.
Then one line: **PASS** if no blocking check failed, otherwise **FAIL** and the suggested fix.
Do not modify any file.
