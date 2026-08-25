"""Unit tests for Module 2 — Data Consistency & Validation Rules."""

import json
import unittest
from pathlib import Path

import pandas as pd

from scripts.data_validation import (
    DataValidator,
    build_default_validator,
    check_date_order,
    check_range,
    check_referential_integrity,
    check_regex_format,
    check_required_fields,
    run_validation_pipeline,
)


class TestDataValidation(unittest.TestCase):
    """Test suite for range, null, format, referential integrity, and business rule validations."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_df = pd.DataFrame(
            {
                "record_id": [1, 2, 3, 4],
                "viewer_id": ["V101", "V102", "INVALID", ""],
                "content_id": ["C101", "C102", "C999", "C101"],
                "watch_duration_mins": [45.0, 120.0, -5.0, 700.0],
                "start_time": ["2025-01-10 10:00:00", "2025-01-10 11:00:00", "2025-01-10 12:00:00", "2025-01-10 13:00:00"],
                "end_time": ["2025-01-10 10:45:00", "2025-01-10 11:30:00", "2025-01-10 11:00:00", "2025-01-10 13:50:00"],
                "user_email": ["user@test.com", "valid.email@stream.org", "bad-email", "user4@test.com"],
                "user_rating": [4.5, 5.0, 0.5, 3.0],
            }
        )

    def test_check_range(self):
        """Verify numeric range boundary assertions."""
        result = check_range(self.test_df, "watch_duration_mins", min_val=0.0, max_val=600.0)
        self.assertTrue(result.iloc[0])  # 45.0
        self.assertTrue(result.iloc[1])  # 120.0
        self.assertFalse(result.iloc[2])  # -5.0 (below min)
        self.assertFalse(result.iloc[3])  # 700.0 (above max)

    def test_check_required_fields(self):
        """Verify null and empty string detection."""
        result = check_required_fields(self.test_df, ["viewer_id", "content_id"])
        self.assertTrue(result.iloc[0])
        self.assertTrue(result.iloc[1])
        self.assertTrue(result.iloc[2])
        self.assertFalse(result.iloc[3])  # Empty string viewer_id

    def test_check_regex_format(self):
        """Verify regex pattern matching for IDs and emails."""
        id_result = check_regex_format(self.test_df, "viewer_id", r"^V\d{3,}$")
        self.assertTrue(id_result.iloc[0])  # V101
        self.assertTrue(id_result.iloc[1])  # V102
        self.assertFalse(id_result.iloc[2])  # INVALID
        self.assertFalse(id_result.iloc[3])  # Empty

        email_result = check_regex_format(self.test_df, "user_email", r"^[\w\.-]+@[\w\.-]+\.\w+$")
        self.assertTrue(email_result.iloc[0])
        self.assertTrue(email_result.iloc[1])
        self.assertFalse(email_result.iloc[2])  # bad-email
        self.assertTrue(email_result.iloc[3])

    def test_check_referential_integrity(self):
        """Verify orphan key detection against master reference list."""
        valid_content = {"C101", "C102", "C103"}
        result = check_referential_integrity(self.test_df, "content_id", valid_content)
        self.assertTrue(result.iloc[0])  # C101
        self.assertTrue(result.iloc[1])  # C102
        self.assertFalse(result.iloc[2])  # C999 (orphan key)
        self.assertTrue(result.iloc[3])  # C101

    def test_check_date_order(self):
        """Verify business rule end_time >= start_time."""
        result = check_date_order(self.test_df, start_col="start_time", end_col="end_time")
        self.assertTrue(result.iloc[0])  # 10:45 >= 10:00
        self.assertTrue(result.iloc[1])  # 11:30 >= 11:00
        self.assertFalse(result.iloc[2])  # 11:00 < 12:00 (Invalid chronological order)
        self.assertTrue(result.iloc[3])  # 13:50 >= 13:00

    def test_data_validator_engine(self):
        """Verify combined multi-rule evaluation and failure classification."""
        validator = build_default_validator(content_catalog_path="data/raw/content_catalog.csv")
        passed_df, failed_df, report = validator.validate(self.test_df)

        self.assertEqual(report["total_records"], 4)
        self.assertEqual(report["passed_records"], 2)  # Rows 1 and 2 pass all rules
        self.assertEqual(report["failed_records"], 2)  # Rows 3 and 4 fail at least one rule
        self.assertIn("_failed_rules", failed_df.columns)
        self.assertIn("_failure_reasons", failed_df.columns)

    def test_end_to_end_pipeline(self):
        """Verify pipeline execution and exported artifacts."""
        report = run_validation_pipeline(
            input_path="data/raw/validation_sample.csv",
            catalog_path="data/raw/content_catalog.csv",
            failed_output_path="data/processed/failed_validation_records.csv",
            passed_output_path="data/processed/clean_validated_records.csv",
            report_output_path="output/data_validation_report.json",
        )
        self.assertEqual(report["status"], "SUCCESS")
        self.assertEqual(report["total_records"], 10)
        self.assertTrue(Path("data/processed/failed_validation_records.csv").exists())
        self.assertTrue(Path("output/data_validation_report.json").exists())


if __name__ == "__main__":
    unittest.main()
