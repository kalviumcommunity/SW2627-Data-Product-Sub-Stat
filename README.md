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

## 5. Module 1 — CSV & JSON Data Ingestion

### Objective
Provide robust, reliable ingestion for structured CSV and nested JSON datasets into Pandas DataFrames, handling varying delimiters, character encodings, nested object flattening, and generating audit reports.

### What Was Implemented
- **Explicit CSV Ingestion (`ingest_csv`)**: Loads CSV files with explicit delimiter and encoding specifications, automatically cycling through fallback encodings (`utf-8`, `latin1`, `cp1252`, `iso-8859-1`) upon decode failure.
- **Nested JSON Ingestion (`ingest_json`)**: Ingests JSON datasets with support for flattening complex nested key-value pairs using `pandas.json_normalize`.
- **Ingestion Audit Reporting (`generate_ingestion_report`)**: Generates structured metadata reports containing source path, file dimensions, column names, data types, null counts, and sample records.
- **Automated Test Suite (`scripts/test_data_ingestion.py`)**: Validates standard/custom delimiters, Latin-1 encoding fallback, JSON flattening, and error scenarios.

### Files Created & Modified
- `scripts/data_ingestion.py`: Core ingestion functions and demo runner.
- `scripts/test_data_ingestion.py`: Unit and integration test suite.
- `data/raw/viewers_nested.json`: Sample nested dataset representing viewer activity, plans, and metrics.
- `README.md`: Module documentation.

### How to Run & Use

```bash
# Run the ingestion pipeline demonstration:
python scripts/data_ingestion.py

# Run the automated unit tests:
python -m unittest scripts/test_data_ingestion.py
```

### Validation & Testing Performed
- **Automated Tests:** All 7 unit tests passed (`OK`), verifying CSV parsing, delimiter handling, character encoding fallback from UTF-8 to Latin-1, nested JSON normalization, and error handling for missing/empty files.
- **Pipeline Execution:** Successfully ingested `data/raw/sample.csv` and `data/raw/viewers_nested.json`, outputting structured audit reports to `output/ingestion_report_csv.json` and `output/ingestion_report_json.json`.
