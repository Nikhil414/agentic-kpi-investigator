CREATE OR REPLACE TABLE quality_issues AS
WITH issues AS (
  SELECT 'duplicate_order' issue_type, order_id issue_key FROM stg_orders GROUP BY order_id HAVING COUNT(*) > 1
  UNION ALL
  SELECT 'order_without_customer', o.order_id FROM stg_orders o LEFT JOIN stg_customers c USING (customer_id) WHERE c.customer_id IS NULL
  UNION ALL
  SELECT 'order_without_payment', o.order_id FROM stg_orders o LEFT JOIN stg_payments p USING (order_id) WHERE p.order_id IS NULL
  UNION ALL
  SELECT 'invalid_order_status', order_id FROM stg_orders WHERE status NOT IN ('completed', 'pending', 'cancelled')
  UNION ALL
  SELECT 'invalid_payment_status', payment_id FROM stg_payments WHERE payment_status NOT IN ('success', 'failed', 'pending')
  UNION ALL
  SELECT 'negative_order_value', order_id FROM stg_orders WHERE order_amount < 0 OR discount_amount < 0
)
SELECT * FROM issues;

CREATE OR REPLACE TABLE missing_dates AS
WITH dates AS (
  SELECT UNNEST(generate_series(MIN(order_date), MAX(order_date), INTERVAL 1 DAY))::DATE order_date FROM stg_orders
)
SELECT d.order_date FROM dates d LEFT JOIN (SELECT DISTINCT order_date FROM stg_orders) o USING (order_date)
WHERE o.order_date IS NULL;

