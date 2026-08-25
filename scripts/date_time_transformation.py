"""Module 1 — Date & Time Transformation Pipeline

Provides reusable and modular routines for:
- Parsing timestamp and date strings into Pandas Datetime with format detection and error handling.
- Extracting temporal features: day of week, numeric day of week, hour, ISO week, month, quarter, year, weekend indicator.
- Datetime arithmetic: calculating days since purchase/event and duration between events.
- Time-series aggregation: resampling across weekly, monthly, and quarterly intervals.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def parse_datetime_column(
    df: pd.DataFrame,
    column: str,
    date_format: Optional[str] = None,
    errors: str = "coerce",
    utc: bool = False,
) -> pd.DataFrame:
    """
    Parse a column of date or timestamp strings into pandas datetime series.

    Parameters:
        df: Input pandas DataFrame.
        column: Name of the column to parse.
        date_format: Optional format string (e.g., '%Y-%m-%d %H:%M:%S').
        errors: Error handling mode ('coerce', 'raise', 'ignore').
        utc: Whether to convert parsed datetimes to UTC.

    Returns:
        DataFrame with the target column parsed to datetime64[ns].
    """
    if column not in df.columns:
        raise KeyError(f"Column '{column}' does not exist in DataFrame.")

    df_copy = df.copy()
    df_copy[column] = pd.to_datetime(
        df_copy[column],
        format=date_format,
        errors=errors,
        utc=utc,
    )
    return df_copy


def extract_temporal_features(
    df: pd.DataFrame,
    datetime_col: str,
    prefix: str = "",
) -> pd.DataFrame:
    """
    Extract calendar and cyclical temporal attributes from a datetime column.

    Extracted features:
    - day_of_week: Full name of day (e.g., 'Monday', 'Sunday')
    - day_of_week_num: Numeric day index (0 for Monday, 6 for Sunday)
    - hour: Hour of day (0 to 23)
    - is_weekend: Boolean flag (1 if Saturday/Sunday, else 0)
    - iso_week: ISO calendar week number (1 to 53)
    - month: Month number (1 to 12)
    - month_name: Full month name (e.g., 'January')
    - quarter: Calendar quarter (1 to 4)
    - year: Calendar year

    Parameters:
        df: Input pandas DataFrame.
        datetime_col: Name of the datetime column.
        prefix: Optional prefix for generated feature columns.

    Returns:
        DataFrame enriched with extracted temporal feature columns.
    """
    if datetime_col not in df.columns:
        raise KeyError(f"Column '{datetime_col}' not found in DataFrame.")

    df_copy = df.copy()

    # Ensure datetime dtype
    dt_series = pd.to_datetime(df_copy[datetime_col])

    p = prefix + "_" if prefix and not prefix.endswith("_") else prefix

    df_copy[f"{p}day_of_week"] = dt_series.dt.day_name()
    df_copy[f"{p}day_of_week_num"] = dt_series.dt.dayofweek
    df_copy[f"{p}hour"] = dt_series.dt.hour
    df_copy[f"{p}is_weekend"] = dt_series.dt.dayofweek.isin([5, 6]).astype(int)
    df_copy[f"{p}iso_week"] = dt_series.dt.isocalendar().week.astype("Int64")
    df_copy[f"{p}month"] = dt_series.dt.month
    df_copy[f"{p}month_name"] = dt_series.dt.month_name()
    df_copy[f"{p}quarter"] = dt_series.dt.quarter
    df_copy[f"{p}year"] = dt_series.dt.year

    return df_copy


def calculate_days_since_event(
    df: pd.DataFrame,
    event_date_col: str,
    reference_date: Optional[Union[str, datetime, pd.Timestamp]] = None,
    output_col: str = "days_since_event",
) -> pd.DataFrame:
    """
    Calculate the elapsed days between an event date and a reference date.

    Parameters:
        df: Input pandas DataFrame.
        event_date_col: Name of event date column.
        reference_date: Fixed reference date or max event date if None.
        output_col: Name of resulting numeric days column.

    Returns:
        DataFrame enriched with elapsed days column.
    """
    if event_date_col not in df.columns:
        raise KeyError(f"Event column '{event_date_col}' not found.")

    df_copy = df.copy()
    dt_series = pd.to_datetime(df_copy[event_date_col])

    if reference_date is None:
        ref_dt = dt_series.max()
    else:
        ref_dt = pd.to_datetime(reference_date)

    # Time delta arithmetic
    time_diff = ref_dt - dt_series
    df_copy[output_col] = (time_diff.dt.total_seconds() / (24 * 3600)).round(2)

    return df_copy


def calculate_duration_between_events(
    df: pd.DataFrame,
    start_date_col: str,
    end_date_col: str,
    unit: str = "days",
    output_col: str = "duration",
) -> pd.DataFrame:
    """
    Calculate duration between two timestamp columns.

    Parameters:
        df: Input pandas DataFrame.
        start_date_col: Column indicating start datetime.
        end_date_col: Column indicating end datetime.
        unit: Output unit ('days', 'hours', 'minutes', 'seconds').
        output_col: Target column name.

    Returns:
        DataFrame enriched with calculated duration.
    """
    for col in [start_date_col, end_date_col]:
        if col not in df.columns:
            raise KeyError(f"Required column '{col}' not found.")

    df_copy = df.copy()
    start_dt = pd.to_datetime(df_copy[start_date_col])
    end_dt = pd.to_datetime(df_copy[end_date_col])

    diff_seconds = (end_dt - start_dt).dt.total_seconds()

    unit_divisors = {
        "seconds": 1.0,
        "minutes": 60.0,
        "hours": 3600.0,
        "days": 86400.0,
    }

    if unit not in unit_divisors:
        raise ValueError(f"Unsupported unit '{unit}'. Allowed: {list(unit_divisors.keys())}")

    df_copy[output_col] = (diff_seconds / unit_divisors[unit]).round(2)
    return df_copy


def resample_time_series(
    df: pd.DataFrame,
    datetime_col: str,
    rule: str = "W",
    aggregations: Optional[Dict[str, Union[str, List[str]]]] = None,
) -> pd.DataFrame:
    """
    Resample a DataFrame along a datetime index using specified aggregation functions.

    Parameters:
        df: Input pandas DataFrame.
        datetime_col: Column containing timestamp to index on.
        rule: Resample offset string ('W' for weekly, 'ME' for month-end, 'QE' for quarter-end).
        aggregations: Mapping of column names to aggregation functions.

    Returns:
        Aggregated time-series DataFrame indexed by resampled periods.
    """
    if datetime_col not in df.columns:
        raise KeyError(f"Column '{datetime_col}' not found.")

    df_indexed = df.copy()
    df_indexed[datetime_col] = pd.to_datetime(df_indexed[datetime_col])
    df_indexed = df_indexed.dropna(subset=[datetime_col]).sort_values(datetime_col)
    df_indexed = df_indexed.set_index(datetime_col)

    if aggregations is None:
        # Default aggregation: count observations
        resampled = df_indexed.resample(rule).size().to_frame(name="record_count")
    else:
        resampled = df_indexed.resample(rule).agg(aggregations)
        # Flatten multi-level column names if needed
        if isinstance(resampled.columns, pd.MultiIndex):
            resampled.columns = [f"{col}_{agg}" for col, agg in resampled.columns]

    return resampled.reset_index()


def run_datetime_pipeline(
    input_path: Union[str, Path] = "data/raw/viewer_activity_sample.csv",
    output_data_path: Union[str, Path] = "data/processed/datetime_transformed_data.csv",
    output_report_path: Union[str, Path] = "output/datetime_transformation_report.json",
    reference_date: str = "2025-04-01",
) -> Dict[str, Any]:
    """
    Execute the end-to-end datetime transformation pipeline on raw data.

    Parameters:
        input_path: Path to raw input CSV.
        output_data_path: Path for transformed CSV dataset.
        output_report_path: Path for summary JSON report.
        reference_date: Reference anchor date for recency calculations.

    Returns:
        Dictionary containing pipeline transformation metrics.
    """
    input_file = Path(input_path)
    output_file = Path(output_data_path)
    report_file = Path(output_report_path)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Loading input dataset from %s", input_file)
    df = pd.read_csv(input_file)
    initial_rows, initial_cols = df.shape

    # 1. Parse Datetime columns
    df_parsed = parse_datetime_column(df, "session_timestamp")
    df_parsed = parse_datetime_column(df_parsed, "subscription_date")

    # 2. Extract Temporal Features
    df_features = extract_temporal_features(df_parsed, "session_timestamp", prefix="session")

    # 3. Calculate Days Since Event & Tenure Duration
    df_tenure = calculate_duration_between_events(
        df_features,
        start_date_col="subscription_date",
        end_date_col="session_timestamp",
        unit="days",
        output_col="tenure_days_at_session",
    )
    df_transformed = calculate_days_since_event(
        df_tenure,
        event_date_col="session_timestamp",
        reference_date=reference_date,
        output_col="days_since_session",
    )

    # 4. Resample Aggregations (Weekly and Monthly)
    weekly_summary = resample_time_series(
        df_transformed,
        datetime_col="session_timestamp",
        rule="W",
        aggregations={
            "viewer_id": "count",
            "watch_duration_mins": ["sum", "mean"],
        },
    )

    monthly_summary = resample_time_series(
        df_transformed,
        datetime_col="session_timestamp",
        rule="ME",
        aggregations={
            "viewer_id": "count",
            "watch_duration_mins": ["sum", "mean"],
        },
    )

    # Save Transformed Dataset
    df_transformed.to_csv(output_file, index=False)
    logger.info("Saved transformed dataset to %s (%d rows, %d cols)", output_file, len(df_transformed), len(df_transformed.columns))

    # Summary Report
    report = {
        "status": "SUCCESS",
        "timestamp": datetime.now().isoformat(),
        "input_file": str(input_file),
        "output_file": str(output_file),
        "initial_dimensions": {"rows": initial_rows, "columns": initial_cols},
        "transformed_dimensions": {"rows": len(df_transformed), "columns": len(df_transformed.columns)},
        "extracted_features": [
            "session_day_of_week",
            "session_day_of_week_num",
            "session_hour",
            "session_is_weekend",
            "session_iso_week",
            "session_month",
            "session_month_name",
            "session_quarter",
            "session_year",
            "tenure_days_at_session",
            "days_since_session",
        ],
        "time_series_aggregations": {
            "weekly_resample_records": len(weekly_summary),
            "monthly_resample_records": len(monthly_summary),
            "total_watch_mins": float(df_transformed["watch_duration_mins"].sum()),
            "avg_watch_mins_per_session": round(float(df_transformed["watch_duration_mins"].mean()), 2),
        },
        "day_of_week_distribution": df_transformed["session_day_of_week"].value_counts().to_dict(),
        "quarterly_distribution": df_transformed["session_quarter"].value_counts().to_dict(),
    }

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info("Saved datetime transformation report to %s", report_file)
    return report


if __name__ == "__main__":
    run_datetime_pipeline()
