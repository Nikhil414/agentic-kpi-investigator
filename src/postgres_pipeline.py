"""Load approved CSV inputs into PostgreSQL and export KPI results."""

from __future__ import annotations

import csv
import os
from datetime import datetime, timezone
from pathlib import Path

import psycopg


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
EXPORTS = ROOT / "data" / "exports"


def connection_string() -> str:
    return os.getenv(
        "DATABASE_URL",
        "host=127.0.0.1 port=5432 dbname=postgres user=postgres password=admin",
    )


def read_csv(name: str) -> list[dict[str, str]]:
    with (RAW / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load(conn: psycopg.Connection) -> None:
    customers = read_csv("customers.csv")
    orders = read_csv("orders.csv")
    payments = read_csv("payments.csv")
    targets = read_csv("daily_kpi_targets.csv")

    with conn.cursor() as cur:
        cur.executemany(
            """INSERT INTO finance.customers
               (customer_id, region, segment, signup_date)
               VALUES (%(customer_id)s, %(region)s, %(segment)s, %(signup_date)s)
               ON CONFLICT (customer_id) DO UPDATE SET
                 region = EXCLUDED.region, segment = EXCLUDED.segment,
                 signup_date = EXCLUDED.signup_date""",
            customers,
        )
        cur.executemany(
            """INSERT INTO finance.orders
               (order_id, customer_id, order_date, product_category, quantity,
                order_amount, discount_amount, status)
               VALUES (%(order_id)s, %(customer_id)s, %(order_date)s,
                       %(product_category)s, %(quantity)s, %(order_amount)s,
                       %(discount_amount)s, %(status)s)
               ON CONFLICT (order_id) DO UPDATE SET
                 customer_id = EXCLUDED.customer_id, order_date = EXCLUDED.order_date,
                 product_category = EXCLUDED.product_category,
                 quantity = EXCLUDED.quantity, order_amount = EXCLUDED.order_amount,
                 discount_amount = EXCLUDED.discount_amount, status = EXCLUDED.status""",
            orders,
        )
        cur.executemany(
            """INSERT INTO finance.payments
               (payment_id, order_id, payment_date, payment_method,
                payment_status, payment_amount)
               VALUES (%(payment_id)s, %(order_id)s, %(payment_date)s,
                       %(payment_method)s, %(payment_status)s, %(payment_amount)s)
               ON CONFLICT (payment_id) DO UPDATE SET
                 order_id = EXCLUDED.order_id, payment_date = EXCLUDED.payment_date,
                 payment_method = EXCLUDED.payment_method,
                 payment_status = EXCLUDED.payment_status,
                 payment_amount = EXCLUDED.payment_amount""",
            payments,
        )
        cur.executemany(
            """INSERT INTO finance.daily_kpi_targets
               (metric_date, target_revenue, target_payment_success_rate,
                target_order_count)
               VALUES (%(metric_date)s, %(target_revenue)s,
                       %(target_payment_success_rate)s, %(target_order_count)s)
               ON CONFLICT (metric_date) DO UPDATE SET
                 target_revenue = EXCLUDED.target_revenue,
                 target_payment_success_rate = EXCLUDED.target_payment_success_rate,
                 target_order_count = EXCLUDED.target_order_count""",
            targets,
        )


def export_query(conn: psycopg.Connection, filename: str, query: str) -> int:
    EXPORTS.mkdir(parents=True, exist_ok=True)
    with conn.cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()
        headers = [column.name for column in cur.description]
    with (EXPORTS / filename).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)
    return len(rows)


def run() -> dict[str, int | str]:
    started = datetime.now(timezone.utc)
    with psycopg.connect(connection_string()) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """CREATE TABLE IF NOT EXISTS finance.pipeline_runs (
                    run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    started_at TIMESTAMPTZ NOT NULL,
                    finished_at TIMESTAMPTZ,
                    status VARCHAR(20) NOT NULL,
                    orders_loaded INTEGER NOT NULL DEFAULT 0,
                    payments_loaded INTEGER NOT NULL DEFAULT 0,
                    issues_exported INTEGER NOT NULL DEFAULT 0,
                    error_message TEXT
                )"""
            )
            cur.execute(
                "INSERT INTO finance.pipeline_runs (started_at, status) VALUES (%s, 'running') RETURNING run_id",
                (started,),
            )
            run_id = cur.fetchone()[0]
        try:
            load(conn)
            issues = export_query(
                conn,
                "quality_issues.csv",
                "SELECT * FROM finance.quality_issues_dated ORDER BY issue_date, issue_key",
            )
            export_query(
                conn,
                "daily_kpis.csv",
                "SELECT * FROM finance.daily_kpis ORDER BY order_date",
            )
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE finance.pipeline_runs
                       SET finished_at = %s, status = 'success',
                           orders_loaded = (SELECT COUNT(*) FROM finance.orders),
                           payments_loaded = (SELECT COUNT(*) FROM finance.payments),
                           issues_exported = %s
                       WHERE run_id = %s""",
                    (datetime.now(timezone.utc), issues, run_id),
                )
            conn.commit()
            return {"run_id": run_id, "status": "success", "issues_exported": issues}
        except Exception as error:
            conn.rollback()
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE finance.pipeline_runs
                       SET finished_at = %s, status = 'failed', error_message = %s
                       WHERE run_id = %s""",
                    (datetime.now(timezone.utc), str(error), run_id),
                )
            conn.commit()
            raise


if __name__ == "__main__":
    print(run())
