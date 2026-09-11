"""Read-only KPI and data-quality investigation output."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import psycopg

from postgres_pipeline import EXPORTS, connection_string


def investigate() -> dict:
    with psycopg.connect(connection_string()) as conn, conn.cursor() as cur:
        cur.execute(
            """SELECT k.order_date, k.order_count, k.net_revenue,
                      k.payment_success_rate, t.target_revenue,
                      t.target_payment_success_rate
               FROM finance.daily_kpis k
               LEFT JOIN finance.daily_kpi_targets t
                 ON t.metric_date = k.order_date
               ORDER BY k.order_date"""
        )
        kpis = cur.fetchall()
        cur.execute(
            """SELECT issue_type, issue_date, entity_type, issue_key
               FROM finance.quality_issues_dated
               ORDER BY issue_date, issue_key"""
        )
        issues = cur.fetchall()

    findings = []
    for date, order_count, revenue, payment_rate, target_revenue, target_rate in kpis:
        reasons = []
        if target_revenue is not None and revenue < target_revenue:
            reasons.append("revenue_below_target")
        if target_rate is not None and payment_rate < target_rate * 100:
            reasons.append("payment_success_below_target")
        date_issues = [issue for issue in issues if issue[1] == date]
        if date_issues:
            reasons.append("data_quality_issue")
        if reasons:
            findings.append({
                "date": date.isoformat(),
                "severity": "high" if "data_quality_issue" in reasons else "medium",
                "reasons": reasons,
                "net_revenue": float(revenue),
                "target_revenue": float(target_revenue) if target_revenue is not None else None,
                "payment_success_rate": float(payment_rate),
                "quality_issue_keys": [issue[3] for issue in date_issues],
            })

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "findings": findings,
        "quality_issue_count": len(issues),
        "read_only": True,
    }
    EXPORTS.mkdir(parents=True, exist_ok=True)
    (EXPORTS / "investigation_results.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    return result


if __name__ == "__main__":
    print(json.dumps(investigate(), indent=2))
