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

## 7. SQL Module 4 — SQL Joins & Multi-Table Analysis

### Objective
Implement, audit, and validate relational data joins (`INNER JOIN`, `LEFT JOIN`, and SQLite-compatible `FULL OUTER JOIN` emulation). Track pre-join versus post-join record counts, detect unmatched foreign keys bidirectionally (left-only and right-only), analyze relationship cardinality ($1:1$, $1:N$), distinguish legitimate row multiplication from duplicate defects, and execute 3-way multi-table relational analysis.

### What Was Implemented
- **Modular SQL Join Queries (`queries/`)**:
  - `join_inner_viewers_events.sql`: Relational inner join matching viewers with payment events, filtering out zero-event subscribers and orphan billing records.
  - `join_left_viewers_events.sql`: Relational left join preserving the complete subscriber population and surfacing zero-activity viewers via NULL event attributes.
  - `join_full_outer_emulation.sql`: Robust SQLite emulation of `FULL OUTER JOIN` using `LEFT JOIN` combined with unmatched right-side rows via `UNION ALL`, categorizing each row into `Matched`, `Master Viewer Only`, or `Orphan Event Only`.
  - `join_multi_table_engagement.sql`: 3-way relational join linking `viewers` $\rightarrow$ `viewer_activity` $\rightarrow$ `content_catalog` for multi-layered behavioral analysis.
- **Relational Integrity Audit Engine (`scripts/sql_joins_validation.py`)**:
  - `audit_relational_join()`: Audits pre-merge counts, distinct key sets, join cardinality, left unmatched keys, right unmatched keys, and post-merge row counts across all join types.
  - Lineage & Row Multiplication Analysis: Programmatically documents why $1:N$ relationships legitimately expand row counts ($N_{\text{left}} \rightarrow N_{\text{merged}}$).
- **Automated Unit Test Suite (`scripts/test_sql_joins_validation.py`)**: 6 unit tests verifying cardinality detection, unmatched key isolation, INNER/LEFT/FULL OUTER row count mathematics, and 3-way multi-table data lineage.

### Files Created & Modified
- `queries/join_inner_viewers_events.sql`: Inner join query.
- `queries/join_left_viewers_events.sql`: Left join query.
- `queries/join_full_outer_emulation.sql`: SQLite full outer join emulation query.
- `queries/join_multi_table_engagement.sql`: 3-way relational multi-table query.
- `scripts/sql_joins_validation.py`: Relational audit engine and workflow runner.
- `scripts/test_sql_joins_validation.py`: Unit test suite.
- `README.md`: Module documentation.

### Database & Tables Involved
- **Database**: SQLite (`data/sub_stat.db`) / in-memory SQLite engine
- **Tables**: `viewers`, `subscription_events`, `viewer_activity`, `content_catalog`

### Technologies & SQL Concepts Used
- **Technologies**: Python 3.10+, SQLAlchemy 2.0+, Pandas 2.0+, SQLite3, unittest.
- **Concepts**: `INNER JOIN`, `LEFT JOIN`, `FULL OUTER JOIN` (emulated via `UNION ALL` and `WHERE IS NULL`), $1:N$ relationship cardinality, row expansion accounting, unmatched key isolation (`NOT IN` subqueries), 3-way relational navigation.

### How to Run & Test

```bash
# Run the SQL joins and multi-table validation workflow:
python scripts/sql_joins_validation.py

# Run the automated unit test suite:
python -m unittest scripts/test_sql_joins_validation.py
```

### Validation & Test Results
- **Unit Tests:** 6/6 tests passing (`OK`) in ~0.16s.
- **Relational Audit Findings:**
  - **Left Table (`viewers`):** 11 rows (11 unique `viewer_id` keys).
  - **Right Table (`subscription_events`):** 13 rows (12 unique `viewer_id` keys).
  - **Cardinality:** $1:N$ (One-to-Many).
  - **Unmatched Left Keys (Registered Viewers with 0 billing events):** `['V199']` (1 viewer).
  - **Unmatched Right Keys (Orphan Events with no master record):** `['V998', 'V999']` (2 events).
  - **Join Counts:**
    - `INNER JOIN`: 11 rows (matched active subscriber events).
    - `LEFT JOIN`: 12 rows (11 matched + 1 unmatched `V199` with NULL event details).
    - `FULL OUTER JOIN`: 14 rows (12 left join + 2 orphan events).
  - **Row Multiplication Analysis:** Average multiplication factor of $1.0\times$ for master viewers, demonstrating valid $1:N$ relational fan-out rather than duplicate errors.


