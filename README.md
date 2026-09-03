# Subscription Statistics Analytics Platform

Interactive Streamlit dashboard and reproducible Python analysis workflows for
understanding subscription revenue, customer segments, churn, retention, and
transaction performance. The project includes data intake validation, an
end-to-end CSV pipeline, KPI calculations, segment analysis, time-series
analysis, and generated reports in `output/`.

## Dataset

The repository contains small CSV fixtures under `data/raw/` so the project can
be run without external credentials or data downloads:

| File | Purpose | Main columns |
| --- | --- | --- |
| `sample.csv` | Intake-validation example | `customer_id`, `customer_name`, `transaction_amount`, `transaction_date` |
| `test.csv` | End-to-end pipeline example | `customer_id`, `order_id`, `amount`, `date`, `segment` |
| `kpi_transactions_sample.csv` | KPI calculations | `customer_id`, `transaction_date`, `amount`, `customer_type`, `product`, `payment_status`, `acquisition_cost` |
| `segment_sample.csv` | Segment analysis | `customer_id`, `customer_type`, `product`, `revenue`, `support_tickets`, `churn` |
| `segment_profile_sample.csv` | Retention strategy analysis | `customer_id`, `customer_type`, `lifetime_value`, `churn`, `support_tickets`, `retention_days` |
| `daily_revenue_sample.csv` | Trend analysis and dashboard trends | `date`, `revenue`, `orders` |

The scheduled pipeline expects a CSV with `customer_id`, `order_id`, `amount`,
`date`, and `segment`. Replace `data/raw/test.csv` with the production input
when connecting an external ingestion source. The sample data is static; the
GitHub Actions workflow is scheduled weekly.

## Getting Started

From a fresh checkout, run these four commands:

```bash
git clone <repository-url>
cd SW2627-Data-Product-Sub-Stat
python3 -m venv venv && venv/bin/pip install -r requirements.txt
venv/bin/streamlit run app.py
```

Open the local URL printed by Streamlit (normally
`http://localhost:8501`). On Windows, use `venv\Scripts\python -m pip install
-r requirements.txt` and `venv\Scripts\streamlit run app.py`.

## Full Usage Guide

### Run the dashboard

```bash
venv/bin/streamlit run app.py
```

Use the sidebar to switch between:

- **Overview**: lifetime value, customers, churn, retention, and segment health.
- **Trends**: daily revenue, 7-day/30-day rolling averages, and monthly totals.
- **Data Explorer**: filter customer records and download the filtered CSV.

### Run the end-to-end pipeline

```bash
venv/bin/python pipeline.py --input data/raw/test.csv --output output
```

The pipeline ingests the CSV, removes unusable rows, converts `amount` to
numeric, filters non-positive amounts, aggregates revenue and order counts by
`segment`, and writes:

- `output/cleaned.csv`
- `output/aggregated.csv`

Both paths are configurable:

```bash
venv/bin/python pipeline.py --input path/to/input.csv --output path/to/output
```

Alternatively, provide a JSON config:

```json
{"input": "data/raw/test.csv", "output": "output"}
```

```bash
venv/bin/python pipeline.py --config pipeline_config.json
```

### Run analysis scripts

Run these from the repository root:

```bash
venv/bin/python scripts/validate_intake.py
venv/bin/python scripts/time_series_analysis.py
venv/bin/python scripts/segment_analysis.py
venv/bin/python scripts/segment_strategy_analysis.py
venv/bin/python kpis/kpi_functions.py
```

Each script writes its reports or charts to `output/`.

### Validate a processed CSV

```bash
venv/bin/python validate_data.py data/processed/cleaned_data.csv
```

The validator checks required columns, numeric `amount`, minimum row count,
and fully-null columns. It exits with code `1` when a check fails.

## Pipeline Architecture

```text
CSV upload / scheduled input
        |
        v
Ingestion: read the source CSV and record row counts
        |
        v
Cleaning: remove missing customer/amount rows, cast amount to numeric,
          remove invalid and non-positive amounts
        |
        v
Aggregation: group by segment and calculate revenue and order count
        |
        v
Output: write cleaned.csv and aggregated.csv to the selected output directory
        |
        v
Analysis: calculate KPI, segment, correlation, and time-series reports
        |
        v
Dashboard: load prepared CSVs, calculate display metrics, and render charts
        |
        v
Alerts: compare KPI values with configured target ranges and label PASS/ALERT
        |
        v
Reports: save CSV, JSON, TXT, and PNG artifacts for review
```

