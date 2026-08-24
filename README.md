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

## 6. Module 5 — NumPy Vectorised Computation & Performance Benchmarking

### Objective
Identify iterative Python loop bottlenecks in numerical data processing, implement both baseline loop and high-performance NumPy vectorized equivalents for Min-Max normalization, Z-score standardization, and multi-variable non-linear metric calculations, integrate vectorized arrays into pandas DataFrames, benchmark execution runtimes across dataset scales (1,000 to 100,000 rows), and document architectural performance advantages.

### What Was Implemented
- **Min-Max Normalization (`min_max_normalize_loop` vs. `min_max_normalize_vectorized`)**: Scales features into $[0.0, 1.0]$. NumPy vectorized routine replaces iterative element-by-element loops with compiled array SIMD operations.
- **Z-Score Standardization (`z_score_standardize_loop` vs. `z_score_standardize_vectorized`)**: Centers data at $\mu = 0.0$ with $\sigma = 1.0$. Vectorized implementation leverages single-pass C statistics.
- **Multi-Variable Composite Non-Linear Score (`compute_composite_score_loop` vs. `compute_composite_score_vectorized`)**: Implements exponential decay penalties and logarithmic scaling using NumPy universal functions (`np.power`, `np.log1p`, `np.exp`).
- **DataFrame Integration (`integrate_vectorized_features`)**: Enriches tabular datasets directly with vectorized normalized series and composite engagement indices.
- **Empirical Benchmarking Engine (`benchmark_operation`, `run_numpy_vectorization_pipeline`)**: Executes multi-trial runtime measurements across multiple scales ($N = 1\text{k}, 10\text{k}, 100\text{k}$), computing speedup multipliers ($T_{\text{loop}} / T_{\text{vectorized}}$).
- **Architectural Rationale**:
  - *Memory Layout & Cache Locality*: NumPy utilizes contiguous C-order memory buffers, maximizing CPU L1/L2 cache hit rates and enabling hardware prefetching.
  - *SIMD Hardware Parallelism*: Universal functions map directly to CPU vector registers (AVX2/AVX-512), processing 4 to 8 floating-point values per clock cycle.
  - *Interpreter Overhead Elimination*: Bypasses Python's dynamic type inspection, object boxing/unboxing, and bytecode evaluation loop.
- **Automated Unit Test Suite (`scripts/test_numpy_vectorization.py`)**: 6 unit tests confirming exact numerical equivalence (`np.testing.assert_allclose`), statistical properties ($\mu=0, \sigma=1$), DataFrame integration, and benchmark performance.

### Files Created & Modified
- `scripts/numpy_vectorization.py`: Core baseline loops, vectorized implementations, DataFrame integration, and benchmark suite.
- `scripts/test_numpy_vectorization.py`: Unit test suite.
- `data/processed/vectorized_computations_data.csv`: Output dataset enriched with vectorized columns.
- `output/numpy_vectorization_benchmark.json`: Multi-scale benchmark results and architectural documentation.
- `README.md`: Module documentation.

### Technologies & Functions Used
- **Technologies**: Python 3.10+, NumPy, Pandas, Unittest, JSON, Logging.
- **Key Functions**: `np.min()`, `np.max()`, `np.mean()`, `np.std()`, `np.power()`, `np.log1p()`, `np.exp()`, `time.perf_counter()`, `np.testing.assert_allclose()`.

### How to Run & Test

```bash
# Run the NumPy Vectorization Pipeline and multi-scale benchmark:
python scripts/numpy_vectorization.py

# Run the automated unit tests:
python -m unittest scripts/test_numpy_vectorization.py
```

### Benchmark Results & Performance Summary

| Dataset Scale (Rows) | Operation | Baseline Loop Time | Vectorized Time | Speedup Factor |
| :--- | :--- | :--- | :--- | :--- |
| **1,000** | Min-Max Normalization | ~0.15 ms | ~0.04 ms | **3.7x** |
| **1,000** | Z-Score Standardization | ~0.26 ms | ~0.06 ms | **3.9x** |
| **1,000** | Composite Non-Linear | ~0.84 ms | ~0.13 ms | **6.6x** |
| **10,000** | Min-Max Normalization | ~1.65 ms | ~0.12 ms | **14.3x** |
| **10,000** | Z-Score Standardization | ~2.72 ms | ~0.17 ms | **16.3x** |
| **10,000** | Composite Non-Linear | ~8.45 ms | ~1.60 ms | **5.3x** |
| **100,000** | Min-Max Normalization | ~16.2 ms | ~1.41 ms | **11.5x** |
| **100,000** | Z-Score Standardization | ~27.3 ms | ~1.74 ms | **15.7x** |
| **100,000** | Composite Non-Linear | ~85.2 ms | ~12.1 ms | **7.0x** |

- **Unit Tests:** 6/6 tests passing (`OK`).


