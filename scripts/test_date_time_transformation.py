"""Unit tests for Module 1 — Date & Time Transformation Pipeline."""

import json
import unittest
from pathlib import Path

import pandas as pd

from scripts.date_time_transformation import (
    calculate_days_since_event,
    calculate_duration_between_events,
    extract_temporal_features,
    parse_datetime_column,
    resample_time_series,
    run_datetime_pipeline,
)


class TestDateTimeTransformation(unittest.TestCase):
    """Test suite for datetime parsing, extraction, arithmetic, and resampling."""

    def setUp(self):
        """Create sample DataFrame for testing."""
        self.sample_df = pd.DataFrame(
            {
                "event_id": [1, 2, 3, 4],
                "event_timestamp": [
                    "2025-01-15 08:30:00",  # Wednesday
                    "2025-01-18 14:45:00",  # Saturday
                    "2025-01-19 22:15:30",  # Sunday
                    "2025-02-01 10:00:00",  # Saturday
                ],
                "start_date": ["2025-01-01", "2025-01-10", "2025-01-10", "2025-01-15"],
                "metric_val": [100.0, 150.0, 200.0, 50.0],
            }
        )

    def test_parse_datetime_column(self):
        """Verify strings are accurately converted to datetime dtypes."""
        parsed_df = parse_datetime_column(self.sample_df, "event_timestamp")
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(parsed_df["event_timestamp"]))
        self.assertEqual(parsed_df["event_timestamp"].iloc[0].year, 2025)
        self.assertEqual(parsed_df["event_timestamp"].iloc[0].month, 1)
        self.assertEqual(parsed_df["event_timestamp"].iloc[0].day, 15)

    def test_extract_temporal_features(self):
        """Verify extraction of day_of_week, numeric day, hour, iso_week, month, quarter, weekend."""
        parsed_df = parse_datetime_column(self.sample_df, "event_timestamp")
        enriched_df = extract_temporal_features(parsed_df, "event_timestamp", prefix="ts")

        # Check column existence
        expected_cols = [
            "ts_day_of_week",
            "ts_day_of_week_num",
            "ts_hour",
            "ts_is_weekend",
            "ts_iso_week",
            "ts_month",
            "ts_month_name",
            "ts_quarter",
            "ts_year",
        ]
        for col in expected_cols:
            self.assertIn(col, enriched_df.columns)

        # Wednesday 2025-01-15 08:30:00
        self.assertEqual(enriched_df["ts_day_of_week"].iloc[0], "Wednesday")
        self.assertEqual(enriched_df["ts_day_of_week_num"].iloc[0], 2)
        self.assertEqual(enriched_df["ts_hour"].iloc[0], 8)
        self.assertEqual(enriched_df["ts_is_weekend"].iloc[0], 0)
        self.assertEqual(enriched_df["ts_month"].iloc[0], 1)
        self.assertEqual(enriched_df["ts_quarter"].iloc[0], 1)

        # Saturday 2025-01-18 14:45:00
        self.assertEqual(enriched_df["ts_day_of_week"].iloc[1], "Saturday")
        self.assertEqual(enriched_df["ts_day_of_week_num"].iloc[1], 5)
        self.assertEqual(enriched_df["ts_is_weekend"].iloc[1], 1)

    def test_calculate_days_since_event(self):
        """Verify datetime subtraction relative to reference date."""
        df_parsed = parse_datetime_column(self.sample_df, "event_timestamp")
        df_recency = calculate_days_since_event(
            df_parsed,
            event_date_col="event_timestamp",
            reference_date="2025-01-20 00:00:00",
            output_col="days_since",
        )
        self.assertIn("days_since", df_recency.columns)
        # Event at 2025-01-15 08:30:00 relative to 2025-01-20 00:00:00 -> 4.65 days
        self.assertAlmostEqual(df_recency["days_since"].iloc[0], 4.65, places=1)

    def test_calculate_duration_between_events(self):
        """Verify duration between two timestamp columns."""
        df_parsed = parse_datetime_column(self.sample_df, "event_timestamp")
        df_parsed = parse_datetime_column(df_parsed, "start_date")
        df_duration = calculate_duration_between_events(
            df_parsed,
            start_date_col="start_date",
            end_date_col="event_timestamp",
            unit="days",
            output_col="tenure_days",
        )
        self.assertIn("tenure_days", df_duration.columns)
        # 2025-01-15 08:30:00 minus 2025-01-01 00:00:00 -> 14.35 days
        self.assertAlmostEqual(df_duration["tenure_days"].iloc[0], 14.35, places=1)

    def test_resample_time_series(self):
        """Verify weekly resampling and aggregation."""
        df_parsed = parse_datetime_column(self.sample_df, "event_timestamp")
        resampled = resample_time_series(
            df_parsed,
            datetime_col="event_timestamp",
            rule="W",
            aggregations={"metric_val": ["sum", "count"]},
        )
        self.assertTrue(len(resampled) > 0)
        self.assertIn("metric_val_sum", resampled.columns)
        self.assertIn("metric_val_count", resampled.columns)

    def test_end_to_end_pipeline(self):
        """Verify pipeline execution and output artifact generation."""
        report = run_datetime_pipeline(
            input_path="data/raw/viewer_activity_sample.csv",
            output_data_path="data/processed/datetime_transformed_data.csv",
            output_report_path="output/datetime_transformation_report.json",
            reference_date="2025-04-01",
        )
        self.assertEqual(report["status"], "SUCCESS")
        self.assertTrue(Path("data/processed/datetime_transformed_data.csv").exists())
        self.assertTrue(Path("output/datetime_transformation_report.json").exists())


if __name__ == "__main__":
    unittest.main()
