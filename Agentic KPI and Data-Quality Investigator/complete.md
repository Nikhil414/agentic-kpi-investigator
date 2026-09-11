Agentic KPI and Data-Quality Investigator
Do not begin with the AI agent. Build the reliable SQL analytics system first, then add AI.
Final project goal
A finance/operations company receives daily transaction files. Your system should:
load data
→ validate data quality
→ calculate KPIs
→ detect anomalies
→ investigate the cause
→ generate a report
→ escalate uncertain issues
Recommended stack
PostgreSQL or DuckDB
SQL
Python only for loading files and running SQL
GitHub
Optional later: OpenAI API + LangGraph
Optional dashboard later: Power BI or Streamlit
Use DuckDB first because it is lightweight and requires no database server. Move to PostgreSQL later if needed.
Step 1: Create the project folder
finance-kpi-agent/
│
├── data/
│ ├── raw/
│ └── processed/
├── sql/
│ ├── 01_staging.sql
│ ├── 02_quality_checks.sql
│ ├── 03_metrics.sql
│ └── 04_investigations.sql
├── src/
├── reports/
├── tests/
├── README.md
└── requirements.txt
Step 2: Create a small business dataset
Start with only four tables:
customers
orders
payments
daily_kpi_targets
customers
customer_id
region
segment
signup_date
orders
order_id
customer_id
order_date
product_category
quantity
order_amount
discount_amount
status
payments
payment_id
order_id
payment_date
payment_method
payment_status
payment_amount
daily_kpi_targets
metric_date
target_revenue
target_payment_success_rate
target_order_count
Generate around 30–60 days of data. Use synthetic data so you can deliberately create failures later.
Step 3: Define the business questions
Your project should answer:
What was daily revenue?
What was the payment-success rate?
Which regions caused revenue decline?
Which products caused margin or revenue leakage?
Are there duplicate orders?
Are any orders missing payments?
Is any day’s data missing?
Did a broken join double-count revenue?
Which KPI breached its target?
What should the operations manager investigate?
Step 4: Learn only the SQL required
Study in this order:
Days 1–2: Fundamentals
SELECT
WHERE
ORDER BY
CASE
NULL
date filtering
COUNT
SUM
AVG
Days 3–4: Joins and aggregation
INNER JOIN
LEFT JOIN
GROUP BY
HAVING
COUNT(DISTINCT ...)
avoiding duplicate joins
table grain
Days 5–6: Analyst SQL
CTEs
subqueries
ROW_NUMBER()
RANK()
LAG()
running totals
month-over-month change
Day 7: Data-quality SQL
duplicates
missing dates
null keys
invalid statuses
unmatched foreign keys
reconciliation totals
Step 5: Build the staging layer
Clean names, types and statuses first.
Example:
CREATE OR REPLACE VIEW stg_orders AS
SELECT
CAST(order_id AS VARCHAR) AS order_id,
CAST(customer_id AS VARCHAR) AS customer_id,
CAST(order_date AS DATE) AS order_date,
LOWER(TRIM(product_category)) AS product_category,
CAST(quantity AS INTEGER) AS quantity,
CAST(order_amount AS DECIMAL(12, 2)) AS order_amount,
CAST(discount_amount AS DECIMAL(12, 2)) AS discount_amount,
LOWER(TRIM(status)) AS status
FROM raw_orders;
Do not calculate business KPIs directly from messy raw tables.
Step 6: Build quality checks
Create a SQL file containing checks such as:
-- Duplicate orders
SELECT order_id, COUNT(_) AS row_count
FROM stg_orders
GROUP BY order_id
HAVING COUNT(_) > 1;
-- Orders without customers
SELECT o.order_id
FROM stg_orders o
LEFT JOIN stg_customers c
ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL;
-- Missing daily data
WITH date_range AS (
SELECT MIN(order_date) AS min_date,
MAX(order_date) AS max_date
FROM stg_orders
),
expected_dates AS (
SELECT _
FROM generate_series(
(SELECT min_date FROM date_range),
(SELECT max_date FROM date_range),
INTERVAL '1 day'
) AS dates(order_date)
)
SELECT e.order_date
FROM expected_dates e
LEFT JOIN (
SELECT DISTINCT order_date
FROM stg_orders
) o USING (order_date)
WHERE o.order_date IS NULL;
For DuckDB, this syntax works with minor adjustments if necessary.
Step 7: Build the KPI layer
CREATE OR REPLACE VIEW daily_kpis AS
SELECT
o.order_date,
COUNT(DISTINCT o.order_id) AS order_count,
SUM(o.order_amount - o.discount_amount) AS net_revenue,
COUNT(DISTINCT CASE
WHEN p.payment_status = 'success' THEN o.order_id
END) _ 1.0 / COUNT(DISTINCT o.order_id) AS payment_success_rate
FROM stg_orders o
LEFT JOIN stg_payments p
ON o.order_id = p.order_id
WHERE o.status <> 'cancelled'
GROUP BY o.order_date;
Then compare against targets:
SELECT
k._,
t.target_revenue,
k.net_revenue - t.target_revenue AS revenue_variance,
CASE
WHEN k.net_revenue < t.target_revenue THEN 'below_target'
ELSE 'on_target'
END AS revenue_status
FROM daily_kpis k
LEFT JOIN daily_kpi_targets t
ON k.order_date = t.metric_date;
Step 8: Add anomaly detection
Start with simple, explainable rules:
WITH baseline AS (
SELECT
order_date,
net_revenue,
AVG(net_revenue) OVER (
ORDER BY order_date
ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
) AS previous_7_day_avg
FROM daily_kpis
)
SELECT _,
CASE
WHEN previous_7_day_avg IS NOT NULL
AND net_revenue < previous_7_day_avg _ 0.80
THEN 'revenue_drop'
WHEN previous_7_day_avg IS NOT NULL
AND net_revenue > previous_7_day_avg _ 1.50
THEN 'revenue_spike'
ELSE 'normal'
END AS anomaly_type
FROM baseline;
Avoid machine learning initially. Explainable thresholds are better for an entry-level analyst project.
Step 9: Add investigation queries
If revenue drops, investigate region:
SELECT
c.region,
COUNT(DISTINCT o.order_id) AS orders,
SUM(o.order_amount - o.discount_amount) AS revenue
FROM stg_orders o
JOIN stg_customers c
ON o.customer_id = c.customer_id
WHERE o.order_date = DATE '2026-01-15'
GROUP BY c.region
ORDER BY revenue;
Investigate product:
SELECT
product_category,
SUM(order_amount - discount_amount) AS revenue,
COUNT(_) AS orders
FROM stg_orders
WHERE order_date = DATE '2026-01-15'
GROUP BY product_category
ORDER BY revenue;
Investigate payment status:
SELECT
payment_status,
COUNT(_) AS payments,
SUM(payment_amount) AS amount
FROM stg_payments
WHERE payment_date = DATE '2026-01-15'
GROUP BY payment_status;
Step 10: Create deliberate failures
Add these one at a time:
Delete one day of orders.
Duplicate five orders.
Add orders with invalid customer IDs.
Change one payment status to an invalid value.
Duplicate the payment table before joining it.
Reduce payment success in one region.
Add a sudden revenue spike.
Your system should detect the problem and identify the likely cause.
Step 11: Add Python only after SQL works
Python should:
Load CSV files
Execute SQL files
Save quality-check results
Save KPI output
Create a report
Write an incident log
Keep the business logic in SQL. That makes your SQL skill visible.
Step 12: Add the agent last
The agent should call only approved read-only tools:
run_quality_checks()
calculate_kpis()
check_missing_dates()
investigate_by_region()
investigate_by_product()
investigate_by_payment_status()
create_incident_report()
The agent’s job is to choose the investigation path and summarize evidence.
Example:
Revenue is 24% below the 7-day baseline.

I checked:

- data freshness: passed
- duplicate orders: passed
- payment success: failed
- regional revenue: Europe declined 42%
- product mix: normal

Likely cause:
Payment failures in Europe.

Confidence:
0.88

Action:
Escalate to payment operations.
Your first 3 days
Day 1
Create the folder.
Install DuckDB and Python.
Create the four tables.
Generate or download data.
Write five basic SQL queries.
Day 2
Build staging views.
Write duplicate, null, missing-key and missing-date checks.
Document table grain and KPI definitions.
Day 3
Build daily KPI queries.
Add target comparison.
Add one anomaly rule.
Test one intentional failure.
Do not touch LangGraph or the OpenAI API until the SQL quality and KPI layers work correctly. That is the part interviewers will inspect most closely.
