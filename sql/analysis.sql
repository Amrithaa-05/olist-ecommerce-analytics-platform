USE olist_db;
-- ============================================================
-- 1. BASIC DATA CHECKS
-- ============================================================

-- Total orders
SELECT COUNT(*) AS total_orders
FROM orders_clean;

-- Total customers
SELECT COUNT(*) AS total_customers
FROM customers_clean;

-- Total order items
SELECT COUNT(*) AS total_order_items
FROM order_items_clean;

-- Total products
SELECT COUNT(*) AS total_products
FROM products_clean;

-- Total payments
SELECT COUNT(*) AS total_payments
FROM payments_clean;

-- Total reviews
SELECT COUNT(*) AS total_reviews
FROM reviews_clean;

-- Total sellers
SELECT COUNT(*) AS total_sellers
FROM sellers_clean;


-- ============================================================
-- 2. REVENUE ANALYSIS
-- ============================================================

-- Total revenue
SELECT
    SUM(payment_value) AS total_revenue
FROM payments_clean;


-- Revenue by payment type
SELECT
    payment_type,
    SUM(payment_value) AS total_revenue
FROM payments_clean
GROUP BY payment_type
ORDER BY total_revenue DESC;


-- ============================================================
-- 3. ORDER STATUS ANALYSIS
-- ============================================================

SELECT
    order_status,
    COUNT(*) AS order_count
FROM orders_clean
GROUP BY order_status
ORDER BY order_count DESC;


-- ============================================================
-- 4. DELIVERY PERFORMANCE
-- ============================================================

-- Average delivery time
SELECT
    AVG(delivery_days) AS avg_delivery_days
FROM orders_clean
WHERE delivery_days IS NOT NULL;


-- Number of delayed orders
SELECT
    SUM(is_delayed) AS delayed_orders
FROM orders_clean;


-- Delayed vs non-delayed orders
SELECT
    is_delayed,
    COUNT(*) AS order_count
FROM orders_clean
GROUP BY is_delayed;


-- ============================================================
-- 5. TOP PRODUCTS
-- ============================================================

SELECT
    oi.product_id,
    SUM(oi.price) AS total_sales
FROM order_items_clean oi
GROUP BY oi.product_id
ORDER BY total_sales DESC
LIMIT 10;


-- ============================================================
-- 6. TOP SELLERS
-- ============================================================

SELECT
    oi.seller_id,
    SUM(oi.price) AS total_sales
FROM order_items_clean oi
GROUP BY oi.seller_id
ORDER BY total_sales DESC
LIMIT 10;


-- ============================================================
-- 7. CUSTOMER ANALYSIS
-- ============================================================

-- Number of orders per customer
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders_clean
GROUP BY customer_id
ORDER BY order_count DESC
LIMIT 10;


-- ============================================================
-- 8. REVIEW ANALYSIS
-- ============================================================

SELECT
    review_score,
    COUNT(*) AS review_count
FROM reviews_clean
GROUP BY review_score
ORDER BY review_score;


-- ============================================================
-- 9. REVENUE BY PRODUCT CATEGORY
-- ============================================================

SELECT
    p.product_category_name,
    SUM(oi.price) AS total_revenue
FROM order_items_clean oi
JOIN products_clean p
    ON oi.product_id = p.product_id
GROUP BY p.product_category_name
ORDER BY total_revenue DESC
LIMIT 10;


-- ============================================================
-- 10. REVENUE BY SELLER STATE
-- ============================================================

SELECT
    s.seller_state,
    SUM(oi.price) AS total_revenue
FROM order_items_clean oi
JOIN sellers_clean s
    ON oi.seller_id = s.seller_id
GROUP BY s.seller_state
ORDER BY total_revenue DESC;


-- ============================================================
-- 11. ORDERS AND CUSTOMERS
-- ============================================================

SELECT
    o.order_id,
    o.order_status,
    c.customer_city,
    c.customer_state
FROM orders_clean o
JOIN customers_clean c
    ON o.customer_id = c.customer_id
LIMIT 10;


-- ============================================================
-- 12. DELIVERY PERFORMANCE BY ORDER STATUS
-- ============================================================

SELECT
    order_status,
    AVG(delivery_days) AS avg_delivery_days,
    AVG(delivery_delay_days) AS avg_delay_days
FROM orders_clean
GROUP BY order_status
ORDER BY avg_delivery_days DESC;

-- ============================================================
-- 13. CUSTOMER SPENDING
-- ============================================================

WITH customer_spending AS (
    SELECT
        o.customer_id,
        SUM(p.payment_value) AS total_spending
    FROM orders_clean o
    JOIN payments_clean p
        ON o.order_id = p.order_id
    GROUP BY o.customer_id
)
SELECT
    customer_id,
    total_spending
FROM customer_spending
ORDER BY total_spending DESC
LIMIT 10;

