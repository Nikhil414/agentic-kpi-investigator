CREATE VIEW finance.quality_issues_dated AS
SELECT 'order_without_payment' AS issue_type,
    o.order_date AS issue_date,
    'order' AS entity_type,
    o.order_id AS issue_key
FROM finance.orders AS o
LEFT JOIN finance.payments AS pay
    ON pay.order_id = o.order_id
WHERE pay.order_id IS NULL
UNION ALL
SELECT 'payment_amount_mismatch' AS issue_type,
    pay.payment_date AS issue_date,
    'payment' AS entity_type,
    pay.payment_id AS issue_key
FROM finance.payments AS pay
JOIN finance.orders AS ord
    ON ord.order_id = pay.order_id
WHERE pay.payment_amount <> (ord.order_amount - ord.discount_amount);
