"""Module 4 — Missing Value Detection & Imputation

Implements structured, defensible missing-value treatment strategies:
- Missing value detection (counts, percentages, completeness)
- Critical identifier validation (dropping rows missing unique entity IDs)
- Median imputation for skewed/continuous numerical features
- Mode imputation for categorical features
- Forward-fill (ffill) for time-series and sequential features
- Before vs. After metrics comparison and strategy audit logging
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd


def detect_missing_values(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Detect and summarize missing values across all columns of a DataFrame.

    Parameters:
        df: Input Pandas DataFrame.

    Returns:
        Dictionary containing overall missingness and per-column null statistics.
    """
    total_cells = df.size
    total_missing = int(df.isna().sum().sum())
    total_rows = max(len(df), 1)

    column_summary: Dict[str, Dict[str, Any]] = {}
    for col in df.columns:
        null_count = int(df[col].isna().sum())
        null_pct = round((null_count / total_rows) * 100, 2)
        column_summary[col] = {
            "null_count": null_count,
            "null_percentage": null_pct,
            "has_missing": null_count > 0,
            "dtype": str(df[col].dtype),
        }

    return {
        "total_rows": int(len(df)),
        "total_columns": int(len(df.columns)),
        "total_missing_cells": total_missing,
        "total_cells": int(total_cells),
        "overall_missing_pct": round((total_missing / max(total_cells, 1)) * 100, 2),
        "columns": column_summary,
    }


