# de-lab conventions

## Databases
- `warehouse.duckdb` is production: open it with `read_only=True` (or `ATTACH ... (READ_ONLY)`). Enforced later by permissions (Day 4) and a hook (Day 9).
- All writes go to `de-lab/lab.duckdb` (tables) or `de-lab/pipeline/` (code).
- DuckDB API: `con.execute(sql).fetchone()`; `con.sql(...).fetchone()` raises AttributeError on the installed version.

## Business rules
- City of an order = the restaurant's city, never the customer's:
  `orders o JOIN restaurants r USING (restaurant_id) JOIN cities c ON c.city_id = r.city_id`
- Date filters are half-open: `order_ts >= DATE '2026-09-01' AND order_ts < DATE '2026-10-01'` (no BETWEEN on timestamps).

## Loading
- Read landing files with `all_varchar=true`; cast in the `stg_` step.
- Every loaded table keeps `_source_file` and `_loaded_at`.
- Tables are snake_case with a layer prefix: `raw_` (as landed), `stg_` (typed), `fct_` (business facts).
