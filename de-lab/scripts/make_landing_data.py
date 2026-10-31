"""
make_landing_data.py  -  generates the "landing zone" files for the daily lab

The warehouse stops on 2026-10-14. These files are the NEXT week of data, as it
would arrive from the ordering app: one CSV per day, plus support tickets and a
nested restaurant menu feed. They are deliberately messy, so every lab day has a
real data-engineering problem to solve.

The random seed is fixed, so everyone gets exactly the same files.
Do not peek at reference/landing_answer_key.md until you have found the problems yourself.

RUN IT (from the repo root)
  python de-lab/scripts/make_landing_data.py
"""
import csv
import datetime as dt
import json
import math
import os
import random

import duckdb

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LANDING = f"{ROOT}/de-lab/data/landing"
rng = random.Random(2026)

wh = duckdb.connect(f"{ROOT}/warehouse.duckdb", read_only=True)
restaurants = wh.execute("SELECT restaurant_id, city_id, restaurant_name, cuisine FROM restaurants").fetchall()
customers_by_city = {}
for cid, city in wh.execute("SELECT customer_id, city_id FROM customers").fetchall():
    customers_by_city.setdefault(city, []).append(cid)
next_order_id = wh.execute("SELECT MAX(order_id) FROM orders").fetchone()[0] + 1
wh.close()

COLUMNS = ["order_id", "customer_id", "restaurant_id", "order_ts", "status", "amount", "promo_value",
           "payment_method", "cancel_reason"]


def make_order(day):
    global next_order_id
    rid, city, _, _ = rng.choice(restaurants)
    minutes = int(rng.triangular(8 * 60, 23 * 60 + 50, 20 * 60))
    ts = dt.datetime.combine(day, dt.time(0)) + dt.timedelta(minutes=minutes)
    item = round(math.exp(rng.gauss(math.log(330), 0.45)))
    amount = round(item * 1.05, 2)
    promo = float(min(round(item * 0.2), rng.choice([50, 75, 100]))) if rng.random() < 0.38 else 0.0
    cancelled = rng.random() < 0.09
    row = {
        "order_id": next_order_id, "customer_id": rng.choice(customers_by_city[city]), "restaurant_id": rid,
        "order_ts": ts.strftime("%Y-%m-%d %H:%M:%S"), "status": "cancelled" if cancelled else "delivered",
        "amount": amount, "promo_value": promo,
        "payment_method": rng.choices(["UPI", "Card", "Cash on delivery", "Wallet"], [62, 20, 12, 6])[0],
        "cancel_reason": rng.choice(["customer_cancelled", "restaurant_closed", "rider_unavailable"]) if cancelled else "",
    }
    next_order_id += 1
    return row


