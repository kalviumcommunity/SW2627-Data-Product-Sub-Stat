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

## 6. Module 2 — Data Consistency & Validation Rules

### Objective
Implement a multi-category rule validation framework supporting range assertions, mandatory field null checks, regex format validation, relational referential integrity against catalog primary keys, and business rules (e.g. `end_time >= start_time`), isolating non-conforming records and generating structured audit reports.

### What Was Implemented
- **Range Constraint Validator (`check_range`)**: Verifies that numeric attributes (e.g. `watch_duration_mins` between 0 and 600, `user_rating` between 1.0 and 5.0) fall within predefined boundaries.
- **Required & Null Assertions (`check_required_fields`)**: Identifies missing, NaN, or whitespace-only records in mandatory business keys (`viewer_id`, `content_id`, `start_time`).
- **Regex & Format Pattern Validation (`check_regex_format`)**: Evaluates string representations against domain regex specifications (e.g. `^V\d{3,}$` for viewer IDs and standard email syntax).
- **Referential Integrity Enforcement (`check_referential_integrity`)**: Validates foreign key relationships against parent catalogs (`content_catalog.csv`), flagging orphan records.
- **Domain Business Rules (`check_date_order`)**: Ensures logical session chronology (`end_time >= start_time`).
- **Validation Engine (`DataValidator`)**:
  - Executes modular registered rules and generates boolean evaluation matrices.
  - Slices datasets into clean passing records and failing records enriched with `_failed_rules` and `_failure_reasons`.
  - Generates comprehensive pass/fail statistics and per-rule breakdown metrics.
- **Automated Test Suite (`scripts/test_data_validation.py`)**: 7 unit tests testing each rule validator individually and validating end-to-end multi-rule pipeline execution.

### Files Created & Modified
- `scripts/data_validation.py`: Core data validation engine and rule pipeline.
- `scripts/test_data_validation.py`: Unit test suite.
- `data/raw/content_catalog.csv`: Master reference catalog for referential integrity.
- `data/raw/validation_sample.csv`: Sample intake dataset with valid and controlled violation records.
- `data/processed/clean_validated_records.csv`: Clean subset passing all validation rules.
- `data/processed/failed_validation_records.csv`: Quarantined records with failure reason metadata.
- `output/data_validation_report.json`: Structured validation audit report.
- `README.md`: Module documentation.

### Technologies & Functions Used
- **Technologies**: Python 3.10+, Pandas, Regular Expressions (`re`), Unittest, JSON, Logging.
- **Key Functions**: `re.compile()`, `pd.to_numeric()`, `pd.to_datetime()`, `.isin()`, `.notna()`, `.all(axis=1)`.

### How to Run & Test

```bash
# Run the Data Consistency & Validation Pipeline:
python scripts/data_validation.py

# Run the automated unit tests:
python -m unittest scripts/test_data_validation.py
```

### Example & Result Summary
- **Intake Evaluated:** 10 records across 6 active validation rules.
- **Clean Records:** 3 passed all rules (30.0% pass rate).
- **Quarantined Records:** 7 failed at least one rule with specific failure explanations attached.
- **Automated Tests:** 7/7 unit tests passing (`OK`).


