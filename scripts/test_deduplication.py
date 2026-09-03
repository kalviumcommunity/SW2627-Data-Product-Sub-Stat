"""Unit and integration tests for Module 6 — Duplicate Detection & Record Deduplication."""

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
from deduplication import (
    deduplicate_dataset,
    detect_exact_duplicates,
    detect_near_duplicates,
    generate_deduplication_report,
)


class TestDeduplication(unittest.TestCase):
    """Test suite for duplicate detection and deduplication strategies."""

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.test_dir.name)

        # Create test DataFrame with exact and near duplicates
        self.df = pd.DataFrame({
            "viewer_id": ["V1", "V1", "V2", "V2", "V3"],
            "date": ["2025-01-01", "2025-01-01", "2025-01-02", "2025-01-02", "2025-01-03"],
            "score": [10.0, 10.0, None, 25.0, 30.0],  # V1 is exact dup, V2 is near dup (one has null)
            "status": ["Active", "Active", "Active", "Active", "Active"],
        })

    def tearDown(self):
        self.test_dir.cleanup()

    def test_detect_exact_duplicates(self):
        stats = detect_exact_duplicates(self.df)
        self.assertEqual(stats["exact_duplicate_rows"], 1)
        self.assertTrue(stats["has_exact_duplicates"])
        self.assertEqual(stats["total_rows_involved"], 2)

    def test_detect_near_duplicates(self):
        stats = detect_near_duplicates(self.df, business_keys=["viewer_id", "date"])
        self.assertEqual(stats["key_duplicate_rows"], 2)
        self.assertTrue(stats["has_near_duplicates"])

    def test_deduplicate_most_complete(self):
        deduped, removed, metrics = deduplicate_dataset(
            self.df,
            strategy="most_complete",
            business_keys=["viewer_id", "date"],
        )

        self.assertEqual(len(deduped), 3)
        self.assertEqual(len(removed), 2)
        self.assertEqual(metrics["records_removed"], 2)

        # For V2, the row with score 25.0 should be kept, and score None should be removed
        v2_row = deduped[deduped["viewer_id"] == "V2"].iloc[0]
        self.assertEqual(v2_row["score"], 25.0)

    def test_deduplicate_first_and_last(self):
        deduped_first, _, _ = deduplicate_dataset(
            self.df,
            strategy="first",
            business_keys=["viewer_id", "date"],
        )
        self.assertEqual(len(deduped_first), 3)

        deduped_last, _, _ = deduplicate_dataset(
            self.df,
            strategy="last",
            business_keys=["viewer_id", "date"],
        )
        self.assertEqual(len(deduped_last), 3)

    def test_generate_deduplication_report(self):
        deduped, removed, metrics = deduplicate_dataset(
            self.df,
            strategy="most_complete",
            business_keys=["viewer_id", "date"],
        )
        exact_stats = detect_exact_duplicates(self.df)
        report_file = self.temp_path / "test_dedup_report.json"

        report = generate_deduplication_report(
            metrics=metrics,
            exact_stats=exact_stats,
            report_path=report_file,
        )

        self.assertTrue(report_file.exists())
        self.assertEqual(report["deduplication_summary"]["rows_after"], 3)
        self.assertIn("strategy_rationale", report)


if __name__ == "__main__":
    unittest.main()
