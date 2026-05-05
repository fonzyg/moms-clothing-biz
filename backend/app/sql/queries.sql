-- Product catalog query with visible SQL joins and aggregation.
SELECT
    p.id,
    p.slug,
    p.name,
    p.category,
    p.price_cents,
    MIN(v.stock_quantity) AS lowest_variant_stock,
    SUM(v.stock_quantity) AS total_stock,
    GROUP_CONCAT(DISTINCT v.size) AS available_sizes,
    GROUP_CONCAT(DISTINCT v.color) AS available_colors
FROM products p
JOIN variants v ON v.product_id = p.id
WHERE p.category = :category
GROUP BY p.id
ORDER BY p.is_featured DESC, p.name ASC;

-- Order detail query interviewers can ask you to explain.
SELECT
    o.id AS order_id,
    c.email,
    c.full_name,
    p.name AS product_name,
    v.size,
    v.color,
    oi.quantity,
    oi.unit_price_cents,
    oi.quantity * oi.unit_price_cents AS line_total_cents
FROM orders o
JOIN customers c ON c.id = o.customer_id
JOIN order_items oi ON oi.order_id = o.id
JOIN variants v ON v.id = oi.variant_id
JOIN products p ON p.id = v.product_id
WHERE o.id = :order_id;

-- Sales aggregation query that demonstrates GROUP BY and SUM.
SELECT
    p.category,
    COUNT(DISTINCT o.id) AS order_count,
    SUM(oi.quantity) AS units_sold,
    SUM(oi.quantity * oi.unit_price_cents) AS revenue_cents
FROM orders o
JOIN order_items oi ON oi.order_id = o.id
JOIN variants v ON v.id = oi.variant_id
JOIN products p ON p.id = v.product_id
WHERE o.status = 'placed'
GROUP BY p.category
ORDER BY revenue_cents DESC;
