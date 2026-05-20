-- ================================================================
-- CUSTOMER 360 DATA PLATFORM — SQL Analytics Layer
-- Platform: Google BigQuery (compatible with PostgreSQL / Snowflake)
-- Schema: customer360.
-- ================================================================


-- ────────────────────────────────────────────────
-- 1. BUILD UNIFIED CUSTOMER 360 VIEW
-- ────────────────────────────────────────────────

CREATE OR REPLACE VIEW customer360.vw_customer_360 AS
WITH txn_summary AS (
    SELECT
        customer_id,
        COUNT(txn_id)                                            AS total_orders,
        SUM(CASE WHEN is_returned = 0 THEN amount ELSE 0 END)   AS total_spend,
        AVG(CASE WHEN is_returned = 0 THEN amount ELSE 0 END)   AS avg_order_value,
        AVG(is_returned)                                         AS return_rate,
        COUNT(DISTINCT category)                                 AS unique_categories,
        MAX(txn_date)                                            AS last_purchase_date,
        MIN(txn_date)                                            AS first_purchase_date,
        APPROX_TOP_COUNT(channel, 1)[OFFSET(0)].value           AS preferred_channel,
        APPROX_TOP_COUNT(category, 1)[OFFSET(0)].value          AS top_category,
        DATE_DIFF(CURRENT_DATE(), MAX(DATE(txn_date)), DAY)      AS days_since_last_purchase
    FROM customer360.transactions
    WHERE amount IS NOT NULL
    GROUP BY customer_id
),

engagement_summary AS (
    SELECT
        customer_id,
        COUNT(event_id)                                          AS total_sessions,
        AVG(session_minutes)                                     AS avg_session_mins,
        COUNTIF(event_type = 'add_to_cart')                     AS cart_events,
        COUNTIF(event_type = 'checkout')                        AS checkout_events,
        SAFE_DIVIDE(COUNTIF(event_type = 'checkout'),
                    NULLIF(COUNTIF(event_type = 'add_to_cart'), 0)) AS cart_to_checkout_rate,
        APPROX_TOP_COUNT(device, 1)[OFFSET(0)].value            AS preferred_device
    FROM customer360.web_events
    GROUP BY customer_id
),

support_summary AS (
    SELECT
        customer_id,
        COUNT(ticket_id)                                         AS total_tickets,
        COUNTIF(priority = 'High')                              AS high_priority_tickets,
        ROUND(AVG(csat_score), 2)                               AS avg_csat_score,
        ROUND(AVG(resolution_days), 1)                          AS avg_resolution_days
    FROM customer360.support_tickets
    GROUP BY customer_id
)

SELECT
    c.customer_id,
    c.full_name,
    c.email,
    c.city,
    c.segment,
    c.age,
    DATE_DIFF(CURRENT_DATE(), DATE(c.signup_date), DAY) AS days_since_signup,

    -- Transaction metrics
    COALESCE(t.total_orders, 0)               AS total_orders,
    COALESCE(t.total_spend, 0)                AS total_spend,
    COALESCE(t.avg_order_value, 0)            AS avg_order_value,
    COALESCE(t.return_rate, 0)                AS return_rate,
    COALESCE(t.unique_categories, 0)          AS unique_categories,
    t.last_purchase_date,
    t.days_since_last_purchase,
    t.preferred_channel,
    t.top_category,

    -- Engagement metrics
    COALESCE(e.total_sessions, 0)             AS total_sessions,
    COALESCE(e.avg_session_mins, 0)           AS avg_session_mins,
    COALESCE(e.cart_to_checkout_rate, 0)      AS cart_to_checkout_rate,
    e.preferred_device,

    -- Support metrics
    COALESCE(s.total_tickets, 0)              AS total_tickets,
    COALESCE(s.high_priority_tickets, 0)      AS high_priority_tickets,
    COALESCE(s.avg_csat_score, NULL)          AS avg_csat_score,
    COALESCE(s.avg_resolution_days, NULL)     AS avg_resolution_days

FROM customer360.crm_customers c
LEFT JOIN txn_summary      t  ON c.customer_id = t.customer_id
LEFT JOIN engagement_summary e ON c.customer_id = e.customer_id
LEFT JOIN support_summary   s  ON c.customer_id = s.customer_id;


-- ────────────────────────────────────────────────
-- 2. RFM SCORING TABLE
-- ────────────────────────────────────────────────

