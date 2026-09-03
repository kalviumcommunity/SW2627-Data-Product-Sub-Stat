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
Viewer Activity
       ↓
Engagement Metrics
       ↓
Viewer Segmentation
       ↓
Retention Analysis
       ↓
Content Insights
       ↓
Acquisition Decisions
```

---

## 3. Project Structure

```text
SW2627-Data-Product-Sub-Stat/
├── data/
│   ├── raw/            # Original, immutable raw datasets
│   └── processed/      # Cleaned and transformed data ready for analysis
├── notebooks/          # Jupyter notebooks for exploratory data analysis (EDA)
├── scripts/            # Modular Python scripts for data processing and analysis
├── output/             # Generated charts, figures, metrics, and export files
├── requirements.txt    # Essential Python dependencies
├── .gitignore          # Files and directories ignored by Git
└── README.md           # Project documentation and setup guide
```

---

## 4. Development Environment Setup

Follow these steps to set up the local development environment on your machine.

### Prerequisites

- Python 3.10+ installed
- Git installed

### 1. Clone the Repository

```bash
git clone https://github.com/kalviumcommunity/SW2627-Data-Product-Sub-Stat.git
cd SW2627-Data-Product-Sub-Stat
```

### 2. Create a Virtual Environment

Create an isolated Python virtual environment named `venv`:

- **Windows (PowerShell / Command Prompt):**
  ```powershell
  python -m venv venv
  ```
- **macOS / Linux:**
  ```bash
  python3 -m venv venv
  ```

### 3. Activate the Virtual Environment

- **Windows (PowerShell):**
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
  *(If you encounter a PowerShell execution policy restriction, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first)*

- **Windows (Command Prompt):**
  ```cmd
  venv\Scripts\activate.bat
  ```

- **macOS / Linux:**
  ```bash
  source venv/bin/activate
  ```

Once activated, your terminal prompt will display `(venv)`.

### 4. Install Dependencies

Upgrade `pip` and install all required project packages:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Verify Setup

Verify that the core libraries import properly:

```bash
python -c "import pandas, numpy, matplotlib, seaborn, sklearn, streamlit; print('Environment setup successful!')"
```

To deactivate the virtual environment when you are finished:

```bash
deactivate
```

---

## 5. Module 5 — Data Type Enforcement & Standardisation

### Objective
Implement explicit type enforcement and standardisation routines across raw datasets (String → Datetime with strict formats, Currency/Text → Numeric, Binary/Flags → Boolean, String normalization) to prevent silent data conversion failures.

### What Was Implemented
- **Explicit Datetime Standardisation (`standardise_datetime`)**: Parses date strings into `datetime64[ns]` using strict, unambiguous strftime patterns (`%Y-%m-%d`), avoiding silent day/month swap anomalies.
- **Currency & Numeric Cleaning (`standardise_numeric`)**: Strips currency symbols (`$`, `€`, `£`, `₹`), thousands commas (`,`), and non-numeric suffixes (e.g. `hrs`, `USD`), safely casting values to `float` or `int`.
- **Boolean Standardisation (`standardise_boolean`)**: Maps integer binary flags (`0`, `1`) and text representations (`True`, `False`, `yes`, `no`) to nullable pandas `boolean` types.
- **String & Categorical Normalization (`standardise_string`)**: Trims whitespace and normalizes text casing (`title`, `lower`, `upper`).
- **Schema Enforcement Engine (`enforce_dataset_schema`)**: Executes schema validation rules across all columns and generates a conversion audit report with success rates and sample failure logs.
- **Automated Test Suite (`scripts/test_data_type_standardisation.py`)**: 5 unit tests validating explicit datetime parsing, currency cleanup, boolean mapping, casing normalization, and schema enforcement.

### Files Created & Modified
- `scripts/data_type_standardisation.py`: Core type standardisation engine and workflow runner.
- `scripts/test_data_type_standardisation.py`: Comprehensive unit test suite.
- `data/raw/raw_unstandardised.csv`: Sample raw dataset with unstandardized dates, currencies, and flags.
- `data/processed/standardised_data.csv`: Cleaned and standardized output dataset.
- `README.md`: Module documentation.

### How to Run & Use

```bash
# Run the duplicate detection and deduplication pipeline:
python scripts/deduplication.py

