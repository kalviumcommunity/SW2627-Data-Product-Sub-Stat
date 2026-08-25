"""Module 2 — Data Consistency & Validation Rules

Provides a comprehensive, rule-based data validation framework:
- Range checks (min/max numeric constraints)
- Null and required-field assertions
- Regex and format validation
- Referential integrity checks against master/parent keys
- Domain business-rule validation (e.g. end_time >= start_time)
- Combined multi-rule evaluation, failed records isolation, and structured reporting.
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class ValidationRule:
    """Represents an individual validation rule."""

    def __init__(
        self,
        name: str,
        rule_type: str,
        description: str,
        validator_fn: Callable[[pd.DataFrame], pd.Series],
    ):
        self.name = name
        self.rule_type = rule_type
        self.description = description
        self.validator_fn = validator_fn

    def evaluate(self, df: pd.DataFrame) -> pd.Series:
        """
        Evaluate rule on DataFrame.

        Returns:
            Boolean Series where True indicates PASS and False indicates FAIL.
        """
        try:
            return self.validator_fn(df).astype(bool)
        except Exception as e:
            logger.warning("Error evaluating rule '%s': %s", self.name, str(e))
            # On unexpected error, flag rows as failed
            return pd.Series(False, index=df.index)


def check_range(
    df: pd.DataFrame,
    column: str,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
) -> pd.Series:
    """
    Validate that numeric values in a column fall within [min_val, max_val].

    Parameters:
        df: Input DataFrame.
        column: Numeric column name.
        min_val: Minimum acceptable value (inclusive).
        max_val: Maximum acceptable value (inclusive).

    Returns:
        Boolean Series (True for pass, False for fail).
    """
    if column not in df.columns:
        return pd.Series(False, index=df.index)

    series = pd.to_numeric(df[column], errors="coerce")
    mask = series.notna()

    if min_val is not None:
        mask = mask & (series >= min_val)
    if max_val is not None:
        mask = mask & (series <= max_val)

    return mask


def check_required_fields(
    df: pd.DataFrame,
    columns: List[str],
) -> pd.Series:
    """
    Validate that specified columns are non-null and not empty strings.

    Parameters:
        df: Input DataFrame.
        columns: List of required column names.

    Returns:
        Boolean Series (True if all required columns are populated).
    """
    mask = pd.Series(True, index=df.index)
    for col in columns:
        if col not in df.columns:
            return pd.Series(False, index=df.index)
        col_series = df[col]
        # Check null, NaN, and blank strings
        valid_col = col_series.notna() & (col_series.astype(str).str.strip() != "")
        mask = mask & valid_col
    return mask


def check_regex_format(
    df: pd.DataFrame,
    column: str,
    pattern: str,
) -> pd.Series:
    """
    Validate that string column matches a given regular expression.

    Parameters:
        df: Input DataFrame.
        column: Target string column.
        pattern: Regex pattern.

    Returns:
        Boolean Series (True if matching regex pattern).
    """
    if column not in df.columns:
        return pd.Series(False, index=df.index)

    compiled_regex = re.compile(pattern)
    series = df[column].fillna("").astype(str)
    return series.apply(lambda val: bool(compiled_regex.match(val)) if val else False)


def check_referential_integrity(
    df: pd.DataFrame,
    column: str,
    valid_keys: Union[Set[Any], List[Any], pd.Series],
) -> pd.Series:
    """
    Validate that foreign key values exist in a master reference set.

    Parameters:
        df: Input DataFrame.
        column: Foreign key column name.
        valid_keys: Set or iterable of valid primary keys.

    Returns:
        Boolean Series (True if foreign key is valid).
    """
    if column not in df.columns:
        return pd.Series(False, index=df.index)

    key_set = set(valid_keys)
    return df[column].isin(key_set)


def check_date_order(
    df: pd.DataFrame,
    start_col: str,
    end_col: str,
) -> pd.Series:
    """
    Validate business rule: end_date >= start_date.

    Parameters:
        df: Input DataFrame.
        start_col: Name of start timestamp column.
        end_col: Name of end timestamp column.

    Returns:
        Boolean Series (True if end >= start and both are valid dates).
    """
    if start_col not in df.columns or end_col not in df.columns:
        return pd.Series(False, index=df.index)

    start_dt = pd.to_datetime(df[start_col], errors="coerce")
    end_dt = pd.to_datetime(df[end_col], errors="coerce")

    valid_dates = start_dt.notna() & end_dt.notna()
    order_valid = end_dt >= start_dt

    return valid_dates & order_valid


class DataValidator:
    """Comprehensive validation engine to register and execute consistency rules."""

    def __init__(self):
        self.rules: List[ValidationRule] = []

    def add_rule(
        self,
        name: str,
        rule_type: str,
        description: str,
        validator_fn: Callable[[pd.DataFrame], pd.Series],
    ) -> "DataValidator":
        """Register a new validation rule."""
        rule = ValidationRule(name, rule_type, description, validator_fn)
        self.rules.append(rule)
        return self

    def validate(
        self,
        df: pd.DataFrame,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
        """
        Execute all registered validation rules on DataFrame.

        Returns:
            Tuple of:
            - passed_df: Rows passing all rules
            - failed_df: Rows failing at least one rule with failure audit metadata
            - report: Structured validation summary dictionary
        """
        total_rows = len(df)
        if total_rows == 0:
            return df.copy(), df.copy(), {"total_records": 0, "passed_records": 0, "failed_records": 0, "rules": []}

        eval_df = df.copy()
        rule_results: Dict[str, pd.Series] = {}
        rule_summaries: List[Dict[str, Any]] = []

        # Evaluate each rule
        for rule in self.rules:
            result = rule.evaluate(eval_df)
            rule_results[rule.name] = result
            failed_count = int((~result).sum())
            passed_count = int(result.sum())
            pass_rate = round((passed_count / total_rows) * 100, 2)

            rule_summaries.append(
                {
                    "rule_name": rule.name,
                    "rule_type": rule.rule_type,
                    "description": rule.description,
                    "records_evaluated": total_rows,
                    "passed_records": passed_count,
                    "failed_records": failed_count,
                    "pass_rate_pct": pass_rate,
                }
            )

        # Combine results across all rules
        results_matrix = pd.DataFrame(rule_results, index=eval_df.index)
        all_passed_mask = results_matrix.all(axis=1)

        passed_df = eval_df[all_passed_mask].copy()
        failed_df = eval_df[~all_passed_mask].copy()

        # Build granular failure audit info for failed rows
        failed_rules_list = []
        failed_reasons_list = []

        for idx in failed_df.index:
            row_fails = results_matrix.loc[idx]
            failed_names = row_fails[~row_fails].index.tolist()
            failed_rules_list.append("; ".join(failed_names))
            failed_reasons_list.append(
                "; ".join([f"{name} ({next(r.description for r in self.rules if r.name == name)})" for name in failed_names])
            )

        failed_df["_failed_rules"] = failed_rules_list
        failed_df["_failure_reasons"] = failed_reasons_list

        passed_count = len(passed_df)
        failed_count = len(failed_df)
        overall_pass_rate = round((passed_count / total_rows) * 100, 2)

        report = {
            "status": "SUCCESS",
            "timestamp": datetime.now().isoformat(),
            "total_records": total_rows,
            "passed_records": passed_count,
            "failed_records": failed_count,
            "overall_pass_rate_pct": overall_pass_rate,
            "rules_evaluated_count": len(self.rules),
            "rule_details": rule_summaries,
        }

        return passed_df, failed_df, report


def build_default_validator(content_catalog_path: Union[str, Path] = "data/raw/content_catalog.csv") -> DataValidator:
    """Construct and configure the domain validator with standard business rules."""
    validator = DataValidator()

    # Load valid foreign keys if catalog exists
    valid_content_ids: Set[str] = set()
    catalog_file = Path(content_catalog_path)
    if catalog_file.exists():
        cat_df = pd.read_csv(catalog_file)
        if "content_id" in cat_df.columns:
            valid_content_ids = set(cat_df["content_id"].dropna().astype(str))

    # 1. Required Fields Check
    validator.add_rule(
        name="REQUIRED_FIELDS",
        rule_type="null_check",
        description="viewer_id, content_id, and start_time must not be null or blank",
        validator_fn=lambda df: check_required_fields(df, ["viewer_id", "content_id", "start_time"]),
    )

    # 2. Viewer ID Regex Format
    validator.add_rule(
        name="VIEWER_ID_FORMAT",
        rule_type="regex_format",
        description="viewer_id must follow the pattern ^V[0-9]{3,}$",
        validator_fn=lambda df: check_regex_format(df, "viewer_id", r"^V\d{3,}$"),
    )

    # 3. Email Format Regex
    validator.add_rule(
        name="EMAIL_FORMAT",
        rule_type="regex_format",
        description="user_email must be a valid email format",
        validator_fn=lambda df: check_regex_format(df, "user_email", r"^[\w\.-]+@[\w\.-]+\.\w+$"),
    )

    # 4. Watch Duration Range Check (0 to 600 minutes)
    validator.add_rule(
        name="WATCH_DURATION_RANGE",
        rule_type="range_check",
        description="watch_duration_mins must be between 0.0 and 600.0 minutes",
        validator_fn=lambda df: check_range(df, "watch_duration_mins", min_val=0.0, max_val=600.0),
    )

    # 5. User Rating Range Check (1.0 to 5.0)
    validator.add_rule(
        name="USER_RATING_RANGE",
        rule_type="range_check",
        description="user_rating must be between 1.0 and 5.0",
        validator_fn=lambda df: check_range(df, "user_rating", min_val=1.0, max_val=5.0),
    )

    # 6. Referential Integrity Check
    if valid_content_ids:
        validator.add_rule(
            name="CONTENT_ID_REFERENTIAL_INTEGRITY",
            rule_type="referential_integrity",
            description="content_id must exist in content catalog master reference",
            validator_fn=lambda df: check_referential_integrity(df, "content_id", valid_content_ids),
        )

    # 7. Business Rule: End Time >= Start Time
    validator.add_rule(
        name="CHRONOLOGICAL_SESSION_ORDER",
        rule_type="business_rule",
        description="end_time must be chronologically greater than or equal to start_time",
        validator_fn=lambda df: check_date_order(df, start_col="start_time", end_col="end_time"),
    )

    return validator


def run_validation_pipeline(
    input_path: Union[str, Path] = "data/raw/validation_sample.csv",
    catalog_path: Union[str, Path] = "data/raw/content_catalog.csv",
    failed_output_path: Union[str, Path] = "data/processed/failed_validation_records.csv",
    passed_output_path: Union[str, Path] = "data/processed/clean_validated_records.csv",
    report_output_path: Union[str, Path] = "output/data_validation_report.json",
) -> Dict[str, Any]:
    """
    Execute data consistency validation pipeline and save failed audit logs and reports.

    Returns:
        Structured validation summary dictionary.
    """
    input_file = Path(input_path)
    failed_out = Path(failed_output_path)
    passed_out = Path(passed_output_path)
    report_out = Path(report_output_path)

    failed_out.parent.mkdir(parents=True, exist_ok=True)
    report_out.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Loading validation input data from %s", input_file)
    df = pd.read_csv(input_file)

    validator = build_default_validator(catalog_path)
    passed_df, failed_df, report = validator.validate(df)

    # Save outputs
    passed_df.to_csv(passed_out, index=False)
    failed_df.to_csv(failed_out, index=False)

    report["input_file"] = str(input_file)
    report["passed_output_file"] = str(passed_out)
    report["failed_output_file"] = str(failed_out)

    with open(report_out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info(
        "Validation complete: %d total, %d passed (%.1f%%), %d failed",
        report["total_records"],
        report["passed_records"],
        report["overall_pass_rate_pct"],
        report["failed_records"],
    )
    return report


if __name__ == "__main__":
    run_validation_pipeline()
