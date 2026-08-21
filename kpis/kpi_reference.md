# KPI Reference

## KPI: Monthly Active Users (MAU)
- Definition: Distinct customers with at least one transaction in the last 30 days.
- Formula: COUNT(DISTINCT customer_id) WHERE transaction_date >= reference_date - 30 days.
- Data Source: `data/raw/kpi_transactions_sample.csv` (`customer_id`, `transaction_date`).
- Target Range: 9 to 12 users.
- Owner: Product Manager.
- Update Frequency: Daily.
- Notes: Leading indicator of product engagement and retention risk.

## KPI: Revenue Per Customer
- Definition: Average revenue generated per unique customer in the observed dataset.
- Formula: SUM(amount) / COUNT(DISTINCT customer_id).
- Data Source: `data/raw/kpi_transactions_sample.csv` (`amount`, `customer_id`).
- Target Range: $120 to $170.
- Owner: Finance Analyst.
- Update Frequency: Daily.
- Notes: Helps compare value generation across acquisition channels.

## KPI: Churn Rate (30-day cohort method)
- Definition: Share of customers active in the prior 30-day window but inactive in the current 30-day window.
- Formula: (Active_P1 - Active_P2 overlap) / Active_P1.
- Data Source: `data/raw/kpi_transactions_sample.csv` (`customer_id`, `transaction_date`).
- Target Range: 0% to 35%.
- Owner: Retention Manager.
- Update Frequency: Weekly.
- Notes: High churn often signals onboarding and support quality issues.

## KPI: Payment Success Rate
- Definition: Proportion of transactions marked as successful.
- Formula: COUNT(payment_status = "success") / COUNT(all transactions).
- Data Source: `data/raw/kpi_transactions_sample.csv` (`payment_status`).
- Target Range: 90% to 100%.
- Owner: Payments Operations.
- Update Frequency: Daily.
- Notes: Drops can indicate processor outages or fraud rule over-blocking.

## KPI: Customer Acquisition Cost (CAC)
- Definition: Average acquisition cost per unique customer.
- Formula: SUM(acquisition_cost by unique customer) / COUNT(DISTINCT customer_id).
- Data Source: `data/raw/kpi_transactions_sample.csv` (`customer_id`, `acquisition_cost`).
- Target Range: $30 to $55.
- Owner: Growth Marketing Lead.
- Update Frequency: Monthly.
- Notes: Should be monitored together with revenue per customer and churn.

## KPI: Total Revenue
- Definition: Total transaction value in the observed period.
- Formula: SUM(amount).
- Data Source: `data/raw/kpi_transactions_sample.csv` (`amount`).
- Target Range: $1,500 to $2,500.
- Owner: Revenue Operations.
- Update Frequency: Daily.
- Notes: Core top-level KPI used for decomposition by segment and product.