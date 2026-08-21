"""Unit and integration tests for Module 3 — Data Dictionary & Business Context Mapping."""

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
from data_dictionary import (
    DATA_DICTIONARY,
    export_data_dictionary_json,
    get_data_dictionary,
    get_fields_by_domain,
    validate_dataframe_schema,
)


class TestDataDictionary(unittest.TestCase):
    """Test suite for Data Dictionary and Business Context Mapping."""

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.test_dir.name)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_dictionary_completeness(self):
        dictionary = get_data_dictionary()
        self.assertGreaterEqual(len(dictionary), 15)

        for col, meta in dictionary.items():
            self.assertIn("domain", meta, f"Missing domain in {col}")
            self.assertIn("data_type", meta, f"Missing data_type in {col}")
            self.assertIn("meaning", meta, f"Missing meaning in {col}")
            self.assertIn("business_purpose", meta, f"Missing business_purpose in {col}")

    def test_domain_filtering(self):
        user_fields = get_fields_by_domain("User & Subscription")
        self.assertIn("viewer_id", user_fields)
        self.assertIn("subscription_plan", user_fields)

        viewing_fields = get_fields_by_domain("Viewing Consumption")
        self.assertIn("content_id", viewing_fields)
        self.assertIn("watch_duration_minutes", viewing_fields)

        engagement_fields = get_fields_by_domain("Engagement Dynamics")
        self.assertIn("completion_rate", engagement_fields)
        self.assertIn("pause_frequency", engagement_fields)

        retention_fields = get_fields_by_domain("Retention & Churn")
        self.assertIn("churn", retention_fields)
        self.assertIn("subscription_status", retention_fields)

    def test_validate_dataframe_schema(self):
        test_df = pd.DataFrame({
            "viewer_id": ["V1", "V2"],
            "subscription_plan": ["Basic", "Premium"],
            "churn": [0, 1],
            "custom_untracked_col": [10, 20],
        })

        validation = validate_dataframe_schema(test_df)
        self.assertEqual(validation["total_dataset_columns"], 4)
        self.assertEqual(validation["matched_columns_count"], 3)
        self.assertIn("custom_untracked_col", validation["unmatched_dataset_columns"])
        self.assertIn("User & Subscription", validation["domain_coverage"])

    def test_export_data_dictionary_json(self):
        output_file = self.temp_path / "exported_dict.json"
        saved_path = export_data_dictionary_json(output_file)

        self.assertTrue(saved_path.exists())
        with open(saved_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("viewer_id", data)
        self.assertIn("churn", data)


if __name__ == "__main__":
    unittest.main()
