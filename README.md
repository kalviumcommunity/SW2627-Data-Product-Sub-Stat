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

## 5. Module 3 — Data Dictionary & Business Context Mapping

### Objective
Establish a formal, comprehensive data dictionary mapping all dataset fields to their technical specifications, data types, business definitions, constraints, and business domain objectives for the streaming analytics platform.

### What Was Implemented
- **Business Domain Segmentation**:
  1. **User & Subscription Domain**: Account identifiers, demographics, subscription plans, pricing, and billing preferences (`viewer_id`, `user_name`, `country`, `signup_date`, `subscription_plan`, `monthly_fee`, `auto_renew`).
  2. **Viewing Consumption Domain**: Content metadata, timestamps, session duration, and asset runtimes (`content_id`, `content_title`, `genre`, `watch_date`, `watch_duration_minutes`, `total_content_duration_minutes`).
  3. **Engagement Dynamics Domain**: Granular engagement metrics and behavioral indicators (`completion_rate`, `pause_frequency`, `episodes_watched`, `viewing_frequency_per_week`, `binge_watching_flag`).
  4. **Retention & Churn Domain**: Churn outcome indicators, risk scoring, and customer lifetime value (`subscription_status`, `churn`, `retention_risk_tier`, `customer_lifetime_value`).
- **Comprehensive Documentation ([docs/data_dictionary.md](docs/data_dictionary.md))**: Full reference detailing data types, constraints, descriptions, and business purpose.
- **Data Dictionary Engine (`scripts/data_dictionary.py`)**: Provides schema lookup, domain filtering (`get_fields_by_domain`), DataFrame schema validation (`validate_dataframe_schema`), and JSON export (`export_data_dictionary_json`).
- **Automated Test Suite (`scripts/test_data_dictionary.py`)**: 4 unit tests validating dictionary completeness, domain partitioning, schema compliance, and JSON export.

### Files Created & Modified
- `docs/data_dictionary.md`: Complete domain reference guide and data dictionary tables.
- `scripts/data_dictionary.py`: Programmatic schema definitions and validation logic.
- `scripts/test_data_dictionary.py`: Automated test suite for data dictionary rules.
- `README.md`: Module documentation.

### How to Run & Use

```bash
# Inspect and export the data dictionary to JSON:
python scripts/data_dictionary.py

# Run the automated unit tests:
python -m unittest scripts/test_data_dictionary.py
```

### Validation & Testing Performed
- **Automated Tests:** All 4 unit tests passed (`OK`), verifying field definitions, domain partitioning, DataFrame schema matching, and JSON export.
- **Export Verification:** Successfully generated schema export at `output/data_dictionary.json`.

