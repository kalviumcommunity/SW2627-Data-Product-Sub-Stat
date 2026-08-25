"""Unit tests for Module 3 — Multi-Source Merging & Join Validation."""

import json
import unittest
from pathlib import Path

import pandas as pd

from scripts.join_validation import (
    assess_cardinality,
    perform_validated_merge,
    run_join_pipeline,
)


class TestJoinValidation(unittest.TestCase):
    """Test suite for join key validation, cardinality assessment, and unmatched record isolation."""

    def setUp(self):
        """Set up test fixtures."""
        self.left_df = pd.DataFrame(
            {
                "viewer_id": ["V101", "V102", "V103", "V104"],
                "name": ["Alice", "Bob", "Charlie", "Diana"],
                "tier": ["Premium", "Standard", "Basic", "Premium"],
            }
        )
        self.right_df = pd.DataFrame(
            {
                "event_id": [1, 2, 3, 4],
                "viewer_id": ["V101", "V101", "V102", "V999"],  # V101 repeated (1:N), V999 orphan
                "amount": [19.99, 19.99, 14.99, 29.99],
            }
        )

    def test_assess_cardinality(self):
        """Verify cardinality classification."""
        # 1:N cardinality (viewer_id unique in left, repeated in right)
        card = assess_cardinality(self.left_df, self.right_df, "viewer_id", "viewer_id")
        self.assertEqual(card, "one_to_many")

        # 1:1 cardinality
        unique_right = self.right_df.drop_duplicates(subset=["viewer_id"])
        self.assertEqual(assess_cardinality(self.left_df, unique_right, "viewer_id", "viewer_id"), "one_to_one")

    def test_left_join_unmatched_isolation(self):
        """Verify left join produces expected rows and detects unmatched keys on both sides."""
        merged_df, unmatched_left, unmatched_right, report = perform_validated_merge(
            left_df=self.left_df,
            right_df=self.right_df,
            how="left",
            on="viewer_id",
        )

        # V103 and V104 have no events in right_df -> unmatched_left
        self.assertEqual(len(unmatched_left), 2)
        self.assertIn("V103", unmatched_left["viewer_id"].values)
        self.assertIn("V104", unmatched_left["viewer_id"].values)

        # V999 exists only in right_df -> unmatched_right
        self.assertEqual(len(unmatched_right), 1)
        self.assertIn("V999", unmatched_right["viewer_id"].values)

        # In a left join, Alice (V101) has 2 rows, Bob (V102) has 1 row, Charlie (V103) has 1 row, Diana (V104) has 1 row -> 5 rows total
        self.assertEqual(len(merged_df), 5)
        self.assertEqual(report["row_counts"]["unmatched_left_rows"], 2)
        self.assertEqual(report["row_counts"]["unmatched_right_rows"], 1)

    def test_inner_join(self):
        """Verify inner join keeps only intersecting records."""
        merged_df, unmatched_left, unmatched_right, report = perform_validated_merge(
            left_df=self.left_df,
            right_df=self.right_df,
            how="inner",
            on="viewer_id",
        )
        # Intersecting: V101 (2 rows) + V102 (1 row) = 3 rows
        self.assertEqual(len(merged_df), 3)
        self.assertNotIn("V103", merged_df["viewer_id"].values)
        self.assertNotIn("V999", merged_df["viewer_id"].values)

    def test_missing_join_key(self):
        """Verify exception when join key does not exist."""
        with self.assertRaises(KeyError):
            perform_validated_merge(
                left_df=self.left_df,
                right_df=self.right_df,
                how="left",
                on="non_existent_key",
            )

    def test_end_to_end_pipeline(self):
        """Verify pipeline execution with output artifacts."""
        report = run_join_pipeline(
            left_path="data/raw/viewers_master.csv",
            right_path="data/raw/subscription_events.csv",
            join_key="viewer_id",
            join_type="left",
            output_merged_path="data/processed/merged_dataset.csv",
            unmatched_left_path="output/unmatched_left_records.csv",
            unmatched_right_path="output/unmatched_right_records.csv",
            report_path="output/join_validation_report.json",
        )
        self.assertEqual(report["status"], "SUCCESS")
        self.assertTrue(Path("data/processed/merged_dataset.csv").exists())
        self.assertTrue(Path("output/unmatched_left_records.csv").exists())
        self.assertTrue(Path("output/unmatched_right_records.csv").exists())
        self.assertTrue(Path("output/join_validation_report.json").exists())


if __name__ == "__main__":
    unittest.main()
