"""Unit and integration tests for Module 2 — Dataset Profiling & Quality Assessment."""

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
from dataset_profiling import (
    assess_data_quality,
    generate_dataset_profile,
    profile_categorical_distributions,
    profile_duplicates,
    profile_missing_values,
    profile_numerical_distributions,
    profile_shape_and_memory,
)


class TestDatasetProfiling(unittest.TestCase):
    """Test suite for dataset profiling and quality assessment."""

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.test_dir.name)

        # Sample DataFrame for testing
        self.df = pd.DataFrame({
            "id": [1, 2, 3, 4, 5, 5],  # Contains 1 duplicate id
            "category": ["Tech", "Finance", "Tech", "Health", None, "Tech"],
            "revenue": [100.0, 250.0, 150.0, 500.0, 300.0, 300.0],
            "churn": [0, 1, 0, 0, 1, 1],
        })

    def tearDown(self):
        self.test_dir.cleanup()

    def test_profile_shape_and_memory(self):
        shape_info = profile_shape_and_memory(self.df)
        self.assertEqual(shape_info["total_rows"], 6)
        self.assertEqual(shape_info["total_columns"], 4)
        self.assertIn("revenue", shape_info["columns"])
        self.assertGreater(shape_info["memory_bytes"], 0)

    def test_profile_missing_values(self):
        missing_info = profile_missing_values(self.df)
        self.assertEqual(missing_info["total_missing_cells"], 1)
        self.assertEqual(missing_info["columns"]["category"]["null_count"], 1)
        self.assertAlmostEqual(missing_info["columns"]["category"]["null_percentage"], 16.67, places=1)
        self.assertTrue(missing_info["columns"]["revenue"]["is_complete"])

    def test_profile_duplicates(self):
        # Row 4 and Row 5 are not exact duplicates because category differs (None vs 'Tech')
        # Let's test with an exact duplicate added
        df_with_exact = pd.concat([self.df, self.df.iloc[[0]]], ignore_index=True)
        dup_info = profile_duplicates(df_with_exact, primary_key="id")

        self.assertEqual(dup_info["exact_duplicate_rows"], 1)
        self.assertFalse(dup_info["is_unique"])
        self.assertFalse(dup_info["primary_key_unique"])

    def test_profile_numerical_distributions(self):
        dist_info = profile_numerical_distributions(self.df)
        self.assertIn("revenue", dist_info)
        rev_stats = dist_info["revenue"]
        self.assertEqual(rev_stats["min"], 100.0)
        self.assertEqual(rev_stats["max"], 500.0)
        self.assertIn("iqr", rev_stats)
        self.assertIn("outlier_count", rev_stats)

    def test_profile_categorical_distributions(self):
        cat_info = profile_categorical_distributions(self.df)
        self.assertIn("category", cat_info)
        self.assertEqual(cat_info["category"]["top_values"]["Tech"], 3)
        self.assertEqual(cat_info["category"]["unique_values"], 3)

    def test_assess_data_quality(self):
        quality = assess_data_quality(self.df)
        self.assertGreaterEqual(quality["overall_quality_score"], 0)
        self.assertLessEqual(quality["overall_quality_score"], 100)
        self.assertIn(quality["quality_status"], ["EXCELLENT", "GOOD", "NEEDS_ATTENTION"])

    def test_generate_dataset_profile_file_export(self):
        report_file = self.temp_path / "test_profiling_report.json"
        report = generate_dataset_profile(
            df=self.df,
            dataset_name="test_data",
            primary_key="id",
            report_path=report_file,
        )

        self.assertTrue(report_file.exists())
        with open(report_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        self.assertEqual(saved_data["dataset_name"], "test_data")
        self.assertIn("shape_and_memory", saved_data)
        self.assertIn("completeness", saved_data)
        self.assertIn("uniqueness", saved_data)
        self.assertIn("numerical_distributions", saved_data)
        self.assertIn("quality_assessment", saved_data)


if __name__ == "__main__":
    unittest.main()