def handle_missing_values(
    df: pd.DataFrame,
    critical_identifiers: Optional[List[str]] = None,
    numerical_median_cols: Optional[List[str]] = None,
    categorical_mode_cols: Optional[List[str]] = None,
    time_series_cols: Optional[List[str]] = None,
    date_sort_col: Optional[str] = None,
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Apply defensible missing value treatment strategies with full audit logging.

    Parameters:
        df: Input DataFrame.
        critical_identifiers: Columns where nulls cannot be imputed (rows are dropped).
        numerical_median_cols: Numerical columns to impute using column median.
        categorical_mode_cols: Categorical columns to impute using column mode.
        time_series_cols: Sequential columns to impute using forward fill.
        date_sort_col: Optional date column to sort by before time-series forward fill.

    Returns:
        Tuple of (Cleaned DataFrame, Strategy Audit Log).
    """
    cleaned_df = df.copy()
    treatment_log: List[Dict[str, Any]] = []

    # 1. Critical Identifier Treatment (Row Dropping)
    if critical_identifiers:
        for id_col in critical_identifiers:
            if id_col in cleaned_df.columns:
                null_count = int(cleaned_df[id_col].isna().sum())
                if null_count > 0:
                    cleaned_df = cleaned_df.dropna(subset=[id_col]).copy()
                    treatment_log.append({
                        "column": id_col,
                        "strategy": "drop_rows",
                        "affected_records": null_count,
                        "imputed_value": None,
                        "reasoning": (
                            f"Dropped {null_count} rows with missing critical identifier '{id_col}'. "
                            "Primary keys cannot be reliably imputed without introducing artificial identity collisions."
                        ),
                    })

    # 2. Time-Series Forward-Fill (ffill)
    if time_series_cols:
        if date_sort_col and date_sort_col in cleaned_df.columns:
            cleaned_df = cleaned_df.sort_values(by=date_sort_col).reset_index(drop=True)

        for ts_col in time_series_cols:
            if ts_col in cleaned_df.columns:
                null_count = int(cleaned_df[ts_col].isna().sum())
                if null_count > 0:
                    cleaned_df[ts_col] = cleaned_df[ts_col].ffill()
                    # If leading values are still null after ffill, apply bfill
                    remaining_nulls = int(cleaned_df[ts_col].isna().sum())
                    if remaining_nulls > 0:
                        cleaned_df[ts_col] = cleaned_df[ts_col].bfill()

                    treatment_log.append({
                        "column": ts_col,
                        "strategy": "forward_fill",
                        "affected_records": null_count,
                        "imputed_value": "propagated_prior_value",
                        "reasoning": (
                            f"Forward-filled {null_count} missing values in time-series column '{ts_col}'. "
                            "Assumes temporal state continuity until subsequent observation."
                        ),
                    })

    # 3. Numerical Median Imputation
    if numerical_median_cols:
        for num_col in numerical_median_cols:
            if num_col in cleaned_df.columns:
                null_count = int(cleaned_df[num_col].isna().sum())
                if null_count > 0:
                    median_val = float(cleaned_df[num_col].median())
                    cleaned_df[num_col] = cleaned_df[num_col].fillna(median_val)
                    treatment_log.append({
                        "column": num_col,
                        "strategy": "median_imputation",
                        "affected_records": null_count,
                        "imputed_value": round(median_val, 4),
                        "reasoning": (
                            f"Imputed {null_count} missing values in '{num_col}' using column median ({round(median_val, 4)}). "
                            "Median is chosen over mean because it is robust against outliers and distribution skewness."
                        ),
                    })

    # 4. Categorical Mode Imputation
    if categorical_mode_cols:
        for cat_col in categorical_mode_cols:
            if cat_col in cleaned_df.columns:
                null_count = int(cleaned_df[cat_col].isna().sum())
                if null_count > 0:
                    mode_series = cleaned_df[cat_col].mode()
                    mode_val = str(mode_series.iloc[0]) if not mode_series.empty else "Unknown"
                    cleaned_df[cat_col] = cleaned_df[cat_col].fillna(mode_val)
                    treatment_log.append({
                        "column": cat_col,
                        "strategy": "mode_imputation",
                        "affected_records": null_count,
                        "imputed_value": mode_val,
                        "reasoning": (
                            f"Imputed {null_count} missing values in '{cat_col}' using category mode ('{mode_val}'). "
                            "Preserves categorical distribution mode without introducing synthetic arbitrary categories."
                        ),
                    })

    return cleaned_df, treatment_log


def generate_imputation_report(
    df_before: pd.DataFrame,
    df_after: pd.DataFrame,
    treatment_log: List[Dict[str, Any]],
    report_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """
    Generate comprehensive before vs. after missingness comparison metrics.

    Parameters:
        df_before: Raw DataFrame before treatment.
        df_after: Cleaned DataFrame after imputation and row removal.
        treatment_log: Log of strategies applied per column.
        report_path: Optional path to save JSON report.

    Returns:
        Structured audit dictionary.
    """
    before_stats = detect_missing_values(df_before)
    after_stats = detect_missing_values(df_after)

    report: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "rows_before": before_stats["total_rows"],
            "rows_after": after_stats["total_rows"],
            "rows_removed": before_stats["total_rows"] - after_stats["total_rows"],
            "missing_cells_before": before_stats["total_missing_cells"],
            "missing_cells_after": after_stats["total_missing_cells"],
            "completeness_before_pct": round(100 - before_stats["overall_missing_pct"], 2),
            "completeness_after_pct": round(100 - after_stats["overall_missing_pct"], 2),
        },
        "treatment_log": treatment_log,
        "before_treatment": before_stats,
        "after_treatment": after_stats,
    }

    if report_path:
        save_path = Path(report_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)

    return report


def run_missing_value_pipeline() -> None:
    """Execute complete missing value detection and imputation workflow demonstration."""
    repo_root = Path(__file__).resolve().parents[1]
    input_path = repo_root / "data/raw/raw_with_missing.csv"
    output_data_path = repo_root / "data/processed/cleaned_imputed.csv"
    output_report_path = repo_root / "output/missing_value_report.json"

    print("=" * 70)
    print("MODULE 4: MISSING VALUE DETECTION & IMPUTATION")
    print("=" * 70)

    if not input_path.exists():
        print(f"[ERROR] Input dataset not found: {input_path}")
        return

    raw_df = pd.read_csv(input_path)
    print(f"\n[1] Initial Missing Value Detection ({input_path.name})")
    initial_stats = detect_missing_values(raw_df)
    print(f"  Total Rows: {initial_stats['total_rows']}")
    print(f"  Total Missing Cells: {initial_stats['total_missing_cells']} ({initial_stats['overall_missing_pct']}%)")
    for col, info in initial_stats["columns"].items():
        if info["has_missing"]:
            print(f"  - {col}: {info['null_count']} nulls ({info['null_percentage']}%)")

    print("\n[2] Applying Missing Value Treatments...")
    cleaned_df, audit_log = handle_missing_values(
        df=raw_df,
        critical_identifiers=["viewer_id"],
        numerical_median_cols=["monthly_fee", "watch_duration_minutes", "completion_rate"],
        categorical_mode_cols=["country", "subscription_plan", "user_name"],
        time_series_cols=["viewing_date"],
        date_sort_col="viewing_date",
    )

    for entry in audit_log:
        print(f"  [{entry['strategy'].upper()}] {entry['column']}: {entry['reasoning']}")

    # Save cleaned dataset
    output_data_path.parent.mkdir(parents=True, exist_ok=True)
    cleaned_df.to_csv(output_data_path, index=False)

    print("\n[3] Generating Before vs. After Comparison Report...")
    report = generate_imputation_report(
        df_before=raw_df,
        df_after=cleaned_df,
        treatment_log=audit_log,
        report_path=output_report_path,
    )

    s = report["summary"]
    print(f"  Rows: {s['rows_before']} -> {s['rows_after']} (Dropped {s['rows_removed']} invalid ID rows)")
    print(f"  Missing Cells: {s['missing_cells_before']} -> {s['missing_cells_after']}")
    print(f"  Completeness: {s['completeness_before_pct']}% -> {s['completeness_after_pct']}%")
    print(f"\n[OK] Cleaned dataset saved to: {output_data_path.relative_to(repo_root)}")
    print(f"[OK] Audit report saved to: {output_report_path.relative_to(repo_root)}")
    print("=" * 70)


if __name__ == "__main__":
    run_missing_value_pipeline()
