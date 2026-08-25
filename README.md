# Viewer Engagement & Retention Analytics Platform

## SW2627 - Data Product - Subscription Statistics

A data analytics platform that identifies viewer engagement patterns associated with subscriber retention and presents actionable insights to support data-driven content acquisition decisions.

---

## 1. Project Overview

Subscription-based streaming platforms collect large amounts of viewer engagement data, including:

- Watch duration
- Pause frequency
- Episode completion
- Episodes watched
- Viewing frequency
- Subscription activity

However, content acquisition teams often lack a unified analytical system that connects these engagement behaviors with subscriber retention.

This project aims to bridge that gap by processing viewer activity data, engineering meaningful engagement metrics, analyzing their relationship with retention, and presenting the findings through an interactive dashboard.

### Core Question

> **Which viewer engagement patterns are associated with subscriber retention, and how can these insights help content acquisition teams make better decisions?**

---

## 2. Problem Statement

A subscription-based streaming platform captures watch duration, pause frequency, and episode completion data, but acquisition teams still greenlight content without understanding which viewer engagement patterns correlate with retention.

The platform may know how many people watched a piece of content, but raw view counts alone do not explain whether the content contributes to sustained subscriber engagement.

The project therefore focuses on connecting:

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

## 7. SQL Module 5 — SQL-Based Insight Validation

### Objective
Build a dual-engine insight validation workflow that calculates essential platform business metrics independently in SQL (via SQLite/SQLAlchemy) and in Python (via Pandas), evaluates numerical alignment across configurable absolute and relative tolerance thresholds, flags discrepancies, investigates root causes (NULL handling, data types, rounding, filtering divergence), and exports structured audit reports.

### What Was Implemented
- **Dual-Engine Metric Execution Framework (`scripts/sql_python_validation.py`)**:
  - `compute_sql_metrics()`: Executes pure SQL aggregate queries against SQLite tables (`subscription_events`, `viewers`, `viewer_activity`).
  - `compute_python_metrics()`: Calculates matching metrics using native Pandas transformations and aggregations directly on raw datasets.
- **Configurable Precision & Tolerance Engine (`SQLPythonValidator`)**:
  - Computes exact absolute differences ($|\text{SQL} - \text{Python}|$) and relative percentage differences ($|\text{SQL} - \text{Python}| / |\text{SQL}|$).
  - Configurable `abs_tolerance` (default: $10^{-4}$) and `rel_tolerance` (default: $10^{-4}$) boundary checks with binary `PASS`/`FAIL` outcome statuses.
- **Root-Cause Discrepancy Diagnostics (`diagnose_discrepancy`)**:
  - Automatically isolates causes of numerical divergences: unhandled `NaN`/`NULL` records, integer division truncation, floating point rounding beyond decimal precision, and row-level filtering mismatches.
- **Extensible Architecture (`register_metric`)**: Allows dynamic registration of future custom business metrics with dedicated SQL and Python calculation functions.
- **Audit Exporting (`output/metric_validation_report.json`)**: Exports structured machine-readable JSON summaries and clean terminal tables.
- **Automated Unit Test Suite (`scripts/test_sql_python_validation.py`)**: 5 unit tests validating dual-engine agreement, strict vs loose tolerance thresholding, intentional discrepancy detection, custom metric registration, and audit report generation.

### Files Created & Modified
- `queries/validation_metrics.sql`: Multi-metric SQL validation query definitions.
- `scripts/sql_python_validation.py`: Core cross-engine validator, discrepancy diagnostic engine, and report exporter.
- `scripts/test_sql_python_validation.py`: Unit test suite.
- `README.md`: Module documentation.

### Database & Tables Involved
- **Database**: SQLite (`data/sub_stat.db`) / in-memory SQLite engine
- **Tables**: `subscription_events`, `viewers`, `viewer_activity`

### Technologies & SQL Concepts Used
- **Technologies**: Python 3.10+, SQLAlchemy 2.0+, Pandas 2.0+, SQLite3, JSON, Dataclasses, unittest.
- **Concepts**: Dual-engine parity validation, numerical tolerance thresholding, root-cause discrepancy isolation, floating point arithmetic auditing, JSON audit trail serialization.

### How to Run & Test

```bash
# Run the SQL-Python metric validation workflow:
python scripts/sql_python_validation.py

# Run the automated unit test suite:
python -m unittest scripts/test_sql_python_validation.py
```

### Validation & Test Results
- **Unit Tests:** 5/5 tests passing (`OK`) in ~0.16s.
- **Metric Verification Table:**

| Metric Name | SQL Value | Python Value | Absolute Diff | Status | Diagnostic Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `total_completed_revenue` | $174.89 | $174.89 | $0.000000$ | **PASS** | Exact match |
| `avg_completed_transaction_amount` | $15.8991 | $15.8991 | $0.000000$ | **PASS** | Exact match |
| `payment_success_rate_pct` | $84.6154\%$ | $84.6154\%$ | $0.000000$ | **PASS** | Exact match |
| `total_watch_duration_mins` | $600.0$ mins | $600.0$ mins | $0.000000$ | **PASS** | Exact match |
| `active_viewers_count` | $6.0$ users | $6.0$ users | $0.000000$ | **PASS** | Exact match |

- **Overall Audit Status:** **PASS** ($5/5$ metrics verified). Report exported to `output/metric_validation_report.json`.


