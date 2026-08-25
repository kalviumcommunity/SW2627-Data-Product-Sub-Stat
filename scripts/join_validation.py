"""Module 3 — Multi-Source Merging & Join Validation

Provides robust multi-source dataset joining and integrity validation:
- Pre- and post-merge row count tracking.
- Merge key schema and nullity validation.
- Join cardinality assessment (1:1, 1:N, N:1, N:M).
- Unmatched key isolation on left and right sources with explicit reason tracking.
- Structured join audit reporting and business rationale documentation.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def assess_cardinality(
    left_df: pd.DataFrame,
    right_df: pd.DataFrame,
    left_key: str,
    right_key: str,
) -> str:
    """
    Determine the relationship cardinality between two DataFrames based on merge keys.

    Returns:
        One of: 'one_to_one', 'one_to_many', 'many_to_one', 'many_to_many'.
    """
    left_unique = left_df[left_key].is_unique
    right_unique = right_df[right_key].is_unique

    if left_unique and right_unique:
        return "one_to_one"
    elif left_unique and not right_unique:
        return "one_to_many"
    elif not left_unique and right_unique:
        return "many_to_one"
    else:
        return "many_to_many"


def perform_validated_merge(
    left_df: pd.DataFrame,
    right_df: pd.DataFrame,
    how: Literal["inner", "left", "right", "outer"] = "left",
    on: Optional[Union[str, List[str]]] = None,
    left_on: Optional[Union[str, List[str]]] = None,
    right_on: Optional[Union[str, List[str]]] = None,
    suffixes: Tuple[str, str] = ("_left", "_right"),
    business_reason: Optional[str] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Execute an audited merge between two datasets, capturing unmatched keys and metrics.

    Parameters:
        left_df: Primary left DataFrame.
        right_df: Secondary right DataFrame.
        how: Type of join ('inner', 'left', 'right', 'outer').
        on: Common column name or list of columns to join on.
        left_on: Column(s) in left DataFrame if names differ.
        right_on: Column(s) in right DataFrame if names differ.
        suffixes: Suffixes for overlapping columns.
        business_reason: Business explanation for the chosen join type.

    Returns:
        Tuple containing:
        - merged_df: Resulting DataFrame from the requested join.
        - unmatched_left: Records present in left DataFrame with no key match in right DataFrame.
        - unmatched_right: Records present in right DataFrame with no key match in left DataFrame.
        - report: Structured validation metrics dictionary.
    """
    l_key = on if on is not None else left_on
    r_key = on if on is not None else right_on

    if l_key is None or r_key is None:
        raise ValueError("Join keys must be specified via 'on' or 'left_on'/'right_on'.")

    # Validate key presence
    l_keys_list = [l_key] if isinstance(l_key, str) else list(l_key)
    r_keys_list = [r_key] if isinstance(r_key, str) else list(r_key)

    for k in l_keys_list:
        if k not in left_df.columns:
            raise KeyError(f"Left join key '{k}' not found in left DataFrame.")
    for k in r_keys_list:
        if k not in right_df.columns:
            raise KeyError(f"Right join key '{k}' not found in right DataFrame.")

    left_rows = len(left_df)
    right_rows = len(right_df)

    # Check key nulls
    left_null_keys = int(left_df[l_keys_list].isna().any(axis=1).sum())
    right_null_keys = int(right_df[r_keys_list].isna().any(axis=1).sum())

    # Evaluate cardinality on primary key
    cardinality = assess_cardinality(left_df, right_df, l_keys_list[0], r_keys_list[0])

    # 1. Perform full outer join with indicator to isolate all match categories
    outer_merged = pd.merge(
        left_df,
        right_df,
        how="outer",
        left_on=left_on if left_on else on,
        right_on=right_on if right_on else on,
        suffixes=suffixes,
        indicator=True,
    )

    both_mask = outer_merged["_merge"] == "both"
    left_only_mask = outer_merged["_merge"] == "left_only"
    right_only_mask = outer_merged["_merge"] == "right_only"

    matched_both_count = int(both_mask.sum())
    left_only_count = int(left_only_mask.sum())
    right_only_count = int(right_only_mask.sum())

    # Extract unmatched subsets
    # Drop columns that originated from the opposite table
    left_cols = list(left_df.columns)
    right_cols = list(right_df.columns)

    unmatched_left = outer_merged[left_only_mask][left_cols].copy()
    unmatched_right = outer_merged[right_only_mask][right_cols].copy()

    # 2. Perform the actual requested merge
    merged_df = pd.merge(
        left_df,
        right_df,
        how=how,
        left_on=left_on if left_on else on,
        right_on=right_on if right_on else on,
        suffixes=suffixes,
    )
    final_rows = len(merged_df)

    # Default business justification if omitted
    default_reasons = {
        "left": "Retain all records from the primary entity (left dataset) to preserve full user/profile coverage, enriching with secondary transactional events where available.",
        "inner": "Retain only records with verified relationships on both sides for strict relational integrity analysis.",
        "right": "Retain all secondary activity records, associating parent attributes where available.",
        "outer": "Preserve all records from both entities to perform comprehensive data reconciliation and audit discrepancies.",
    }
    selected_reason = business_reason or default_reasons.get(how, "Standard dataset merge.")

    # Match percentages
    left_match_pct = round((matched_both_count / max(left_rows, 1)) * 100, 2)
    right_match_pct = round((matched_both_count / max(right_rows, 1)) * 100, 2)

    report = {
        "status": "SUCCESS",
        "timestamp": datetime.now().isoformat(),
        "join_configuration": {
            "join_type": how,
            "left_keys": l_keys_list,
            "right_keys": r_keys_list,
            "cardinality": cardinality,
            "business_reason": selected_reason,
        },
        "row_counts": {
            "left_source_rows": left_rows,
            "right_source_rows": right_rows,
            "merged_output_rows": final_rows,
            "matched_both_rows": matched_both_count,
            "unmatched_left_rows": left_only_count,
            "unmatched_right_rows": right_only_count,
        },
        "match_rates": {
            "left_match_pct": left_match_pct,
            "right_match_pct": right_match_pct,
        },
        "data_quality_flags": {
            "left_null_keys": left_null_keys,
            "right_null_keys": right_null_keys,
            "has_unmatched_left": left_only_count > 0,
            "has_unmatched_right": right_only_count > 0,
        },
    }

    return merged_df, unmatched_left, unmatched_right, report


