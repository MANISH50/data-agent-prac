# de-lab journal

One chat session per day, grouped by level (session tag `de-lab:level-N`).
Branch per level: `de-lab/level-N`.

## Progress

```
L1  [x] 1  [ ] 2  [ ] 3  [ ] 4  [ ] 5  [ ] 6
L2  [ ] 7  [ ] 8  [ ] 9  [ ] 10 [ ] 11 [ ] 12 [ ] 13
L3  [ ] 14 [ ] 15 [ ] 16 [ ] 17 [ ] 18
L4  [ ] 19 [ ] 20 [ ] 21 [ ] 22
L5  [ ] 23 [ ] 24 [ ] 25 [ ] 26 [ ] 27 [ ] 28
```

## Level 1 · Foundations (Days 1–6) · branch `de-lab/level-1`

- **Day 1 (2026-10-31):** Claude mapped repo + warehouse and proved grain/joins with anti-join checks (0 orphans; Sept net_revenue ₹78,09,309 vs SUM(amount) ₹1,02,13,435, +31%); I had to correct its DuckDB snippet (`.sql().fetchone()` removed in the new version → use `.execute()`); rule for CLAUDE.md: "use `con.execute(...)` for DuckDB, and city always comes from the restaurant".

## Level 2 · Customize Claude for your team (Days 7–13) · branch `de-lab/level-2`

## Level 3 · Headless Claude and the API (Days 14–18) · branch `de-lab/level-3`

## Level 4 · Production agents (Days 19–22) · branch `de-lab/level-4`

## Level 5 · Tokens & context engineering (Days 23–28) · branch `de-lab/level-5`