# Run the automated unit tests:
python -m unittest scripts/test_deduplication.py
```

### Validation & Testing Performed
- **Automated Tests:** All 5 unit tests passed (`OK`), verifying exact and near-duplicate detection, `most_complete` ranking accuracy, and audit log generation.
- **Pipeline Execution:** Successfully deduplicated `data/raw/raw_with_duplicates.csv` (10 rows -> 6 rows, 4 records removed / 40.0%), exporting `data/processed/deduplicated_data.csv`, `output/removed_duplicates_audit.csv`, and `output/deduplication_report.json`.

---

## 6. Module 1 — Date & Time Transformation Pipeline

### Objective
Parse timestamp and date strings into pandas datetime objects, extract structured calendar and cyclical features (day of week, numeric day of week, hour, ISO week number, month, quarter, year, weekend indicators), compute elapsed time metrics (days since event, tenure duration) using datetime arithmetic, and aggregate time-series observations via resampling.

### What Was Implemented
- **Datetime Parsing Engine (`parse_datetime_column`)**: Robust parsing of timestamp and calendar date strings into `datetime64[ns]` with configurable error handling (`coerce`, `raise`) and optional UTC standardisation.
- **Temporal Feature Extraction (`extract_temporal_features`)**: Generates rich calendar attributes from datetimes:
  - `day_of_week` (e.g. `'Wednesday'`, `'Saturday'`)
  - `day_of_week_num` (numeric index: `0` for Monday through `6` for Sunday)
  - `hour` (0 to 23 integer hour)
  - `is_weekend` (binary flag: `1` for Saturday/Sunday, `0` otherwise)
  - `iso_week` (ISO-8601 calendar week number `1`–`53`)
  - `month` (`1`–`12`) & `month_name` (`'January'`–`'December'`)
  - `quarter` (`1`–`4`) & `year`
- **Datetime Arithmetic & Recency (`calculate_days_since_event`, `calculate_duration_between_events`)**: Computes exact elapsed days between user events and an anchor reference date, as well as elapsed tenure durations between start and activity dates.
- **Time-Series Resampling & Aggregation (`resample_time_series`)**: Re-indexes DataFrame on datetime index to produce weekly (`'W'`), monthly (`'ME'`), and quarterly (`'QE'`) multi-metric aggregations (sum, mean, count).
- **Automated Unit Test Suite (`scripts/test_date_time_transformation.py`)**: 6 comprehensive unit tests covering parsing, feature extraction, arithmetic calculations, resampling, and end-to-end pipeline execution.

### Files Created & Modified
- `scripts/date_time_transformation.py`: Core date/time parsing, feature extraction, arithmetic, and resampling pipeline.
- `scripts/test_date_time_transformation.py`: Unit test suite.
- `data/raw/viewer_activity_sample.csv`: Sample activity dataset with timestamp strings and subscription dates.
- `data/processed/datetime_transformed_data.csv`: Transformed output dataset with 11 extracted temporal columns.
- `output/datetime_transformation_report.json`: Structured transformation and aggregation summary report.
- `README.md`: Module documentation and instructions.

### Technologies & Functions Used
- **Technologies**: Python 3.10+, Pandas, Unittest, JSON, Logging.
- **Key Functions**: `pd.to_datetime()`, `.dt.day_name()`, `.dt.dayofweek`, `.dt.hour`, `.dt.isocalendar().week`, `.dt.month`, `.dt.quarter`, `.dt.total_seconds()`, `.resample()`, `.agg()`.

### How to Run & Test

```bash
# Run the end-to-end Date & Time Transformation Pipeline:
python scripts/date_time_transformation.py

