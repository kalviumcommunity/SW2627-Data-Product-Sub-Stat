"""Unit and integration tests for Module 4 — Missing Value Detection & Imputation."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

# Add scripts directory to sys.path
scripts_dir = Path(__file__).resolve().parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

import numpy as np
import pandas as pd
from missing_value_handling import (
    detect_missing_values,
    generate_imputation_report,
    handle_missing_values,
)


class TestMissingValueHandling(unittest.TestCase):
    """Test suite for missing value detection and imputation strategies."""

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.test_dir.name)

        # Create test DataFrame with mixed nulls
        self.df = pd.DataFrame({
            "viewer_id": ["V1", "V2", None, "V4", "V5"],
            "plan": ["Basic", "Standard", "Standard", None, "Premium"],
            "duration": [10.0, 20.0, 30.0, None, 50.0],
            "date": ["2025-01-01", None, "2025-01-03", "2025-01-04", None],
        })

    def tearDown(self):
        self.test_dir.cleanup()

    def test_detect_missing_values(self):
        stats = detect_missing_values(self.df)
        self.assertEqual(stats["total_rows"], 5)
        self.assertEqual(stats["total_columns"], 4)
        self.assertEqual(stats["total_missing_cells"], 5)
        self.assertEqual(stats["columns"]["viewer_id"]["null_count"], 1)
        self.assertEqual(stats["columns"]["duration"]["null_count"], 1)

    def test_critical_identifier_dropping(self):
        cleaned, log = handle_missing_values(
            df=self.df,
            critical_identifiers=["viewer_id"],
        )
        self.assertEqual(len(cleaned), 4)
        self.assertFalse(cleaned["viewer_id"].isna().any())
        self.assertEqual(log[0]["strategy"], "drop_rows")

    def test_numerical_median_imputation(self):
        cleaned, log = handle_missing_values(
            df=self.df,
            critical_identifiers=["viewer_id"],
            numerical_median_cols=["duration"],
        )
        # Remaining valid rows: 10, 20, None, 50 -> median of (10, 20, 50) is 20.0
        self.assertFalse(cleaned["duration"].isna().any())
        self.assertEqual(cleaned.loc[cleaned["viewer_id"] == "V4", "duration"].values[0], 20.0)

    def test_categorical_mode_imputation(self):
        cleaned, log = handle_missing_values(
            df=self.df,
            critical_identifiers=["viewer_id"],
            categorical_mode_cols=["plan"],
        )
        # Valid plans: Basic, Standard, None, Premium -> mode is Standard/Basic/Premium
        self.assertFalse(cleaned["plan"].isna().any())

    def test_time_series_forward_fill(self):
        cleaned, log = handle_missing_values(
            df=self.df,
            critical_identifiers=["viewer_id"],
            time_series_cols=["date"],
            date_sort_col="date",
        )
        self.assertFalse(cleaned["date"].isna().any())

    def test_generate_imputation_report(self):
        cleaned, log = handle_missing_values(
            df=self.df,
            critical_identifiers=["viewer_id"],
            numerical_median_cols=["duration"],
            categorical_mode_cols=["plan"],
            time_series_cols=["date"],
        )

        report_file = self.temp_path / "test_missing_report.json"
        report = generate_imputation_report(
            df_before=self.df,
            df_after=cleaned,
            treatment_log=log,
            report_path=report_file,
        )

        self.assertEqual(report["summary"]["rows_before"], 5)
        self.assertEqual(report["summary"]["rows_after"], 4)
        self.assertEqual(report["summary"]["missing_cells_after"], 0)
        self.assertEqual(report["summary"]["completeness_after_pct"], 100.0)
        self.assertTrue(report_file.exists())


if __name__ == "__main__":
    unittest.main()