-- ============================================================
-- 14. MONTHLY REVENUE USING CTE
-- ============================================================

WITH monthly_revenue AS (
    SELECT
        YEAR(o.order_purchase_timestamp) AS order_year,
        MONTH(o.order_purchase_timestamp) AS order_month,
        SUM(p.payment_value) AS total_revenue
    FROM orders_clean o
    JOIN payments_clean p
        ON o.order_id = p.order_id
    GROUP BY
        YEAR(o.order_purchase_timestamp),
        MONTH(o.order_purchase_timestamp)
)
SELECT
    order_year,
    order_month,
    total_revenue
FROM monthly_revenue
ORDER BY
    order_year,
    order_month;

    -- ============================================================
-- 15. CUSTOMER ORDER FREQUENCY + SPENDING
-- ============================================================

WITH customer_summary AS (
    SELECT
        o.customer_id,
        COUNT(DISTINCT o.order_id) AS total_orders,
        SUM(p.payment_value) AS total_spending
    FROM orders_clean o
    JOIN payments_clean p
        ON o.order_id = p.order_id
    GROUP BY o.customer_id
)
SELECT
    customer_id,
    total_orders,
    total_spending
FROM customer_summary
ORDER BY total_spending DESC
LIMIT 10;

-- ============================================================
-- 16. CUSTOMER RECENCY
-- ============================================================

WITH customer_recency AS (
    SELECT
        customer_id,
        MAX(order_purchase_timestamp) AS last_purchase_date
    FROM orders_clean
    WHERE order_status = 'delivered'
    GROUP BY customer_id
)
SELECT
    customer_id,
    last_purchase_date,
    DATEDIFF(
        '2018-10-17',
        last_purchase_date
    ) AS recency_days
FROM customer_recency
ORDER BY recency_days ASC
LIMIT 10;

-- ============================================================
-- 17. COMPLETE RFM
-- ============================================================
--
WITH rfm AS (
    SELECT
        c.customer_unique_id,
        DATEDIFF(
            '2018-10-17',
            MAX(o.order_purchase_timestamp)
        ) AS recency,
        COUNT(DISTINCT o.order_id) AS frequency,
        SUM(p.payment_value) AS monetary
    FROM orders_clean o
    JOIN customers_clean c
        ON o.customer_id = c.customer_id
    JOIN payments_clean p
        ON o.order_id = p.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
)

SELECT *
FROM rfm
ORDER BY monetary DESC
LIMIT 10;

-- ============================================================
-- 18. RFM SCORING
-- ============================================================
-- ============================================================
-- 18. RFM SCORING
-- ============================================================

WITH rfm AS (
    SELECT
        c.customer_unique_id,

        DATEDIFF(
            '2018-10-17',
            MAX(o.order_purchase_timestamp)
        ) AS recency,

        COUNT(DISTINCT o.order_id) AS frequency,

        SUM(p.payment_value) AS monetary

    FROM orders_clean o
    JOIN customers_clean c
        ON o.customer_id = c.customer_id

    JOIN payments_clean p
        ON o.order_id = p.order_id

    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
),
rfm_scores AS (
    SELECT
        customer_unique_id,
        recency,
        frequency,
        monetary,

        CASE
            WHEN recency <= 90 THEN 5
            WHEN recency <= 180 THEN 4
            WHEN recency <= 270 THEN 3
            WHEN recency <= 365 THEN 2
            ELSE 1
        END AS recency_score,

        CASE
            WHEN frequency >= 5 THEN 5
            WHEN frequency = 4 THEN 4
            WHEN frequency = 3 THEN 3
            WHEN frequency = 2 THEN 2
            ELSE 1
        END AS frequency_score,

        CASE
            WHEN monetary >= 1000 THEN 5
            WHEN monetary >= 500 THEN 4
            WHEN monetary >= 250 THEN 3
            WHEN monetary >= 100 THEN 2
            ELSE 1
        END AS monetary_score
    FROM rfm
)

SELECT *
FROM rfm_scores
LIMIT 10;

-- ============================================================
-- 19. CUSTOMER SEGMENTATION
-- ============================================================

CREATE OR REPLACE VIEW customer_segmentation AS
SELECT
    customer_unique_id,
    recency,
    frequency,
    monetary,
    recency_score,
    frequency_score,
    monetary_score,

    CASE
        WHEN recency_score >= 4
             AND frequency_score >= 4
             AND monetary_score >= 4
            THEN 'Champions'

        WHEN recency_score >= 4
             AND frequency_score >= 2
            THEN 'Loyal Customers'

        WHEN recency_score >= 4
             AND frequency_score = 1
            THEN 'New Customers'

        WHEN recency_score <= 2
             AND frequency_score >= 2
            THEN 'At Risk'

        WHEN recency_score <= 2
             AND frequency_score = 1
             AND monetary_score >= 3
            THEN 'High-Value At Risk'

        WHEN recency_score <= 2
             AND frequency_score = 1
             AND monetary_score <= 2
            THEN 'Lost / Inactive'

        ELSE 'Regular Customers'
    END AS customer_segment

