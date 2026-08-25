"""Unit tests for Module 5 — SQL-Based Insight Validation."""

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

from scripts.sql_python_validation import MetricValidationResult, SQLPythonValidator


class TestSQLPythonValidation(unittest.TestCase):
    """Test suite for cross-engine metric validation, tolerance thresholds, and discrepancy diagnosis."""

    def setUp(self):
        """Set up in-memory database and validator instance pointing to project raw data."""
        self.engine = create_engine("sqlite:///:memory:")
        self.raw_data_dir = Path(__file__).resolve().parent.parent / "data" / "raw"
        self.validator = SQLPythonValidator(
            engine=self.engine,
            data_dir=self.raw_data_dir,
            abs_tolerance=1e-4,
            rel_tolerance=1e-4,
        )

    def test_built_in_metrics_pass_validation(self):
        """Verify all project metrics match between SQL and Python within tolerance."""
        results = self.validator.validate_metrics()
        self.assertGreaterEqual(len(results), 5)
        for r in results:
            self.assertEqual(r.status, "PASS", f"Metric {r.metric_name} failed: SQL={r.sql_value}, Py={r.python_value}")
            self.assertLessEqual(r.abs_difference, 1e-4)

    def test_tolerance_threshold_behavior(self):
        """Verify strict vs loose tolerance correctly controls PASS/FAIL status."""
        # Intentionally register divergent metric
        self.validator.register_metric(
            name="test_divergent_metric",
            sql_calculation=lambda eng: 100.05,
            python_calculation=lambda path: 100.00,
        )

        # Under strict tolerance (0.01), it should FAIL
        strict_results = self.validator.validate_metrics(abs_tol=0.01, rel_tol=0.0001)
        divergent_strict = next(r for r in strict_results if r.metric_name == "test_divergent_metric")
        self.assertEqual(divergent_strict.status, "FAIL")
        self.assertAlmostEqual(divergent_strict.abs_difference, 0.05, places=3)

        # Under looser tolerance (0.1), it should PASS
        loose_results = self.validator.validate_metrics(abs_tol=0.1, rel_tol=0.01)
        divergent_loose = next(r for r in loose_results if r.metric_name == "test_divergent_metric")
        self.assertEqual(divergent_loose.status, "PASS")

    def test_discrepancy_diagnostic_analysis(self):
        """Verify discrepancy diagnosis identifies filtering divergence."""
        diagnostic = self.validator.diagnose_discrepancy("sample_metric", sql_val=150.0, py_val=100.0)
        self.assertIn("Definition / Filtering Divergence", diagnostic)

    def test_custom_metric_registration(self):
        """Verify custom metrics can be registered dynamically."""
        self.validator.register_metric(
            name="custom_constant",
            sql_calculation=lambda eng: 42.0,
            python_calculation=lambda path: 42.0,
            description="Testing custom metric registration",
        )
        metrics = self.validator.compute_sql_metrics()
        self.assertIn("custom_constant", metrics)
        self.assertEqual(metrics["custom_constant"], 42.0)

    def test_report_generation(self):
        """Verify report structure and overall status."""
        results = self.validator.validate_metrics()
        report = self.validator.generate_report(results)
        self.assertEqual(report["overall_status"], "PASS")
        self.assertEqual(report["failed_count"], 0)
        self.assertEqual(len(report["metrics"]), len(results))


if __name__ == "__main__":
    unittest.main()
