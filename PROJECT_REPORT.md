# Agentic KPI and Data-Quality Investigator

## Executive summary

This project is a finance and operations control system that combines PostgreSQL, Python, Power BI, and a bounded Anthropic investigator. It detects KPI shortfalls and data-quality issues, produces evidence-backed findings, and routes recommended actions to human review.

The system is read-only during investigation. It does not automatically change orders, payments, targets, or financial records.

## Business problem

Finance and operations teams need to know whether a revenue miss is a real business problem, a payment problem, or a data problem. A dashboard alone shows the result; this project adds validation, investigation, and auditability.

## Architecture

```text
PostgreSQL source tables
        ↓
Python PostgreSQL pipeline
        ↓
SQL KPI and quality views
        ↓
Deterministic investigator
        ↓
Approved JSON findings
        ↓
Anthropic explanation layer
        ↓
Power BI dashboards and human review
```

## PostgreSQL model

The `finance` schema contains:

- `customers` — customer region, segment, and signup date.
- `orders` — order value, discount, status, and customer link.
- `payments` — payment method, status, amount, and order link.
- `daily_kpi_targets` — daily revenue, payment-success, and order targets.
- `quality_issues_dated` — dated, traceable quality exceptions.
- `investigation_reviews` — human decisions and review notes.
- `pipeline_runs` — execution status, counts, timestamps, and errors.

Important controls include primary keys, foreign keys, approved status values, non-negative monetary values, and target-range checks.

## Python automation

Run the pipeline from the project root:

```powershell
python src/postgres_pipeline.py
```

The pipeline:

1. Upserts customers, orders, payments, and KPI targets.
2. Records a run in `finance.pipeline_runs`.
3. Exports `data/exports/daily_kpis.csv`.
4. Exports `data/exports/quality_issues.csv`.

Verified run:

```text
run_id: 3
status: success
orders_loaded: 139
payments_loaded: 138
issues_exported: 1
```

## Deterministic investigation

Run:

```powershell
python src/investigator.py
```

Output:

```text
data/exports/investigation_results.json
```

The investigator compares actual revenue and payment success with targets and attaches quality issue keys to affected dates. It returned five findings and one quality issue. The output explicitly marks itself as read-only.

## AI explanation layer

Run:

```powershell
python src/ai_investigator.py
```

The AI receives only `investigation_results.json`. It does not connect to PostgreSQL, execute SQL, or modify records. Output:

```text
data/exports/ai_investigation.md
```

The AI must return evidence, likely explanation, recommended human review, confidence, and `approval_required`.

## Power BI implementation

> Built and exercised locally; the `.pbix` file is not included in this repo.

The report contains:

- `KPI Dashboard` — date slicer, revenue, order count, payment success, variance, status, and revenue trend.
- `Data Quality Investigation` — date-aware issue table, issue type filter, and quality count.
- `Investigation Review` — issue key, severity, reviewer, decision, notes, and review date.

The model uses a shared `DimDate` table. Active date relationships filter orders, payments, KPI targets, and dated quality issues. The orders-to-payments relationship is many-to-one and single-direction; it is inactive where needed to avoid ambiguous filter paths.

Core measures:

- `Total Revenue`
- `Order Count`
- `Payment Success Rate`
- `Revenue Variance`
- `Revenue Status`
- `Quality Issue Count`

## Investigation findings

### Finding 1 — recurring revenue shortfall and payment degradation

Dates affected: `2026-01-05`, `2026-01-07`, `2026-01-09`, and `2026-01-10`.

| Date | Net revenue | Target | Gap | Payment success |
|---|---:|---:|---:|---:|
| 2026-01-05 | $5,743.58 | $5,755.25 | -$11.67 | 64.29% |
| 2026-01-07 | $3,435.61 | $3,529.36 | -$93.75 | 87.50% |
| 2026-01-09 | $4,697.16 | $4,916.50 | -$219.34 | 73.33% |
| 2026-01-10 | $6,162.68 | $6,504.88 | -$342.20 | 78.57% |

Three of four dates show both a revenue miss and lower payment success. This is a correlation, not proof of causation. Human review should inspect gateway decline codes, processor outages, order volume, refunds, discounts, and target assumptions.

Severity: medium. Confidence: medium. Approval required: yes.

### Finding 2 — quality exception for `O9999`

Date: `2026-08-17`.

- Net revenue: `$100.00`.
- Target revenue: missing.
- Payment success: `0.0%`.
- Quality issue key: `O9999`.
- Severity: high.

The record is internally inconsistent or incomplete: revenue exists while no successful payment is recorded, and there is no target baseline. It may be test data, a broken join, or a genuine failed-payment case. The system does not decide which.

Required human review:

1. Inspect the source order and payment records.
2. Check ingestion and ETL logs for `2026-08-17`.
3. Confirm whether `O9999` is synthetic/test data.
4. Record the decision in `finance.investigation_reviews`.
5. Do not alter or exclude the record without approval.

Severity: high. Confidence: high. Approval required: yes.

## Human approval control

The current review record is:

```text
Issue: O9999
Severity: high
Reviewer: Nikhil
Decision: needs_more_evidence
Action: inspect source order and ETL logs
```

This keeps AI recommendations separate from financial-record changes and creates an audit trail.

## Limitations

- The dataset is synthetic and small compared with a production finance system.
- Payment decline reasons are not present, so payment causation cannot be proven.
- Quality issue history is currently limited.
- AI output is explanatory, not authoritative.
- Power BI refresh and report validation must be repeated after larger data loads.

## Future improvements

- Add gateway decline codes and processor fields.
- Add region, segment, and product-level investigation outputs.
- Add issue lifecycle status and owner.
- Add scheduled pipeline execution.
- Add automated tests for KPI and quality rules.
- Publish the Power BI report with documented refresh credentials.

## Reproduction commands

```powershell
python -m pip install -r requirements.txt
python src/postgres_pipeline.py
python src/investigator.py
$env:ANTHROPIC_API_KEY = "YOUR_KEY"
python src/ai_investigator.py
```

Never commit the API key or database password.
