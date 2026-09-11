from pathlib import Path
import random
from datetime import date, timedelta

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"


def generate(seed: int = 42, days: int = 45) -> None:
    random.seed(seed)
    RAW.mkdir(parents=True, exist_ok=True)
    start = date(2026, 1, 1)

    customers = []
    for i in range(1, 31):
        customers.append({
            "customer_id": f"C{i:03d}",
            "region": random.choice(["India", "Europe", "North America", "APAC"]),
            "segment": random.choice(["SMB", "Mid-Market", "Enterprise"]),
            "signup_date": start - timedelta(days=random.randint(0, 180)),
        })

    orders, payments, order_no, payment_no = [], [], 1, 1
    for offset in range(days):
        order_date = start + timedelta(days=offset)
        for _ in range(random.randint(8, 18)):
            customer = random.choice(customers)
            amount = round(random.uniform(40, 800), 2)
            discount = round(amount * random.uniform(0, 0.15), 2)
            order_id = f"O{order_no:04d}"
            orders.append({
                "order_id": order_id,
                "customer_id": customer["customer_id"],
                "order_date": order_date,
                "product_category": random.choice(["Software", "Hardware", "Services"]),
                "quantity": random.randint(1, 5),
                "order_amount": amount,
                "discount_amount": discount,
                "status": random.choices(["completed", "pending", "cancelled"], [0.78, 0.15, 0.07])[0],
            })
            payments.append({
                "payment_id": f"P{payment_no:04d}",
                "order_id": order_id,
                "payment_date": order_date,
                "payment_method": random.choice(["card", "bank_transfer", "wallet"]),
                "payment_status": random.choices(["success", "failed", "pending"], [0.82, 0.10, 0.08])[0],
                "payment_amount": amount - discount,
            })
            order_no += 1
            payment_no += 1

    pd.DataFrame(customers).to_csv(RAW / "customers.csv", index=False)
    pd.DataFrame(orders).to_csv(RAW / "orders.csv", index=False)
    pd.DataFrame(payments).to_csv(RAW / "payments.csv", index=False)

    targets = []
    for offset in range(days):
        metric_date = start + timedelta(days=offset)
        daily_orders = [o for o in orders if o["order_date"] == metric_date and o["status"] != "cancelled"]
        revenue = sum(o["order_amount"] - o["discount_amount"] for o in daily_orders)
        targets.append({
            "metric_date": metric_date,
            "target_revenue": round(revenue * random.uniform(0.9, 1.1), 2),
            "target_payment_success_rate": 0.80,
            "target_order_count": len(daily_orders),
        })
    pd.DataFrame(targets).to_csv(RAW / "daily_kpi_targets.csv", index=False)


if __name__ == "__main__":
    generate()
    print(f"Generated source data in {RAW}")

