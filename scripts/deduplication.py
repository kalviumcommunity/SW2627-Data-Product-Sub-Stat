"""Module 6 — Duplicate Detection & Record Deduplication

Implements comprehensive duplicate detection and defensible deduplication routines:
- Exact duplicate detection across all columns
- Near-duplicate detection based on primary and composite business keys
- Multiple defensible deduplication strategies:
    * 'first': Retains the first observed record
    * 'last': Retains the most recent record (after sorting)
    * 'most_complete': Retains the record with the fewest missing/null values
- Audit reporting with exported removed records and before/after metrics
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

import pandas as pd


def detect_exact_duplicates(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Detect exact duplicate rows where every column has identical values.

    Parameters:
        df: Input Pandas DataFrame.

    Returns:
        Dictionary with count, percentage, and boolean duplicate flag.
    """
    total_rows = max(len(df), 1)
    dup_mask = df.duplicated(keep=False)
    exact_dup_count = int(df.duplicated(keep="first").sum())
    exact_dup_pct = round((exact_dup_count / total_rows) * 100, 2)

    return {
        "exact_duplicate_rows": exact_dup_count,
        "exact_duplicate_pct": exact_dup_pct,
        "has_exact_duplicates": exact_dup_count > 0,
        "total_rows_involved": int(dup_mask.sum()),
    }


def detect_near_duplicates(
    df: pd.DataFrame,
    business_keys: List[str],
) -> Dict[str, Any]:
    """
    Detect near-duplicate records sharing business keys but differing in non-key columns.

    Parameters:
        df: Input Pandas DataFrame.
        business_keys: List of column names forming the primary/composite business key.

    Returns:
        Dictionary with near-duplicate statistics and key groupings.
    """
    total_rows = max(len(df), 1)
    missing_keys = [k for k in business_keys if k not in df.columns]
    if missing_keys:
        raise ValueError(f"Business keys not found in DataFrame: {missing_keys}")

    key_dup_mask = df.duplicated(subset=business_keys, keep="first")
    near_dup_count = int(key_dup_mask.sum())
    near_dup_pct = round((near_dup_count / total_rows) * 100, 2)

    return {
        "business_keys": business_keys,
        "key_duplicate_rows": near_dup_count,
        "key_duplicate_pct": near_dup_pct,
        "has_near_duplicates": near_dup_count > 0,
    }