# Run the automated unit tests:
python -m unittest scripts/test_date_time_transformation.py
```

### Example & Result Summary
- **Input Records:** 16 viewer activity sessions with raw string timestamps.
- **Extracted Columns (11 new features):** `session_day_of_week`, `session_day_of_week_num`, `session_hour`, `session_is_weekend`, `session_iso_week`, `session_month`, `session_month_name`, `session_quarter`, `session_year`, `tenure_days_at_session`, `days_since_session`.
- **Aggregated Output:** Weekly and monthly summaries aggregating total watch duration and session frequencies.
- **Unit Tests:** 6/6 tests passing (`OK`).

---

## 7. SQL Module 1 — SQL Environment & Database Integration

### Objective
Set up a reproducible, modular, and self-contained database integration workflow using SQLite, SQLAlchemy, and Pandas. Automatically load raw and cleaned datasets into relational tables, introspect schema definitions using SQLAlchemy Inspector, execute parameterized SQL queries to Pandas DataFrames, and ensure database connection credentials remain strictly decoupled from source code.

### Implementation Summary
- **Database Engine Lifecycle (`create_db_engine`)**: Configurable SQLAlchemy engine instantiation supporting local SQLite file storage (`sqlite:///data/sub_stat.db`), in-memory testing instances (`sqlite:///:memory:`), and external relational databases via environment variables (`DATABASE_URL`).
- **Automated Data Ingestion & Table Initialization (`initialize_database`, `load_csv_to_table`)**: Populates relational tables (`viewers`, `subscription_events`, `viewer_activity`, `content_catalog`) from project CSV files using Pandas `to_sql()` with idempotency support.
- **Schema Introspection & Validation (`inspect_database_schema`, `verify_table_exists`)**: Utilizes `sqlalchemy.inspect` to introspect table names, column data types, nullability, primary key constraints, and dynamic row counts.
- **SQL-to-DataFrame Query Pipeline (`query_to_dataframe`)**: Securely executes standard and parameterized SQL statements via SQLAlchemy `text()` constructs into Pandas DataFrames.
- **Environment Decoupling**: `.env.example` template provided to keep credentials out of code.
- **Automated Test Suite (`scripts/test_database_integration.py`)**: 7 unit tests validating engine creation, table verification, schema inspection, DataFrame queries, parameterized security, and project dataset loading.

### Files Created & Modified
- `requirements.txt`: Added `sqlalchemy>=2.0.0` dependency.
- `.env.example`: Environment template for database connection strings.
- `scripts/database_integration.py`: Core database integration workflow, engine factory, table loader, schema inspector, and query runner.
- `scripts/test_database_integration.py`: Comprehensive unit test suite.
- `README.md`: Module documentation, usage instructions, and validation summary.

### Database & Tables Involved
- **Database**: SQLite (`data/sub_stat.db`)
- **Tables Initialized**:
  - `viewers` (11 rows, 5 columns: `viewer_id`, `signup_date`, `plan_tier`, `country`, `device_type`)
  - `subscription_events` (13 rows, 6 columns: `event_id`, `viewer_id`, `event_date`, `payment_amount`, `payment_status`, `auto_renew`)
  - `viewer_activity` (16 rows, 6 columns: `viewer_id`, `content_id`, `session_timestamp`, `subscription_date`, `watch_duration_mins`, `completion_status`)
  - `content_catalog` (5 rows, 4 columns: `content_id`, `title`, `total_duration_mins`, `genre`)

### Technologies & SQL Concepts Used
- **Technologies**: Python 3.10+, SQLAlchemy 2.0+, Pandas 2.0+, SQLite3, python-dotenv, unittest.
- **Concepts**: Relational schema design, SQL DDL/DML, parameterized query execution (`:param`), schema introspection (`sqlalchemy.inspect`), data serialization (`to_sql`, `read_sql_query`).

### Setup & Execution Instructions

```bash
# 1. Install dependencies (including SQLAlchemy):
pip install -r requirements.txt

# 2. Run the database integration and verification workflow:
python scripts/database_integration.py

# 3. Run the automated unit tests:
python -m unittest scripts/test_database_integration.py
```

### Expected Output & Test Results
- **Unit Tests:** 7/7 tests passing (`OK`) in ~0.28s.
- **Workflow Run Output:**
  - Initialized 4 relational tables.
  - Inspected schema and verified row counts (`viewers`: 11, `subscription_events`: 13, `viewer_activity`: 16, `content_catalog`: 5).
  - Executed aggregate query and top-paying parameterized query into Pandas DataFrames.

### Design Decisions & Assumptions
- **SQLite Selection**: SQLite was chosen as the default self-contained engine to enable 100% reproducible execution out of the box without external database server dependencies.
- **Security & Decoupling**: Connection parameters default to the local database but automatically respect `DATABASE_URL` from the environment if PostgreSQL or MySQL is configured.
- **Idempotency**: `to_sql(..., if_exists='replace')` allows the database initialization script to be re-run safely at any time.