def run_join_pipeline(
    left_path: Union[str, Path] = "data/raw/viewers_master.csv",
    right_path: Union[str, Path] = "data/raw/subscription_events.csv",
    join_key: str = "viewer_id",
    join_type: Literal["inner", "left", "right", "outer"] = "left",
    output_merged_path: Union[str, Path] = "data/processed/merged_dataset.csv",
    unmatched_left_path: Union[str, Path] = "output/unmatched_left_records.csv",
    unmatched_right_path: Union[str, Path] = "output/unmatched_right_records.csv",
    report_path: Union[str, Path] = "output/join_validation_report.json",
    business_reason: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run multi-source join validation pipeline on raw datasets.
    """
    left_file = Path(left_path)
    right_file = Path(right_path)
    out_merged = Path(output_merged_path)
    out_unmatched_l = Path(unmatched_left_path)
    out_unmatched_r = Path(unmatched_right_path)
    out_report = Path(report_path)

    out_merged.parent.mkdir(parents=True, exist_ok=True)
    out_unmatched_l.parent.mkdir(parents=True, exist_ok=True)
    out_report.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Reading left dataset from %s and right dataset from %s", left_file, right_file)
    left_df = pd.read_csv(left_file)
    right_df = pd.read_csv(right_file)

    merged_df, unmatched_l, unmatched_r, report = perform_validated_merge(
        left_df=left_df,
        right_df=right_df,
        how=join_type,
        on=join_key,
        business_reason=business_reason,
    )

    # Save artifacts
    merged_df.to_csv(out_merged, index=False)
    unmatched_l.to_csv(out_unmatched_l, index=False)
    unmatched_r.to_csv(out_unmatched_r, index=False)

    report["left_source_file"] = str(left_file)
    report["right_source_file"] = str(right_file)
    report["output_merged_file"] = str(out_merged)

    with open(out_report, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info(
        "Merge complete: %d left rows + %d right rows -> %d merged rows (matched: %d, unmatched left: %d, unmatched right: %d)",
        len(left_df),
        len(right_df),
        len(merged_df),
        report["row_counts"]["matched_both_rows"],
        report["row_counts"]["unmatched_left_rows"],
        report["row_counts"]["unmatched_right_rows"],
    )

    return report


if __name__ == "__main__":
    run_join_pipeline()
