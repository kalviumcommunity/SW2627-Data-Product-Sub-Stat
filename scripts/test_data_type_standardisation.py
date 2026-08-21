"""Unit and integration tests for Module 5 — Data Type Enforcement & Standardisation."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

# Add scripts directory to sys.path
scripts_dir = Path(__file__).resolve().parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

import pandas as pd
from data_type_standardisation import (
    enforce_dataset_schema,
    standardise_boolean,
    standardise_datetime,
    standardise_numeric,
    standardise_string,
)


class TestDataTypeStandardisation(unittest.TestCase):
    """Test suite for explicit data type enforcement and standardisation."""

    def test_standardise_datetime_explicit(self):
        series = pd.Series(["2025-01-15", "2025-02-20", "invalid-date"])
        converted, audit = standardise_datetime(series, date_format="%Y-%m-%d")

        self.assertEqual(audit["successful_conversions"], 2)
        self.assertEqual(audit["failed_conversions"], 1)
        self.assertEqual(len(audit["sample_failures"]), 1)
        self.assertEqual(audit["sample_failures"][0]["raw_value"], "invalid-date")
        self.assertTrue(pd.isna(converted.iloc[2]))
        self.assertEqual(converted.iloc[0].year, 2025)

    def test_standardise_numeric_currency(self):
        series = pd.Series(["$1,250.50", " $15.99 ", "20.00 USD", "invalid"])
        converted, audit = standardise_numeric(series, target_type="float", is_currency=True)

        self.assertEqual(audit["successful_conversions"], 3)
        self.assertEqual(audit["failed_conversions"], 1)
        self.assertEqual(converted.iloc[0], 1250.50)
        self.assertEqual(converted.iloc[1], 15.99)
        self.assertEqual(converted.iloc[2], 20.00)

    def test_standardise_boolean(self):
        series = pd.Series([1, 0, "true", "False", "yes", "no", "invalid"])
        converted, audit = standardise_boolean(series)

        self.assertEqual(audit["successful_conversions"], 6)
        self.assertEqual(audit["failed_conversions"], 1)
        self.assertEqual(converted.iloc[0], True)
        self.assertEqual(converted.iloc[1], False)
        self.assertEqual(converted.iloc[2], True)
        self.assertEqual(converted.iloc[3], False)
        self.assertEqual(converted.iloc[4], True)
        self.assertEqual(converted.iloc[5], False)

    def test_standardise_string_casing(self):
        series = pd.Series(["  john doe  ", "ALICE SMITH", "standard"])
        converted, audit = standardise_string(series, case="title")

        self.assertEqual(converted.iloc[0], "John Doe")
        self.assertEqual(converted.iloc[1], "Alice Smith")
        self.assertEqual(converted.iloc[2], "Standard")

    def test_enforce_dataset_schema(self):
        df = pd.DataFrame({
            "date": ["2025-01-01", "2025-01-02"],
            "fee": ["$10.00", "$20.00"],
            "active": ["1", "0"],
            "tier": ["basic", "PREMIUM"],
        })

        rules = {
            "date": {"type": "datetime", "format": "%Y-%m-%d"},
            "fee": {"type": "currency"},
            "active": {"type": "boolean"},
            "tier": {"type": "string", "case": "title"},
        }

        std_df, report = enforce_dataset_schema(df, rules)
        self.assertEqual(len(report["column_audits"]), 4)
        self.assertEqual(std_df["fee"].dtype, float)
        self.assertEqual(std_df["active"].dtype, "boolean")
        self.assertEqual(std_df["tier"].tolist(), ["Basic", "Premium"])


if __name__ == "__main__":
    unittest.main()
