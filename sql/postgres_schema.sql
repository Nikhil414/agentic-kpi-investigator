-- PostgreSQL foundation for the Agentic KPI and Data-Quality Investigator.

CREATE SCHEMA IF NOT EXISTS finance;

CREATE TABLE IF NOT EXISTS finance.customers (
    customer_id VARCHAR(20) PRIMARY KEY,
    region VARCHAR(50) NOT NULL,
    segment VARCHAR(30) NOT NULL,
    signup_date DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS finance.orders (
    order_id VARCHAR(20) PRIMARY KEY,
    customer_id VARCHAR(20) NOT NULL REFERENCES finance.customers(customer_id),
    order_date DATE NOT NULL,
    product_category VARCHAR(30) NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    order_amount NUMERIC(12, 2) NOT NULL CHECK (order_amount >= 0),
    discount_amount NUMERIC(12, 2) NOT NULL DEFAULT 0 CHECK (discount_amount >= 0),
    status VARCHAR(20) NOT NULL CHECK (status IN ('completed', 'pending', 'cancelled'))
);

CREATE TABLE IF NOT EXISTS finance.payments (
    payment_id VARCHAR(20) PRIMARY KEY,
    order_id VARCHAR(20) NOT NULL REFERENCES finance.orders(order_id),
    payment_date DATE NOT NULL,
    payment_method VARCHAR(30) NOT NULL,
    payment_status VARCHAR(20) NOT NULL CHECK (payment_status IN ('success', 'failed', 'pending')),
    payment_amount NUMERIC(12, 2) NOT NULL CHECK (payment_amount >= 0)
);

CREATE TABLE IF NOT EXISTS finance.daily_kpi_targets (
    metric_date DATE PRIMARY KEY,
    target_revenue NUMERIC(12, 2) NOT NULL CHECK (target_revenue >= 0),
    target_payment_success_rate NUMERIC(5, 4) NOT NULL CHECK (target_payment_success_rate BETWEEN 0 AND 1),
    target_order_count INTEGER NOT NULL CHECK (target_order_count >= 0)
);

INSERT INTO finance.customers (customer_id, region, segment, signup_date) VALUES
('C001', 'India', 'SMB', '2025-12-01'),
('C002', 'Europe', 'Enterprise', '2025-11-15'),
('C003', 'APAC', 'Mid-Market', '2026-01-02')
ON CONFLICT (customer_id) DO NOTHING;

INSERT INTO finance.orders (order_id, customer_id, order_date, product_category, quantity, order_amount, discount_amount, status) VALUES
('O0001', 'C001', '2026-01-05', 'Software', 2, 500.00, 25.00, 'completed'),
('O0002', 'C002', '2026-01-05', 'Services', 1, 800.00, 0.00, 'completed'),
('O0003', 'C003', '2026-01-06', 'Hardware', 3, 300.00, 15.00, 'pending')
ON CONFLICT (order_id) DO NOTHING;

INSERT INTO finance.payments (payment_id, order_id, payment_date, payment_method, payment_status, payment_amount) VALUES
('P0001', 'O0001', '2026-01-05', 'card', 'success', 475.00),
('P0002', 'O0002', '2026-01-05', 'bank_transfer', 'success', 800.00),
('P0003', 'O0003', '2026-01-06', 'wallet', 'pending', 285.00)
ON CONFLICT (payment_id) DO NOTHING;

CREATE OR REPLACE VIEW finance.daily_kpis AS
SELECT
    o.order_date,
    COUNT(*) FILTER (WHERE o.status <> 'cancelled') AS order_count,
    COALESCE(SUM(o.order_amount - o.discount_amount) FILTER (WHERE o.status <> 'cancelled'), 0)::NUMERIC(12, 2) AS net_revenue,
    ROUND(AVG(CASE WHEN p.payment_status = 'success' THEN 1.0 ELSE 0.0 END) * 100, 2) AS payment_success_rate
FROM finance.orders o
LEFT JOIN finance.payments p ON p.order_id = o.order_id
GROUP BY o.order_date;

CREATE OR REPLACE VIEW finance.quality_issues AS
SELECT 'order_without_payment' AS issue_type, o.order_id AS issue_key
FROM finance.orders o
LEFT JOIN finance.payments p ON p.order_id = o.order_id
WHERE p.order_id IS NULL
UNION ALL
SELECT 'payment_amount_mismatch', p.payment_id
FROM finance.payments p
JOIN finance.orders o ON o.order_id = p.order_id
WHERE p.payment_amount <> o.order_amount - o.discount_amount;

CREATE OR REPLACE VIEW finance.quality_issues_dated AS
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

CREATE TABLE IF NOT EXISTS finance.investigation_reviews (
    review_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    issue_key VARCHAR(20) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high')),
    reviewer VARCHAR(100) NOT NULL,
    decision VARCHAR(30) NOT NULL,
    reviewer_notes TEXT,
    reviewed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
