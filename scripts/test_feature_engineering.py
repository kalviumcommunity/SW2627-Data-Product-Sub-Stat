"""Unit tests for Module 4 — Feature Engineering & Derived Business Columns."""

import json
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.feature_engineering import (
    calculate_rfm_composite_scores,
    create_binned_features,
    create_ratio_features,
    run_feature_engineering_pipeline,
    safe_divide,
    validate_feature_distributions,
)


class TestFeatureEngineering(unittest.TestCase):
    """Test suite for ratio creation, binning, RFM scoring, and distribution validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_df = pd.DataFrame(
            {
                "viewer_id": ["V1", "V2", "V3", "V4", "V5"],
                "tenure_months": [12, 6, 0, 24, 3],  # V3 has 0 tenure (tests division by zero)
                "total_transactions": [24, 12, 0, 48, 6],
                "total_spend": [240.0, 180.0, 0.0, 600.0, 75.0],
                "completed_episodes": [45, 30, 0, 120, 15],
                "total_episodes_started": [50, 35, 0, 130, 20],  # V3 has 0 started
                "total_watch_hours": [120.0, 80.0, 2.0, 310.0, 35.0],
                "active_days": [60, 40, 1, 180, 18],
                "days_since_last_active": [3, 7, 45, 1, 12],
            }
        )

    def test_safe_divide(self):
        """Verify division handles zeros, NaNs, and infinities without raising exceptions."""
        num = pd.Series([10.0, 0.0, 50.0, np.nan])
        den = pd.Series([2.0, 0.0, 0.0, 5.0])
        result = safe_divide(num, den, fill_value=0.0)

        self.assertEqual(result.iloc[0], 5.0)
        self.assertEqual(result.iloc[1], 0.0)
        self.assertEqual(result.iloc[2], 0.0)  # 50 / 0 -> 0.0
        self.assertEqual(result.iloc[3], 0.0)  # NaN / 5 -> 0.0
        self.assertFalse(np.isinf(result).any())
        self.assertFalse(result.isna().any())

    def test_create_ratio_features(self):
        """Verify calculation of business ratio features."""
        df_ratios = create_ratio_features(self.sample_df)

        self.assertIn("transactions_per_month", df_ratios.columns)
        self.assertIn("avg_spend_per_transaction", df_ratios.columns)
        self.assertIn("completion_rate", df_ratios.columns)
        self.assertIn("watch_hours_per_active_day", df_ratios.columns)

        # Row 0: 24 / 12 = 2.0
        self.assertEqual(df_ratios["transactions_per_month"].iloc[0], 2.0)
        # Row 0: 240 / 24 = 10.0
        self.assertEqual(df_ratios["avg_spend_per_transaction"].iloc[0], 10.0)
        # Row 2 (zero denominator safe division): 0.0
        self.assertEqual(df_ratios["transactions_per_month"].iloc[2], 0.0)

    def test_create_binned_features(self):
        """Verify pd.cut domain tiers and pd.qcut quantile binning."""
        df_binned = create_binned_features(self.sample_df)

        self.assertIn("spend_tier", df_binned.columns)
        self.assertIn("engagement_quantile", df_binned.columns)

        # Check domain spend tier values
        self.assertIn(df_binned["spend_tier"].iloc[0], ["Medium", "High", "VIP", "Low"])
        # Spend 600.0 should be VIP
        self.assertEqual(df_binned["spend_tier"].iloc[3], "VIP")
        # Spend 0.0 should be Low
        self.assertEqual(df_binned["spend_tier"].iloc[2], "Low")

    def test_calculate_rfm_composite_scores(self):
        """Verify composite RFM calculations and customer segmentation."""
        df_rfm = calculate_rfm_composite_scores(self.sample_df)

        self.assertIn("r_score", df_rfm.columns)
        self.assertIn("f_score", df_rfm.columns)
        self.assertIn("m_score", df_rfm.columns)
        self.assertIn("rfm_composite_score", df_rfm.columns)
        self.assertIn("rfm_segment", df_rfm.columns)

        # Composite score must be within [20, 100]
        self.assertTrue((df_rfm["rfm_composite_score"] >= 20).all())
        self.assertTrue((df_rfm["rfm_composite_score"] <= 100).all())

    def test_validate_feature_distributions(self):
        """Verify statistical validation metrics and absence of NaN/Inf."""
        df_ratios = create_ratio_features(self.sample_df)
        dist_report = validate_feature_distributions(df_ratios, ["transactions_per_month", "avg_spend_per_transaction"])

        self.assertIn("transactions_per_month", dist_report)
        self.assertTrue(dist_report["transactions_per_month"]["is_valid"])
        self.assertEqual(dist_report["transactions_per_month"]["null_count"], 0)
        self.assertEqual(dist_report["transactions_per_month"]["inf_count"], 0)

    def test_end_to_end_pipeline(self):
        """Verify pipeline execution and exported artifacts."""
        report = run_feature_engineering_pipeline(
            input_path="data/raw/viewer_engagement_features.csv",
            output_data_path="data/processed/feature_engineered_data.csv",
            output_report_path="output/feature_engineering_report.json",
        )
        self.assertEqual(report["status"], "SUCCESS")
        self.assertTrue(Path("data/processed/feature_engineered_data.csv").exists())
        self.assertTrue(Path("output/feature_engineering_report.json").exists())


if __name__ == "__main__":
    unittest.main()
