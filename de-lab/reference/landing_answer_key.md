# Landing zone answer key (spoilers)

Try to find these yourself first, with Claude, on Days 4, 5, 12 and 13.

| File | Planted problem | Count | Lab day |
|---|---|---|---|
| `orders_2026-10-15.csv` | Clean baseline | 795 rows | 4 |
| `orders_2026-10-16.csv` | Exact duplicate rows (app re-sent a batch) | 815 rows, 790 distinct `order_id` → 25 duplicates | 4, 5 |
| `orders_2026-10-17.csv` | Mixed timestamp format `DD/MM/YYYY HH:MM` | 40 rows | 4, 5 |
| | Missing `customer_id` | 10 rows | 4 |
| | Negative `amount` | 3 rows | 4 |
| `orders_2026-10-18.csv` | Schema drift: `amount` renamed to `order_amount`, new column `delivery_fee` | whole file | 12 |
| `orders_2026-10-19.csv` | Orphan `restaurant_id` (9001–9099, not in `restaurants`) | 8 rows | 4, 8 |
| | Upper-case status (`DELIVERED`, `CANCELLED`) | 60 rows | 5 |
| `orders_2026-10-20.csv` | **Missing file** (partition never arrived; its order_ids are a gap) | — | 14 |
| `orders_2026-10-21.csv` | Late-arriving rows whose `order_ts` is 19 Oct | 30 rows | 13 |
| `support_tickets.jsonl` | Free text, Hinglish, some tickets reference orders from the missing 20 Oct file, one template has no order id | 300 tickets | 16, 18 |
| `restaurant_menus.json` | Nested JSON: restaurants → menu.items[] → price{amount,currency}, tags[] | 60 restaurants, 180 items | 6 |

Regenerate the files at any time with `python de-lab/scripts/make_landing_data.py` (fixed seed, identical output).
