"""Unit tests for Module 5 — NumPy Vectorised Computation."""

import json
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.numpy_vectorization import (
    benchmark_operation,
    compute_composite_score_loop,
    compute_composite_score_vectorized,
    integrate_vectorized_features,
    min_max_normalize_loop,
    min_max_normalize_vectorized,
    run_numpy_vectorization_pipeline,
    z_score_standardize_loop,
    z_score_standardize_vectorized,
)


class TestNumPyVectorization(unittest.TestCase):
    """Test suite for numerical equivalence, DataFrame integration, and benchmarking."""

    def setUp(self):
        """Set up test fixtures."""
        np.random.seed(123)
        self.test_array = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
        self.watch = np.array([30.0, 60.0, 90.0, 120.0])
        self.sessions = np.array([5.0, 10.0, 15.0, 20.0])
        self.dropoffs = np.array([1.0, 2.0, 3.0, 0.0])

        self.sample_df = pd.DataFrame(
            {
                "viewer_id": ["V1", "V2", "V3", "V4"],
                "watch_duration_mins": [30.0, 60.0, 90.0, 120.0],
                "session_count": [5, 10, 15, 20],
                "dropoff_count": [1, 2, 3, 0],
            }
        )

    def test_min_max_normalization_parity(self):
        """Verify loop and vectorized Min-Max produce numerically equivalent outputs."""
        loop_res = np.array(min_max_normalize_loop(self.test_array.tolist()))
        vec_res = min_max_normalize_vectorized(self.test_array)

        np.testing.assert_allclose(loop_res, vec_res, rtol=1e-6, atol=1e-6)
        self.assertEqual(vec_res.min(), 0.0)
        self.assertEqual(vec_res.max(), 1.0)

    def test_z_score_standardization_parity(self):
        """Verify loop and vectorized Z-Score produce numerically equivalent outputs."""
        loop_res = np.array(z_score_standardize_loop(self.test_array.tolist()))
        vec_res = z_score_standardize_vectorized(self.test_array)

        np.testing.assert_allclose(loop_res, vec_res, rtol=1e-6, atol=1e-6)
        self.assertAlmostEqual(vec_res.mean(), 0.0, places=6)
        self.assertAlmostEqual(vec_res.std(), 1.0, places=6)

    def test_composite_score_parity(self):
        """Verify composite score mathematical equivalence between loop and vectorized routines."""
        loop_res = np.array(compute_composite_score_loop(self.watch.tolist(), self.sessions.tolist(), self.dropoffs.tolist()))
        vec_res = compute_composite_score_vectorized(self.watch, self.sessions, self.dropoffs)

        np.testing.assert_allclose(loop_res, vec_res, rtol=1e-6, atol=1e-6)

    def test_dataframe_integration(self):
        """Verify that vectorized metrics integrate seamlessly as new DataFrame columns."""
        df_out = integrate_vectorized_features(self.sample_df)

        self.assertIn("watch_duration_minmax", df_out.columns)
        self.assertIn("watch_duration_zscore", df_out.columns)
        self.assertIn("vectorized_engagement_index", df_out.columns)

        # Min-max boundary check
        self.assertEqual(df_out["watch_duration_minmax"].min(), 0.0)
        self.assertEqual(df_out["watch_duration_minmax"].max(), 1.0)

    def test_benchmark_speedup(self):
        """Verify benchmark runs and demonstrates significant vectorized speedup."""
        bench = benchmark_operation(scale=5000, runs=3)
        self.assertIn("min_max_normalization", bench)
        self.assertIn("z_score_standardization", bench)
        self.assertIn("composite_nonlinear_computation", bench)

        # Vectorized time should be measurably faster
        vec_time = bench["composite_nonlinear_computation"]["vectorized_time_sec"]
        loop_time = bench["composite_nonlinear_computation"]["loop_time_sec"]
        self.assertLess(vec_time, loop_time)

    def test_end_to_end_pipeline(self):
        """Verify pipeline execution and artifact generation."""
        report = run_numpy_vectorization_pipeline(
            sample_size=500,
            benchmark_scales=(500, 2000),
            output_data_path="data/processed/vectorized_computations_data.csv",
            output_report_path="output/numpy_vectorization_benchmark.json",
        )
        self.assertEqual(report["status"], "SUCCESS")
        self.assertTrue(Path("data/processed/vectorized_computations_data.csv").exists())
        self.assertTrue(Path("output/numpy_vectorization_benchmark.json").exists())


if __name__ == "__main__":
    unittest.main()
