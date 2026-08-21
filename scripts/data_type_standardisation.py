"""Module 5 — Data Type Enforcement & Standardisation

Provides explicit data type casting, cleaning, and standardization routines:
- String to Datetime using explicit date formats (avoids ambiguous silent swaps)
- Currency and text to clean Numeric (removes symbols, thousands commas, units)
- Binary integers and text representations to Boolean (0/1, True/False, Yes/No)
- String and Categorical normalization (whitespace trimming, consistent casing)
- Validation of conversions and structured reporting of conversion failures
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd


def standardise_datetime(
    series: pd.Series,
    date_format: str = "%Y-%m-%d",
    errors: str = "coerce",
) -> Tuple[pd.Series, Dict[str, Any]]:
    """
    Convert string series to datetime using an explicit format string.

    Parameters:
        series: Pandas Series to convert.
        date_format: Explicit strftime format (e.g., '%Y-%m-%d').
        errors: How to handle unparseable values ('coerce' or 'raise').

    Returns:
        Tuple of (Standardized Datetime Series, Conversion Audit Info).
    """
    original_non_null = int(series.dropna().count())

    # Strip surrounding whitespace from string dates before parsing
    cleaned_series = series.astype(str).str.strip().replace({"nan": np.nan, "None": np.nan, "": np.nan})

    converted = pd.to_datetime(cleaned_series, format=date_format, errors=errors)
    converted_count = int(converted.dropna().count())
    failure_count = original_non_null - converted_count

    failures = []
    if failure_count > 0:
        failed_mask = series.notna() & converted.isna()
        failed_indices = series[failed_mask].index.tolist()
        failed_values = series[failed_mask].head(5).tolist()
        failures = [{"index": idx, "raw_value": str(val)} for idx, val in zip(failed_indices[:5], failed_values)]

    audit = {
        "target_type": "datetime64[ns]",
        "date_format_used": date_format,
        "total_inputs": original_non_null,
        "successful_conversions": converted_count,
        "failed_conversions": failure_count,
        "success_rate_pct": round((converted_count / max(original_non_null, 1)) * 100, 2),
        "sample_failures": failures,
    }

    return converted, audit


def standardise_numeric(
    series: pd.Series,
    target_type: str = "float",
    is_currency: bool = False,
    errors: str = "coerce",
) -> Tuple[pd.Series, Dict[str, Any]]:
    """
    Clean currency/text artifacts and cast series explicitly to numeric (float or integer).

    Parameters:
        series: Pandas Series to clean and cast.
        target_type: 'float' or 'int'.
        is_currency: If True, strips currency symbols ($, EUR, etc.) and commas.
        errors: 'coerce' or 'raise'.

    Returns:
        Tuple of (Standardized Numeric Series, Conversion Audit Info).
    """
    original_non_null = int(series.dropna().count())

    # Convert to string for regex cleanup
    cleaned = series.astype(str).str.strip()

    # Remove currency symbols, commas, and common non-numeric suffixes (e.g. 'hrs', 'USD')
    cleaned = cleaned.str.replace(r"[\$,€£₹]", "", regex=True)
    cleaned = cleaned.str.replace(r",", "", regex=True)
    cleaned = cleaned.str.replace(r"[a-zA-Z]+", "", regex=True).str.strip()
    cleaned = cleaned.replace({"": np.nan, "nan": np.nan, "None": np.nan})

    converted = pd.to_numeric(cleaned, errors=errors)

    if target_type == "int" and not converted.isna().any():
        converted = converted.astype(int)
    elif target_type == "float":
        converted = converted.astype(float)

    converted_count = int(converted.dropna().count())
    failure_count = original_non_null - converted_count

    failures = []
    if failure_count > 0:
        failed_mask = series.notna() & converted.isna()
        failed_indices = series[failed_mask].index.tolist()
        failed_values = series[failed_mask].head(5).tolist()
        failures = [{"index": idx, "raw_value": str(val)} for idx, val in zip(failed_indices[:5], failed_values)]

    audit = {
        "target_type": target_type,
        "is_currency": is_currency,
        "total_inputs": original_non_null,
        "successful_conversions": converted_count,
        "failed_conversions": failure_count,
        "success_rate_pct": round((converted_count / max(original_non_null, 1)) * 100, 2),
        "sample_failures": failures,
    }

    return converted, audit


def standardise_boolean(
    series: pd.Series,
    true_values: Tuple[Any, ...] = ("1", 1, "true", "t", "yes", "y", "True"),
    false_values: Tuple[Any, ...] = ("0", 0, "false", "f", "no", "n", "False"),
    errors: str = "coerce",
) -> Tuple[pd.Series, Dict[str, Any]]:
    """
    Standardize binary integers, text flags, and boolean representations to boolean (True/False).

    Parameters:
        series: Pandas Series to convert.
        true_values: Iterable of representations mapped to True.
        false_values: Iterable of representations mapped to False.
        errors: 'coerce' turns invalid values to NaN/None.

    Returns:
        Tuple of (Standardized Boolean Series, Conversion Audit Info).
    """
    original_non_null = int(series.dropna().count())

    true_set = {str(v).strip().lower() for v in true_values}
    false_set = {str(v).strip().lower() for v in false_values}

    def _convert_val(val: Any) -> Any:
        if pd.isna(val):
            return np.nan
        s_val = str(val).strip().lower()
        if s_val in true_set:
            return True
        if s_val in false_set:
            return False
        if errors == "coerce":
            return np.nan
        raise ValueError(f"Unrecognized boolean value: {val}")

    converted = series.apply(_convert_val).astype("boolean")
    converted_count = int(converted.dropna().count())
    failure_count = original_non_null - converted_count

    failures = []
    if failure_count > 0:
        failed_mask = series.notna() & converted.isna()
        failed_indices = series[failed_mask].index.tolist()
        failed_values = series[failed_mask].head(5).tolist()
        failures = [{"index": idx, "raw_value": str(val)} for idx, val in zip(failed_indices[:5], failed_values)]

    audit = {
        "target_type": "boolean",
        "total_inputs": original_non_null,
        "successful_conversions": converted_count,
        "failed_conversions": failure_count,
        "success_rate_pct": round((converted_count / max(original_non_null, 1)) * 100, 2),
        "sample_failures": failures,
    }

    return converted, audit


def standardise_string(
    series: pd.Series,
    case: str = "preserve",
    strip_whitespace: bool = True,
) -> Tuple[pd.Series, Dict[str, Any]]:
    """
    Trim whitespace and normalize text casing.

    Parameters:
        series: Pandas Series to clean.
        case: 'preserve', 'title', 'lower', 'upper'.
        strip_whitespace: Whether to strip leading/trailing whitespace.

    Returns:
        Tuple of (Cleaned String Series, Conversion Audit Info).
    """
    cleaned = series.copy()
    if strip_whitespace:
        cleaned = cleaned.astype(str).str.strip().replace({"nan": np.nan, "None": np.nan})

    if case == "title":
        cleaned = cleaned.str.title()
    elif case == "lower":
        cleaned = cleaned.str.lower()
    elif case == "upper":
        cleaned = cleaned.str.upper()

    return cleaned, {
        "target_type": "string",
        "case_normalization": case,
        "whitespace_stripped": strip_whitespace,
        "total_records": int(len(series)),
    }


def enforce_dataset_schema(
    df: pd.DataFrame,
    schema_spec: Dict[str, Dict[str, Any]],
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Enforce explicit data types and standardizations across a DataFrame according to schema specifications.

    Parameters:
        df: Input DataFrame.
        schema_spec: Dictionary mapping column names to transformation rules.

    Returns:
        Tuple of (Standardized DataFrame, Full Type Enforcement Audit Report).
    """
    standardized_df = df.copy()
    audit_report: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "total_columns": len(df.columns),
        "columns_enforced": len(schema_spec),
        "column_audits": {},
    }

    for col, rules in schema_spec.items():
        if col not in standardized_df.columns:
            continue

        target = rules.get("type", "string").lower()
        initial_dtype = str(standardized_df[col].dtype)

        if target == "datetime":
            fmt = rules.get("format", "%Y-%m-%d")
            series, audit = standardise_datetime(standardized_df[col], date_format=fmt)
            standardized_df[col] = series
        elif target in ("numeric", "float", "int", "currency"):
            is_curr = target == "currency" or rules.get("is_currency", False)
            t_type = "int" if target == "int" else "float"
            series, audit = standardise_numeric(standardized_df[col], target_type=t_type, is_currency=is_curr)
            standardized_df[col] = series
        elif target in ("bool", "boolean"):
            series, audit = standardise_boolean(standardized_df[col])
            standardized_df[col] = series
        elif target == "string":
            c_case = rules.get("case", "preserve")
            series, audit = standardise_string(standardized_df[col], case=c_case)
            standardized_df[col] = series
        else:
            audit = {"target_type": target, "status": "skipped"}

        audit["initial_dtype"] = initial_dtype
        audit["final_dtype"] = str(standardized_df[col].dtype)
        audit_report["column_audits"][col] = audit

    return standardized_df, audit_report


