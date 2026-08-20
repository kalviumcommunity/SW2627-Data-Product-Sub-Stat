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

## 5. Module 2 — Dataset Profiling & Quality Assessment

### Objective
Perform automated dataset profiling and evaluate core data quality dimensions (Completeness, Uniqueness, Distribution, Validity, and Consistency) to ensure data reliability before downstream analysis and modeling.

### What Was Implemented
- **Shape & Memory Profiling (`profile_shape_and_memory`)**: Measures total rows, columns, memory usage (in bytes, KB, MB), and column names.
- **Completeness Analysis (`profile_missing_values`)**: Detects missing cells, null counts, null percentages per column, and computes overall dataset completeness.
- **Uniqueness & Key Checks (`profile_duplicates`)**: Calculates exact duplicate rows and verifies primary key uniqueness.
- **Numerical Distribution Profiling (`profile_numerical_distributions`)**: Computes statistical summaries including mean, standard deviation, median, 25th/75th percentiles, IQR, skewness, and identifies potential outliers using the 1.5x IQR rule.
- **Categorical Profiling (`profile_categorical_distributions`)**: Profiles cardinality and value frequencies for object/categorical columns.
- **Quality Assessment Engine (`assess_data_quality`)**: Assesses completeness, uniqueness, validity, and domain constraints, returning an overall data quality score (0-100), status, issues, and warnings.
- **Automated Test Suite (`scripts/test_dataset_profiling.py`)**: 7 automated unit tests validating all profiling functions and JSON report exports.

### Files Created & Modified
- `scripts/dataset_profiling.py`: Core profiling functions and pipeline runner.
- `scripts/test_dataset_profiling.py`: Comprehensive unit and integration test suite.
- `README.md`: Module documentation.

### How to Run & Use

```bash
# Run the dataset profiling pipeline:
python scripts/dataset_profiling.py

# Run the automated unit tests:
python -m unittest scripts/test_dataset_profiling.py
```

### Validation & Testing Performed
- **Automated Tests:** All 7 unit tests passed (`OK`), verifying dimension extraction, null detection, duplicate detection, distribution metrics, outlier identification, and report export.
- **Pipeline Execution:** Successfully profiled `data/raw/segment_sample.csv`, producing a structured audit report at `output/profiling_report.json`.