def write_csv(name, rows, columns=COLUMNS):
    with open(f"{LANDING}/orders/{name}", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


all_orders = []
for offset in range(7):
    day = dt.date(2026, 10, 15) + dt.timedelta(days=offset)
    rows = [make_order(day) for _ in range(rng.randint(780, 860))]
    all_orders += [dict(r) for r in rows]          # clean copies, before the defects are planted

    if day == dt.date(2026, 10, 16):                       # the app re-sent a chunk of rows
        rows += [dict(r) for r in rng.sample(rows, 25)]
    if day == dt.date(2026, 10, 17):                       # mixed timestamp formats, nulls, negatives
        for r in rng.sample(rows, 40):
            r["order_ts"] = dt.datetime.strptime(r["order_ts"], "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M")
        for r in rng.sample(rows, 10):
            r["customer_id"] = ""
        for r in rng.sample(rows, 3):
            r["amount"] = -r["amount"]
    if day == dt.date(2026, 10, 19):                       # orphan restaurants and inconsistent status case
        for r in rng.sample(rows, 8):
            r["restaurant_id"] = 9000 + rng.randint(1, 99)
        for r in rng.sample(rows, 60):
            r["status"] = r["status"].upper()
    if day == dt.date(2026, 10, 20):                       # the file never arrives
        continue
    if day == dt.date(2026, 10, 21):                       # late-arriving rows for 19 Oct
        rows += [make_order(dt.date(2026, 10, 19)) for _ in range(30)]

    rng.shuffle(rows)
    if day == dt.date(2026, 10, 18):                       # schema drift: renamed + new column
        drift_cols = [c if c != "amount" else "order_amount" for c in COLUMNS] + ["delivery_fee"]
        for r in rows:
            r["order_amount"] = r.pop("amount")
            r["delivery_fee"] = rng.choice([0, 0, 19, 29, 39])
        write_csv(f"orders_{day}.csv", rows, drift_cols)
    else:
        write_csv(f"orders_{day}.csv", rows)

# ---------------------------------------------------------------------------
# Support tickets: free text, one JSON object per line (for structured outputs / batches)
# ---------------------------------------------------------------------------
TEMPLATES = [
    ("Order {oid} came {mins} minutes late and the food was cold. I want a refund of Rs {amt}.", "late_delivery"),
    ("bhai order #{oid} me paneer missing tha!! please refund {amt}", "missing_items"),
    ("Got someone else's order ({oid}). Wrong order completely. Need full refund.", "wrong_order"),
    ("The biryani in order {oid} smelled bad, food quality is terrible. Refund Rs.{amt} pls", "food_quality"),
    ("Rider was very rude on order {oid}, but food was fine. No refund needed, just feedback.", "rider_behaviour"),
    ("Payment of Rs {amt} deducted twice for order {oid} via UPI!!", "payment_issue"),
    ("App crashed while placing order, charged but no order id shown. Please check.", "payment_issue"),
    ("order {oid} - {mins} min delay. not happy :(", "late_delivery"),
]
with open(f"{LANDING}/support_tickets.jsonl", "w") as f:
    for i in range(300):
        order = rng.choice(all_orders)
        text, _label = rng.choice(TEMPLATES)
        created = dt.datetime.strptime(order["order_ts"], "%Y-%m-%d %H:%M:%S") + dt.timedelta(hours=rng.randint(1, 30))
        ticket = {"ticket_id": f"T{50000 + i}", "created_at": created.isoformat(), "channel": rng.choice(["app", "email", "whatsapp"]),
                  "body": text.format(oid=order["order_id"], mins=rng.randint(25, 95), amt=round(order["amount"]))}
        f.write(json.dumps(ticket) + "\n")

# ---------------------------------------------------------------------------
# Restaurant menu feed: nested JSON from a partner API (for flattening / semi-structured data)
# ---------------------------------------------------------------------------
DISHES = {"North Indian": ["Paneer Butter Masala", "Dal Makhani", "Butter Naan"],
          "South Indian": ["Masala Dosa", "Idli Vada", "Filter Coffee"],
          "Biryani": ["Chicken Biryani", "Veg Biryani", "Raita"],
          "Chinese": ["Hakka Noodles", "Chilli Paneer", "Manchurian"],
          "Street Food": ["Pav Bhaji", "Pani Puri", "Vada Pav"],
          "Pizza": ["Margherita", "Farmhouse", "Garlic Bread"],
          "Desserts": ["Gulab Jamun", "Rasmalai", "Kulfi"],
          "Healthy": ["Quinoa Bowl", "Sprouts Salad", "Smoothie"],
          "Seafood": ["Fish Curry", "Prawn Fry", "Neer Dosa"]}
feed = {"source": "partner-menu-api", "extracted_at": "2026-10-21T06:00:00", "restaurants": []}
for rid, _city, name, cuisine in rng.sample(restaurants, 60):
    items = [{"item_id": f"{rid}-{n}", "name": dish, "price": {"amount": rng.choice([89, 129, 179, 249, 299]), "currency": "INR"},
              "tags": rng.sample(["veg", "spicy", "bestseller", "new", "jain"], rng.randint(0, 2)),
              "available": rng.random() > 0.1}
             for n, dish in enumerate(DISHES[cuisine])]
    feed["restaurants"].append({"restaurant_id": rid, "name": name, "cuisine": cuisine, "menu": {"items": items}})
with open(f"{LANDING}/restaurant_menus.json", "w") as f:
    json.dump(feed, f, indent=2)

print("Landing files written to de-lab/data/landing/")
for name in sorted(os.listdir(f"{LANDING}/orders")):
    print("  orders/" + name)
print("  support_tickets.jsonl\n  restaurant_menus.json")