FROM rfm_scores;

-- ============================================================
-- 20. MONTHLY SALES & REVENUE TREND
-- ============================================================

SELECT
    YEAR(o.order_purchase_timestamp) AS order_year,
    MONTH(o.order_purchase_timestamp) AS order_month,

    COUNT(DISTINCT o.order_id) AS total_orders,

    COUNT(DISTINCT c.customer_unique_id) AS unique_customers,

    ROUND(SUM(p.payment_value), 2) AS total_revenue,

    ROUND(
        SUM(p.payment_value) / COUNT(DISTINCT o.order_id),
        2
    ) AS average_order_value

FROM orders_clean o

JOIN customers_clean c
    ON o.customer_id = c.customer_id

JOIN payments_clean p
    ON o.order_id = p.order_id

WHERE o.order_status = 'delivered'

GROUP BY
    YEAR(o.order_purchase_timestamp),
    MONTH(o.order_purchase_timestamp)

ORDER BY
    order_year,
    order_month;


-- ============================================================
-- 21. PRODUCT CATEGORY PERFORMANCE
-- ============================================================

SELECT
    pr.product_category_name AS category,
    COUNT(DISTINCT oi.order_id) AS total_orders,
    COUNT(*) AS units_sold,
    ROUND(SUM(oi.price), 2) AS product_revenue,
    ROUND(AVG(oi.price), 2) AS average_product_price
FROM order_items_clean oi
JOIN products_clean pr
    ON oi.product_id = pr.product_id
JOIN orders_clean o
    ON oi.order_id = o.order_id
WHERE o.order_status = 'delivered'
GROUP BY
    pr.product_category_name
ORDER BY
    product_revenue DESC;


-- ============================================================
-- 22. SELLER PERFORMANCE
-- ============================================================

SELECT
    oi.seller_id,
    COUNT(DISTINCT oi.order_id) AS total_orders,
    COUNT(*) AS units_sold,
    ROUND(SUM(oi.price), 2) AS seller_revenue,
    ROUND(AVG(oi.price), 2) AS average_item_price
FROM order_items_clean oi
JOIN orders_clean o
    ON oi.order_id = o.order_id
WHERE o.order_status = 'delivered'
GROUP BY
    oi.seller_id
ORDER BY
    seller_revenue DESC;


-- ============================================================
-- 23. TOP SELLERS WITH MEANINGFUL ORDER VOLUME
-- ============================================================

SELECT
    oi.seller_id,
    COUNT(DISTINCT oi.order_id) AS total_orders,
    COUNT(*) AS units_sold,
    ROUND(SUM(oi.price), 2) AS seller_revenue,
    ROUND(AVG(oi.price), 2) AS average_item_price
FROM order_items_clean oi
JOIN orders_clean o
    ON oi.order_id = o.order_id
WHERE o.order_status = 'delivered'
GROUP BY
    oi.seller_id
HAVING COUNT(DISTINCT oi.order_id) >= 10
ORDER BY
    seller_revenue DESC
LIMIT 10;


-- ============================================================
-- 24. DELIVERY PERFORMANCE BY CUSTOMER STATE
-- ============================================================

SELECT
    c.customer_state,
    COUNT(DISTINCT o.order_id) AS total_orders,

    ROUND(
        AVG(o.delivery_days),
        2
    ) AS avg_delivery_days,

    ROUND(
        AVG(o.delivery_delay_days),
        2
    ) AS avg_delivery_delay_days,

    ROUND(
        100 * AVG(o.is_delayed),
        2
    ) AS delayed_percentage

FROM orders_clean o

JOIN customers_clean c
    ON o.customer_id = c.customer_id

WHERE o.order_status = 'delivered'

GROUP BY
    c.customer_state

ORDER BY
    delayed_percentage DESC;


-- ============================================================
-- 25. DELIVERY PERFORMANCE BY PRODUCT CATEGORY
-- ============================================================

SELECT
    pr.product_category_name AS category,

    COUNT(DISTINCT o.order_id) AS total_orders,

    ROUND(
        AVG(o.delivery_days),
        2
    ) AS avg_delivery_days,

    ROUND(
        AVG(o.delivery_delay_days),
        2
    ) AS avg_delivery_delay_days,

    ROUND(
        100 * AVG(o.is_delayed),
        2
    ) AS delayed_percentage

FROM orders_clean o

JOIN order_items_clean oi
    ON o.order_id = oi.order_id

JOIN products_clean pr
    ON oi.product_id = pr.product_id

WHERE o.order_status = 'delivered'

GROUP BY
    pr.product_category_name

HAVING COUNT(DISTINCT o.order_id) >= 100

ORDER BY
    delayed_percentage DESC;