The weekly GitHub Actions workflow in
`.github/workflows/pipeline.yml` runs the pipeline on Mondays at 06:00 UTC and
can also be started manually with **Run workflow**.

## Derived Features

The following table documents engineered columns created by the pipeline and
analysis code. Display-only formatted values are included where they are
written into output tables.

| Column | Type | Description | Example |
| --- | --- | --- | --- |
| `amount` | float | Input amount coerced to numeric during cleaning | `120.50` |
| `revenue` | float | Sum of cleaned amounts by segment or period | `370.50` |
| `orders` | integer | Count of orders by segment or day | `2` |
| `revenue_ma7` | float | Trailing seven-observation revenue mean | `108.43` |
| `revenue_ma30` | float | Trailing thirty-observation revenue mean | `112.76` |
| `revenue_sum` | float | Weekly/monthly revenue total | `3,245.00` |
| `orders_count` | integer | Number of non-null order observations in a period | `42` |
| `revenue_mean` | float | Mean revenue for a week/month | `115.89` |
| `mom_change_pct` | float | Percentage change from the previous month | `4.25` |
| `churn_rate` | float | Mean churn outcome within a customer segment | `0.20` |
| `total_revenue` | float | Sum of revenue within a segment | `12,500.00` |
| `customer_count` | integer | Number of customer records in a segment | `25` |
| `avg_support_tickets` | float | Mean support tickets per segment | `3.40` |
| `avg_ltv` | float | Mean lifetime value per segment | `42,500.00` |
| `avg_tickets` | float | Segment mean support-ticket count in strategy analysis | `3.40` |
| `avg_retention` | float | Mean retention days per segment | `245.00` |
| `count` | integer | Segment record count in strategy analysis | `25` |
| `ltv_rank` | float | Dense rank of segments by average lifetime value | `1.0` |
| `churn_rank` | float | Dense rank of segments by churn rate | `2.0` |
| `segment_share_pct` | float | Segment records as a percentage of all records | `33.33` |
| `avg_ltv_display` | string | Currency-formatted average LTV for reports | `"$42,500"` |
| `churn_rate_display` | string | Percentage-formatted churn rate for reports | `"20.0%"` |
| `avg_tickets_display` | string | Formatted average support tickets | `"3.40"` |
| `avg_retention_display` | string | Formatted retention duration | `"245 days"` |
| `segment_share_display` | string | Formatted segment share | `"33.3%"` |
| `revenue_contribution` | float | Segment revenue as a percentage of total segment revenue | `48.75` |

KPI functions also derive scalar/report values: monthly active users (distinct
customers in the latest 30-day window), revenue per customer, churn rate,
payment success rate, customer acquisition cost, total revenue, trend direction,
trend magnitude, and PASS/ALERT KPI status. These are saved in JSON or report
fields rather than as DataFrame columns.

## Known Limitations

- The included datasets are synthetic/sample fixtures, not live production data.
- The scheduled workflow runs weekly; the dashboard does not provide real-time
  ingestion.
- The pipeline accepts CSV input and expects exact column names.
- The pipeline filters missing or non-positive amounts but does not deduplicate
  orders or reconcile refunds.
- Date values are parsed only in the analyses that require dates; invalid dates
  are removed by those loaders.
- Churn is assumed to be a binary `0/1` value, and segment churn means the mean
  of that field.
- KPI target ranges are static JSON configuration and do not adjust for
  seasonality.
- Rolling metrics require enough observations; initial windows are blank.
- Email delivery and SMTP configuration are not currently implemented by the
  Streamlit app.
- GitHub Actions output commits require repository write permission and a
  workflow token with appropriate access.

## Project Checks

There are currently no committed pytest test cases in `tests/`. The practical
smoke checks are the pipeline command, the analysis script commands above, and
opening the Streamlit dashboard. CI data validation is defined in
`.github/workflows/validate.yml`.
