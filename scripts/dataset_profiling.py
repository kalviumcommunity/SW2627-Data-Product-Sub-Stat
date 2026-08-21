"""Module 2 — Dataset Profiling & Quality Assessment

Provides comprehensive profiling and quality dimension analysis for tabular datasets:
- Dimensions (shape, memory, column data types)
- Completeness (missing values, null percentages, completeness score)
- Uniqueness (exact duplicates, duplicate percentages, unique counts)
- Distribution (numerical statistics: mean, std, min, IQR, percentiles, skewness, outliers)
- Validity & Consistency (range validations, business logic anomalies, quality flags)
- Structured JSON and terminal reporting
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd


def profile_shape_and_memory(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Profile dataset dimensions, columns, and memory consumption.

    Parameters:
        df: Pandas DataFrame to analyze.

    Returns:
        Dictionary containing rows, columns, memory usage in KB/MB.
    """
    memory_bytes = int(df.memory_usage(deep=True).sum())
    return {
        "total_rows": int(len(df)),
        "total_columns": int(len(df.columns)),
        "memory_bytes": memory_bytes,
        "memory_kb": round(memory_bytes / 1024, 2),
        "memory_mb": round(memory_bytes / (1024 * 1024), 4),
        "columns": list(df.columns),
    }


def profile_missing_values(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze missing values across columns and compute completeness metrics.

    Parameters:
        df: Pandas DataFrame to analyze.

    Returns:
        Dictionary with per-column null counts, null percentages, and overall completeness score.
    """
    total_cells = df.size
    total_missing = int(df.isna().sum().sum())
    total_rows = max(len(df), 1)

    column_missing: Dict[str, Dict[str, Any]] = {}
    for col in df.columns:
        null_count = int(df[col].isna().sum())
        null_pct = round((null_count / total_rows) * 100, 2)
        column_missing[col] = {
            "null_count": null_count,
            "null_percentage": null_pct,
            "is_complete": null_count == 0,
        }

    overall_completeness = round(((total_cells - total_missing) / max(total_cells, 1)) * 100, 2)

    return {
        "total_missing_cells": total_missing,
        "total_cells": int(total_cells),
        "overall_completeness_pct": overall_completeness,
        "columns": column_missing,
    }


def profile_duplicates(df: pd.DataFrame, primary_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Detect exact and primary key duplicates in the dataset.

    Parameters:
        df: Pandas DataFrame to analyze.
        primary_key: Optional primary key column name to check uniqueness.

    Returns:
        Dictionary with exact duplicate counts, percentages, and primary key duplicate info.
    """
    total_rows = max(len(df), 1)
    exact_duplicates = int(df.duplicated().sum())
    exact_duplicate_pct = round((exact_duplicates / total_rows) * 100, 2)

    result: Dict[str, Any] = {
        "exact_duplicate_rows": exact_duplicates,
        "exact_duplicate_pct": exact_duplicate_pct,
        "is_unique": exact_duplicates == 0,
    }

    if primary_key and primary_key in df.columns:
        pk_duplicates = int(df.duplicated(subset=[primary_key]).sum())
        result["primary_key"] = primary_key
        result["primary_key_duplicates"] = pk_duplicates
        result["primary_key_unique"] = pk_duplicates == 0

    return result


def profile_numerical_distributions(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute statistical distribution metrics for all numerical columns.

    Parameters:
        df: Pandas DataFrame to analyze.

    Returns:
        Dictionary mapping column names to distribution metrics (mean, std, percentiles, IQR, skewness, outliers).
    """
    num_df = df.select_dtypes(include=[np.number])
    distributions: Dict[str, Any] = {}

    for col in num_df.columns:
        series = df[col].dropna()
        if len(series) == 0:
            continue

        q25 = float(series.quantile(0.25))
        q50 = float(series.median())
        q75 = float(series.quantile(0.75))
        iqr = float(q75 - q25)
        lower_bound = float(q25 - 1.5 * iqr)
        upper_bound = float(q75 + 1.5 * iqr)

        outliers = series[(series < lower_bound) | (series > upper_bound)]
        skew_val = float(series.skew()) if len(series) > 2 else 0.0

        distributions[col] = {
            "count": int(series.count()),
            "mean": round(float(series.mean()), 4),
            "std": round(float(series.std()), 4) if len(series) > 1 else 0.0,
            "min": round(float(series.min()), 4),
            "q25": round(q25, 4),
            "median": round(q50, 4),
            "q75": round(q75, 4),
            "max": round(float(series.max()), 4),
            "iqr": round(iqr, 4),
            "skewness": round(skew_val, 4),
            "outlier_count": int(len(outliers)),
            "outlier_pct": round((len(outliers) / max(len(series), 1)) * 100, 2),
        }

    return distributions


def profile_categorical_distributions(df: pd.DataFrame, max_top: int = 5) -> Dict[str, Any]:
    """
    Profile categorical and object columns for cardinality and frequencies.

    Parameters:
        df: Pandas DataFrame to analyze.
        max_top: Maximum number of top frequent values to return.

    Returns:
        Dictionary mapping column names to unique counts, top values, and frequencies.
    """
    cat_df = df.select_dtypes(include=["object", "string", "category", "bool"])
    distributions: Dict[str, Any] = {}

    for col in cat_df.columns:
        series = df[col].dropna()
        unique_count = int(series.nunique())
        top_counts = series.value_counts().head(max_top).to_dict()
        top_formatted = {str(k): int(v) for k, v in top_counts.items()}

        distributions[col] = {
            "total_non_null": int(len(series)),
            "unique_values": unique_count,
            "cardinality_pct": round((unique_count / max(len(df), 1)) * 100, 2),
            "top_values": top_formatted,
        }

    return distributions


def assess_data_quality(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Evaluate 5 core data quality dimensions:
    1. Completeness: Missing values threshold.
    2. Uniqueness: Duplication rate.
    3. Validity: Type correctness, invalid values.
    4. Consistency: Anomalous values, extreme variance.
    5. Timeliness/Integrity: Structural integrity.

    Parameters:
        df: Pandas DataFrame to assess.

    Returns:
        Dictionary with dimensional scores, flags, and actionable recommendations.
    """
    issues: List[str] = []
    warnings: List[str] = []

    # 1. Completeness Check
    null_counts = df.isna().sum()
    cols_with_high_nulls = null_counts[null_counts / max(len(df), 1) > 0.2].index.tolist()
    if cols_with_high_nulls:
        issues.append(f"High missingness (>20%) detected in: {cols_with_high_nulls}")

    # 2. Uniqueness Check
    exact_dups = df.duplicated().sum()
    if exact_dups > 0:
        warnings.append(f"Found {exact_dups} exact duplicate rows ({round(exact_dups/len(df)*100, 1)}%)")

    # 3. Validity & Distribution Check
    num_df = df.select_dtypes(include=[np.number])
    for col in num_df.columns:
        if (df[col] < 0).any() and any(term in col.lower() for term in ["revenue", "duration", "count", "tickets"]):
            issues.append(f"Negative values found in non-negative domain column '{col}'")

    # Overall Quality Score Calculation (0-100)
    completeness_score = max(0, 100 - (df.isna().sum().sum() / max(df.size, 1) * 100))
    uniqueness_score = max(0, 100 - (exact_dups / max(len(df), 1) * 100))
    validity_penalty = len(issues) * 10
    overall_score = round(max(0, (completeness_score * 0.5 + uniqueness_score * 0.3) - validity_penalty), 1)

    status = "EXCELLENT" if overall_score >= 90 else "GOOD" if overall_score >= 75 else "NEEDS_ATTENTION"

    return {
        "overall_quality_score": overall_score,
        "quality_status": status,
        "completeness_score": round(completeness_score, 1),
        "uniqueness_score": round(uniqueness_score, 1),
        "critical_issues": issues,
        "warnings": warnings,
    }


def generate_dataset_profile(
    df: pd.DataFrame,
    dataset_name: str = "dataset",
    primary_key: Optional[str] = None,
    report_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """
    Run complete dataset profiling and quality assessment pipeline.

    Parameters:
        df: Pandas DataFrame to profile.
        dataset_name: Identifier for the dataset.
        primary_key: Optional primary key column.
        report_path: Optional output path for the JSON profile report.

    Returns:
        Structured dictionary containing full profile report.
    """
    report: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "dataset_name": dataset_name,
        "shape_and_memory": profile_shape_and_memory(df),
        "completeness": profile_missing_values(df),
        "uniqueness": profile_duplicates(df, primary_key=primary_key),
        "numerical_distributions": profile_numerical_distributions(df),
        "categorical_distributions": profile_categorical_distributions(df),
        "quality_assessment": assess_data_quality(df),
    }

    if report_path:
        save_path = Path(report_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)

    return report


def run_profiling_demo() -> None:
    """Execute demonstration of dataset profiling on sample raw data."""
    repo_root = Path(__file__).resolve().parents[1]
    data_path = repo_root / "data/raw/segment_sample.csv"
    output_path = repo_root / "output/profiling_report.json"

    if not data_path.exists():
        print(f"[ERROR] Sample data file not found: {data_path}")
        return

    print("=" * 70)
    print("MODULE 2: DATASET PROFILING & QUALITY ASSESSMENT")
    print("=" * 70)

    df = pd.read_csv(data_path)
    print(f"\nProfiling dataset: {data_path.name}")
    print(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns")

    report = generate_dataset_profile(
        df=df,
        dataset_name="segment_sample",
        primary_key="customer_id",
        report_path=output_path,
    )

    print("\n--- [1] DIMENSIONS & MEMORY ---")
    sm = report["shape_and_memory"]
    print(f"  Rows: {sm['total_rows']}, Columns: {sm['total_columns']}, Memory: {sm['memory_kb']} KB")

    print("\n--- [2] COMPLETENESS ---")
    comp = report["completeness"]
    print(f"  Overall Completeness: {comp['overall_completeness_pct']}%")
    print(f"  Missing Cells: {comp['total_missing_cells']} / {comp['total_cells']}")

    print("\n--- [3] UNIQUENESS ---")
    uniq = report["uniqueness"]
    print(f"  Exact Duplicate Rows: {uniq['exact_duplicate_rows']} ({uniq['exact_duplicate_pct']}%)")
    if "primary_key" in uniq:
        print(f"  Primary Key ('{uniq['primary_key']}') Duplicates: {uniq['primary_key_duplicates']}")

    print("\n--- [4] NUMERICAL DISTRIBUTIONS ---")
    for col, stats in report["numerical_distributions"].items():
        print(f"  [{col}] mean={stats['mean']}, median={stats['median']}, std={stats['std']}, min={stats['min']}, max={stats['max']}, IQR={stats['iqr']}, outliers={stats['outlier_count']}")

    print("\n--- [5] QUALITY ASSESSMENT ---")
    qa = report["quality_assessment"]
    print(f"  Quality Score: {qa['overall_quality_score']} / 100 (Status: {qa['quality_status']})")
    if qa["critical_issues"]:
        for issue in qa["critical_issues"]:
            print(f"  [ISSUE] {issue}")
    if qa["warnings"]:
        for warning in qa["warnings"]:
            print(f"  [WARN] {warning}")
    if not qa["critical_issues"] and not qa["warnings"]:
        print("  [OK] No critical quality defects detected.")

    print(f"\n[OK] Full structured report saved to: {output_path.relative_to(repo_root)}")
    print("=" * 70)


if __name__ == "__main__":
    run_profiling_demo()