CREATE OR REPLACE TABLE customer360.rfm_scores AS
WITH rfm_raw AS (
    SELECT
        customer_id,
        days_since_last_purchase  AS recency,
        total_orders              AS frequency,
        total_spend               AS monetary
    FROM customer360.vw_customer_360
    WHERE total_orders > 0
),

rfm_percentiles AS (
    SELECT
        customer_id,
        recency, frequency, monetary,
        NTILE(5) OVER (ORDER BY recency DESC)    AS R_score,  -- lower recency = higher score
        NTILE(5) OVER (ORDER BY frequency ASC)  AS F_score,
        NTILE(5) OVER (ORDER BY monetary ASC)   AS M_score
    FROM rfm_raw
),

rfm_combined AS (
    SELECT
        *,
        R_score + F_score + M_score AS rfm_total
    FROM rfm_percentiles
)

SELECT
    customer_id,
    recency, frequency, monetary,
    R_score, F_score, M_score,
    rfm_total,
    CASE
        WHEN rfm_total >= 13 THEN 'Champions'
        WHEN rfm_total >= 10 THEN 'Loyal Customers'
        WHEN rfm_total >= 7  THEN 'Potential Loyalists'
        WHEN rfm_total >= 5  THEN 'At Risk'
        ELSE                      'Lost / Inactive'
    END AS rfm_segment
FROM rfm_combined;


-- ────────────────────────────────────────────────
-- 3. CHURN RISK SCORING
-- ────────────────────────────────────────────────

CREATE OR REPLACE TABLE customer360.churn_risk AS
SELECT
    customer_id,
    days_since_last_purchase,
    total_tickets,
    avg_csat_score,
    return_rate,
    total_sessions,

    -- Composite churn risk score
    (
        CASE WHEN days_since_last_purchase > 180 THEN 3
             WHEN days_since_last_purchase > 90  THEN 1 ELSE 0 END
      + CASE WHEN total_tickets > 3              THEN 2 ELSE 0 END
      + CASE WHEN avg_csat_score < 3
              AND avg_csat_score IS NOT NULL      THEN 2 ELSE 0 END
      + CASE WHEN return_rate > 0.30             THEN 1 ELSE 0 END
      + CASE WHEN total_sessions < 5             THEN 1 ELSE 0 END
    ) AS churn_score,

    CASE
        WHEN (
            CASE WHEN days_since_last_purchase > 180 THEN 3
                 WHEN days_since_last_purchase > 90  THEN 1 ELSE 0 END
          + CASE WHEN total_tickets > 3              THEN 2 ELSE 0 END
          + CASE WHEN avg_csat_score < 3
                  AND avg_csat_score IS NOT NULL      THEN 2 ELSE 0 END
          + CASE WHEN return_rate > 0.30             THEN 1 ELSE 0 END
          + CASE WHEN total_sessions < 5             THEN 1 ELSE 0 END
        ) >= 5 THEN 'High'
        WHEN (
            CASE WHEN days_since_last_purchase > 180 THEN 3
                 WHEN days_since_last_purchase > 90  THEN 1 ELSE 0 END
          + CASE WHEN total_tickets > 3              THEN 2 ELSE 0 END
          + CASE WHEN avg_csat_score < 3
                  AND avg_csat_score IS NOT NULL      THEN 2 ELSE 0 END
          + CASE WHEN return_rate > 0.30             THEN 1 ELSE 0 END
          + CASE WHEN total_sessions < 5             THEN 1 ELSE 0 END
        ) >= 3 THEN 'Medium'
        ELSE 'Low'
    END AS churn_risk_level

FROM customer360.vw_customer_360;


-- ────────────────────────────────────────────────
-- 4. KPI / EXECUTIVE REPORT QUERIES
-- ────────────────────────────────────────────────

-- 4A: Segment Revenue Summary
SELECT
    r.rfm_segment,
    COUNT(DISTINCT c.customer_id)                               AS customers,
    ROUND(SUM(c.total_spend), 0)                               AS total_revenue,
    ROUND(AVG(c.total_spend), 0)                               AS avg_clv,
    ROUND(AVG(c.avg_order_value), 0)                           AS avg_aov,
    ROUND(AVG(c.total_orders), 1)                              AS avg_orders,
    ROUND(AVG(c.days_since_last_purchase), 0)                  AS avg_recency_days,
    ROUND(SUM(c.total_spend) / SUM(SUM(c.total_spend))
          OVER () * 100, 1)                                     AS revenue_share_pct