def deduplicate_dataset(
    df: pd.DataFrame,
    strategy: Literal["first", "last", "most_complete"] = "most_complete",
    business_keys: Optional[List[str]] = None,
    sort_by: Optional[Union[str, List[str]]] = None,
    ascending: bool = True,
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Deduplicate a dataset using a defensible, audited strategy.

    Parameters:
        df: Input Pandas DataFrame.
        strategy: 'first', 'last', or 'most_complete'.
        business_keys: Columns defining identity. If None, uses all columns (exact deduplication).
        sort_by: Optional column(s) to sort by before selecting first/last.
        ascending: Sort order if sort_by is provided.

    Returns:
        Tuple of (Deduplicated DataFrame, Removed Records Audit DataFrame, Metrics Dictionary).
    """
    keys = business_keys or list(df.columns)
    working_df = df.copy()
    working_df["_orig_idx"] = working_df.index

    # 1. Optional sorting
    if sort_by:
        working_df = working_df.sort_values(by=sort_by, ascending=ascending)

    # 2. Strategy Application
    if strategy == "most_complete":
        # Calculate completeness score (number of non-null values per row)
        working_df["_completeness"] = working_df.notna().sum(axis=1)
        # Sort so most complete rows appear first within each key group
        sort_cols = keys + ["_completeness"]
        ascending_spec = [True] * len(keys) + [False]
        working_df = working_df.sort_values(by=sort_cols, ascending=ascending_spec)

        keep_mask = ~working_df.duplicated(subset=keys, keep="first")
        deduped = working_df[keep_mask].sort_values(by="_orig_idx").drop(columns=["_orig_idx", "_completeness"])
        removed = working_df[~keep_mask].sort_values(by="_orig_idx").drop(columns=["_completeness"])
    elif strategy in ("first", "last"):
        keep_mask = ~working_df.duplicated(subset=keys, keep=strategy)
        deduped = working_df[keep_mask].sort_values(by="_orig_idx").drop(columns=["_orig_idx"])
        removed = working_df[~keep_mask].sort_values(by="_orig_idx")
    else:
        raise ValueError(f"Unknown deduplication strategy: '{strategy}'. Choose 'first', 'last', or 'most_complete'.")

    # Add audit metadata to removed records
    if not removed.empty:
        removed["dedup_strategy"] = strategy
        removed["business_keys_used"] = ", ".join(keys)
        removed["removal_timestamp"] = datetime.now().isoformat()

    total_before = len(df)
    total_after = len(deduped)
    total_removed = total_before - total_after
    pct_removed = round((total_removed / max(total_before, 1)) * 100, 2)

    metrics = {
        "strategy": strategy,
        "business_keys": keys,
        "rows_before": total_before,
        "rows_after": total_after,
        "records_removed": total_removed,
        "percentage_removed": pct_removed,
    }

    return deduped, removed, metrics


def generate_deduplication_report(
    metrics: Dict[str, Any],
    exact_stats: Dict[str, Any],
    report_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """
    Generate and save a structured JSON audit report for deduplication.

    Parameters:
        metrics: Output metrics from deduplicate_dataset.
        exact_stats: Output from detect_exact_duplicates.
        report_path: Optional destination path for JSON export.

    Returns:
        Structured audit dictionary.
    """
    report = {
        "timestamp": datetime.now().isoformat(),
        "strategy_rationale": {
            "strategy_chosen": metrics["strategy"],
            "business_keys": metrics["business_keys"],
            "rationale": (
                "Strategy 'most_complete' prioritizes records with maximum feature richness "
                "and fewest missing attributes when duplicate entity keys collide."
            ),
        },
        "exact_duplicates_detected": exact_stats,
        "deduplication_summary": metrics,
    }

    if report_path:
        save_path = Path(report_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)

    return report


def run_deduplication_pipeline() -> None:
    """Execute complete duplicate detection and deduplication demonstration."""
    repo_root = Path(__file__).resolve().parents[1]
    input_path = repo_root / "data/raw/raw_with_duplicates.csv"
    output_data_path = repo_root / "data/processed/deduplicated_data.csv"
    output_audit_path = repo_root / "output/removed_duplicates_audit.csv"
    output_report_path = repo_root / "output/deduplication_report.json"

    print("=" * 70)
    print("MODULE 6: DUPLICATE DETECTION & RECORD DEDUPLICATION")
    print("=" * 70)

    if not input_path.exists():
        print(f"[ERROR] Input dataset not found: {input_path}")
        return

    df_raw = pd.read_csv(input_path)
    print(f"\n[1] Input Dataset: {input_path.name} ({len(df_raw)} rows)")

    # 1. Detect Exact Duplicates
    exact_stats = detect_exact_duplicates(df_raw)
    print(f"  Exact Duplicate Rows: {exact_stats['exact_duplicate_rows']} ({exact_stats['exact_duplicate_pct']}%)")

    # 2. Detect Near Duplicates on Composite Business Keys
    composite_keys = ["viewer_id", "content_id", "watch_date"]
    near_stats = detect_near_duplicates(df_raw, composite_keys)
    print(f"  Near-Duplicates on {composite_keys}: {near_stats['key_duplicate_rows']} ({near_stats['key_duplicate_pct']}%)")

    # 3. Apply Most-Complete Deduplication
    print("\n[2] Executing 'most_complete' Deduplication Strategy...")
    deduped_df, removed_df, metrics = deduplicate_dataset(
        df=df_raw,
        strategy="most_complete",
        business_keys=composite_keys,
    )

    print(f"  Rows Before: {metrics['rows_before']}")
    print(f"  Rows After:  {metrics['rows_after']}")
    print(f"  Records Removed: {metrics['records_removed']} ({metrics['percentage_removed']}%)")

    # 4. Save Outputs & Audit Log
    output_data_path.parent.mkdir(parents=True, exist_ok=True)
    deduped_df.to_csv(output_data_path, index=False)

    output_audit_path.parent.mkdir(parents=True, exist_ok=True)
    removed_df.to_csv(output_audit_path, index=False)

    report = generate_deduplication_report(
        metrics=metrics,
        exact_stats=exact_stats,
        report_path=output_report_path,
    )

    print(f"\n[OK] Cleaned deduplicated dataset saved to: {output_data_path.relative_to(repo_root)}")
    print(f"[OK] Audit of removed duplicates saved to: {output_audit_path.relative_to(repo_root)}")
    print(f"[OK] Audit summary JSON saved to: {output_report_path.relative_to(repo_root)}")
    print("=" * 70)


if __name__ == "__main__":
    run_deduplication_pipeline()
