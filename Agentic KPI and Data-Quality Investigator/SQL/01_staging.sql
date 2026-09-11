CREATE OR REPLACE TABLE stg_customers AS
SELECT CAST(customer_id AS VARCHAR) customer_id,
    LOWER(TRIM(region)) region,
    LOWER(TRIM(segment)) segment,
    CAST(signup_date AS DATE) signup_date
FROM read_csv_auto('data/raw/customers.csv');
CREATE OR REPLACE TABLE stg_orders AS
SELECT CAST(order_id AS VARCHAR) order_id,
    CAST(customer_id AS VARCHAR) customer_id,
    CAST(order_date AS DATE) order_date,
    LOWER(TRIM(product_category)) product_category,
    CAST(quantity AS INTEGER) quantity,
    CAST(order_amount AS DECIMAL(12, 2)) order_amount,
    CAST(discount_amount AS DECIMAL(12, 2)) discount_amount,
    LOWER(TRIM(status)) status
FROM read_csv_auto('data/raw/orders.csv');
CREATE OR REPLACE TABLE stg_payments AS
SELECT CAST(payment_id AS VARCHAR) payment_id,
    CAST(order_id AS VARCHAR) order_id,
    CAST(payment_date AS DATE) payment_date,
    LOWER(TRIM(payment_method)) payment_method,
    LOWER(TRIM(payment_status)) payment_status,
    CAST(payment_amount AS DECIMAL(12, 2)) payment_amount
FROM read_csv_auto('data/raw/payments.csv');
CREATE OR REPLACE TABLE stg_daily_kpi_targets AS
SELECT CAST(metric_date AS DATE) metric_date,
    CAST(target_revenue AS DECIMAL(12, 2)) target_revenue,
    CAST(target_payment_success_rate AS DECIMAL(5, 4)) target_payment_success_rate,
    CAST(target_order_count AS INTEGER) target_order_count
FROM read_csv_auto('data/raw/daily_kpi_targets.csv');