FROM customer360.vw_customer_360 c
JOIN customer360.rfm_scores r USING (customer_id)
GROUP BY r.rfm_segment
ORDER BY total_revenue DESC;


-- 4B: Monthly Revenue Trend with MoM Growth
WITH monthly AS (
    SELECT
        DATE_TRUNC(txn_date, MONTH)  AS txn_month,
        SUM(amount)                   AS revenue,
        COUNT(DISTINCT customer_id)   AS active_customers,
        COUNT(txn_id)                 AS transactions
    FROM customer360.transactions
    WHERE is_returned = 0
    GROUP BY txn_month
)
SELECT
    txn_month,
    ROUND(revenue, 0)                AS revenue,
    active_customers,
    transactions,
    ROUND(revenue / LAG(revenue) OVER (ORDER BY txn_month) - 1, 4) AS mom_growth,
    ROUND(AVG(revenue) OVER (ORDER BY txn_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 0) AS rolling_3m_avg
FROM monthly
ORDER BY txn_month;


-- 4C: Channel Performance
SELECT
    preferred_channel,
    COUNT(DISTINCT customer_id)       AS customers,
    ROUND(SUM(total_spend), 0)        AS total_revenue,
    ROUND(AVG(avg_order_value), 0)    AS avg_aov,
    ROUND(AVG(return_rate) * 100, 1)  AS return_rate_pct
FROM customer360.vw_customer_360
WHERE preferred_channel IS NOT NULL
GROUP BY preferred_channel
ORDER BY total_revenue DESC;


-- 4D: City-wise Customer Health Index
SELECT
    city,
    COUNT(DISTINCT c.customer_id)             AS total_customers,
    ROUND(AVG(c.total_spend), 0)              AS avg_clv,
    ROUND(AVG(c.avg_csat_score), 2)           AS avg_csat,
    ROUND(AVG(c.total_tickets), 2)            AS avg_tickets,
    COUNTIF(cr.churn_risk_level = 'High')     AS high_churn_customers,
    ROUND(COUNTIF(cr.churn_risk_level='High') / COUNT(*) * 100, 1) AS churn_risk_pct
FROM customer360.vw_customer_360 c
LEFT JOIN customer360.churn_risk cr USING (customer_id)
GROUP BY city
ORDER BY avg_clv DESC;


-- 4E: Cross-sell Opportunity — Customers buying in <3 Categories
SELECT
    c.customer_id,
    c.full_name,
    c.city,
    r.rfm_segment,
    c.unique_categories,
    c.total_spend,
    c.top_category,
    'Cross-sell Opportunity' AS action_tag
FROM customer360.vw_customer_360 c
JOIN customer360.rfm_scores r USING (customer_id)
WHERE c.unique_categories < 3
  AND r.rfm_segment IN ('Champions','Loyal Customers')
  AND c.total_orders >= 5
ORDER BY c.total_spend DESC
LIMIT 500;


-- 4F: At-Risk Win-Back List — High-Value Churners
SELECT
    c.customer_id,
    c.full_name,
    c.email,
    c.city,
    c.total_spend,
    c.days_since_last_purchase,
    c.preferred_channel,
    cr.churn_risk_level,
    'Win-Back Campaign'   AS recommended_action
FROM customer360.vw_customer_360 c
JOIN customer360.churn_risk cr USING (customer_id)
WHERE cr.churn_risk_level IN ('High','Medium')
  AND c.total_spend > 50000
ORDER BY c.total_spend DESC;


-- ────────────────────────────────────────────────
-- 5. DATA QUALITY CHECKS
-- ────────────────────────────────────────────────

SELECT
    'crm_customers'                          AS table_name,
    COUNT(*)                                 AS total_rows,
    COUNTIF(customer_id IS NULL)             AS null_customer_ids,
    COUNTIF(email IS NULL)                   AS null_emails,
    COUNTIF(segment IS NULL)                 AS null_segments,
    COUNT(DISTINCT customer_id)              AS unique_customers
FROM customer360.crm_customers

UNION ALL

SELECT
    'transactions',
    COUNT(*),
    COUNTIF(customer_id IS NULL),
    COUNTIF(amount IS NULL),
    COUNTIF(txn_date IS NULL),
    COUNT(DISTINCT txn_id)
FROM customer360.transactions

UNION ALL

SELECT
    'web_events',
    COUNT(*),
    COUNTIF(customer_id IS NULL),
    COUNTIF(event_type IS NULL),
    COUNTIF(event_date IS NULL),
    COUNT(DISTINCT event_id)
FROM customer360.web_events;