def run_type_standardisation_pipeline() -> None:
    """Execute complete data type enforcement and standardization demonstration."""
    repo_root = Path(__file__).resolve().parents[1]
    raw_path = repo_root / "data/raw/raw_unstandardised.csv"
    output_data_path = repo_root / "data/processed/standardised_data.csv"
    output_report_path = repo_root / "output/type_enforcement_report.json"

    print("=" * 70)
    print("MODULE 5: DATA TYPE ENFORCEMENT & STANDARDISATION")
    print("=" * 70)

    if not raw_path.exists():
        print(f"[ERROR] Sample raw file not found: {raw_path}")
        return

    df_raw = pd.read_csv(raw_path)
    print(f"\n[1] Input Dataset: {raw_path.name} ({len(df_raw)} rows)")
    print("  Initial Data Types:")
    for col, dtype in df_raw.dtypes.items():
        print(f"    - {col}: {dtype} (Sample: {df_raw[col].iloc[0]})")

    # Define explicit schema enforcement rules
    schema_rules = {
        "user_name": {"type": "string", "case": "preserve"},
        "signup_date": {"type": "datetime", "format": "%Y-%m-%d"},
        "monthly_fee": {"type": "currency", "is_currency": True},
        "watch_duration": {"type": "float"},
        "auto_renew": {"type": "boolean"},
        "churn": {"type": "int"},
        "plan": {"type": "string", "case": "title"},
    }

    print("\n[2] Enforcing Explicit Type Standardisation...")
    df_std, report = enforce_dataset_schema(df_raw, schema_rules)

    for col, audit in report["column_audits"].items():
        succ = audit.get("successful_conversions", audit.get("total_records", len(df_std)))
        rate = audit.get("success_rate_pct", 100.0)
        print(f"  [OK] {col}: {audit['initial_dtype']} -> {audit['final_dtype']} ({succ} records, {rate}%)")

    # Save outputs
    output_data_path.parent.mkdir(parents=True, exist_ok=True)
    df_std.to_csv(output_data_path, index=False)

    output_report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\n[OK] Standardized dataset saved to: {output_data_path.relative_to(repo_root)}")
    print(f"[OK] Audit report saved to: {output_report_path.relative_to(repo_root)}")
    print("=" * 70)


if __name__ == "__main__":
    run_type_standardisation_pipeline()
