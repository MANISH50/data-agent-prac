# Day 8 · dbt tests with Claude: encode data contracts as code

**Level:** 2 Customize · **Time:** 75 min · **Claude concepts:** test-first prompting, running the feedback loop (`dbt build`) inside Claude, iterating on failures

## Scenario
The checker from Day 4 lives outside dbt. The analytics team wants the same guarantees inside the dbt project, so a bad model can never reach dashboards.

## Goal
Add sources for the lab tables and tests that would have caught every landing defect, then make `dbt build` pass.

## Steps to implement
1. Install dbt: `pip install -r requirements-dbt.txt`.
2. Ask Claude to write tests **first**:
   `In dbt_project, add the lab's stg_orders (de-lab/lab.duckdb) as a source "lab" and write tests in schema.yml: unique + not_null on order_id, not_null customer_id, accepted_values on status, relationships from restaurant_id to stg_restaurants, and an expression test that amount >= 0. Don't change models yet. Run dbt build --profiles-dir . from dbt_project and show me which tests fail.`
   (Hint: `profiles.yml` needs a second `attach` entry for `../de-lab/lab.duckdb` with alias `lab`, read-only.)
3. Read the failures. Are they real data issues or test mistakes? Discuss with Claude before changing anything.
4. Add a **freshness / completeness** test: a singular test in `dbt_project/tests/` that fails when a day between the min and max `order_date` has zero orders (catches the missing 20 Oct file).
5. Iterate until the only failing tests are the ones you **expect** to fail, then set those to `severity: warn` with a comment explaining why.
6. Run a single model's tests: `dbt test --profiles-dir . --select fct_orders`.

## Core learnings
- Write the tests before the fix, so Claude is optimising for a contract you agreed, not for "make it green".
- Let Claude run the feedback loop (`dbt build`), read the errors, and fix. This loop is where agents shine.
- Watch for "fixing" tests by weakening them. Ask Claude to justify every change to a test.
- `schema.yml` descriptions double as documentation **and** agent context (see `agent.py --context`).

## Done when
`dbt build` passes with documented warnings, and the missing-day test fails on the current data.
