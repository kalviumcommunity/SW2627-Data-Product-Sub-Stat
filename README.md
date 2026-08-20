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

## 5. Module 4 — Missing Value Detection & Imputation

### Objective
Implement automated missing-value detection and defensible, multi-strategy imputation routines (dropping invalid identifiers, time-series forward fill, median imputation, mode imputation) accompanied by rigorous before/after audit tracking.

### What Was Implemented
- **Missing Value Profiling (`detect_missing_values`)**: Measures total missing cells, overall missingness percentage, and per-column null statistics.
- **Defensible Treatment Strategy Selection (`handle_missing_values`)**:
  - **Critical Identifiers (Row Dropping)**: Removes records missing primary keys (`viewer_id`) to prevent artificial identity collisions.
  - **Time-Series Sequential Imputation (Forward Fill)**: Propagates prior observations across sorted date fields (`viewing_date`) assuming state continuity.
  - **Numerical Imputation (Median)**: Imputes continuous/skewed features (`monthly_fee`, `watch_duration_minutes`, `completion_rate`) using the column median to resist outlier distortion.
  - **Categorical Imputation (Mode)**: Imputes categorical variables (`country`, `subscription_plan`, `user_name`) with the most frequent valid category.
- **Before vs. After Audit Reporting (`generate_imputation_report`)**: Tracks row counts, missingness reductions, completeness percentages, and logs the explicit rationale for each feature treatment.
- **Automated Test Suite (`scripts/test_missing_value_handling.py`)**: 6 unit tests validating detection, ID dropping, median/mode/ffill logic, and report generation.

### Files Created & Modified
- `scripts/missing_value_handling.py`: Core imputation engine and workflow runner.
- `scripts/test_missing_value_handling.py`: Comprehensive test suite.
- `data/raw/raw_with_missing.csv`: Sample raw dataset with representative null patterns.
- `README.md`: Module documentation.

### How to Run & Use

```bash
# Run the missing value detection and imputation workflow:
python scripts/missing_value_handling.py

# Run the automated unit tests:
python -m unittest scripts/test_missing_value_handling.py
```

### Validation & Testing Performed
- **Automated Tests:** All 6 unit tests passed (`OK`), validating missingness detection, row dropping on null IDs, median replacement accuracy, mode replacement accuracy, time-series continuity, and JSON audit logging.
- **Pipeline Execution:** Successfully cleaned `data/raw/raw_with_missing.csv` (10 rows, 11.1% missing cells) into `data/processed/cleaned_imputed.csv` (8 rows, 100.0% completeness), producing `output/missing_value_report.json`.

