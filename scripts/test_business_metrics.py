"""Unit tests for Module 2 — SQL Business Metrics Query Design."""

import unittest
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

from scripts.business_metrics import (
    QUERIES_DIR,
    execute_metric_query,
    load_sql_query,
    run_all_metrics,
)


class TestBusinessMetrics(unittest.TestCase):
    """Test suite for loading and executing business metric SQL queries."""

    def setUp(self):
        """Set up in-memory database with populated test data."""
        self.engine = create_engine("sqlite:///:memory:")

        # Populating test tables with representative schema
        viewers_df = pd.DataFrame(
            {
                "viewer_id": ["V101", "V102", "V103", "V104"],
                "signup_date": ["2025-01-01", "2025-01-10", "2025-02-01", "2025-02-15"],
                "plan_tier": ["Premium", "Standard", "Basic", "Premium"],
                "country": ["US", "CA", "UK", "US"],
                "device_type": ["SmartTV", "Mobile", "Web", "Tablet"],
            }
        )
        viewers_df.to_sql("viewers", con=self.engine, index=False)

        events_df = pd.DataFrame(
            {
                "event_id": [1, 2, 3, 4, 5],
                "viewer_id": ["V101", "V101", "V102", "V103", "V104"],
                "event_date": ["2025-01-15", "2025-02-15", "2025-01-20", "2025-02-20", "2025-03-01"],
                "payment_amount": [19.99, 19.99, 14.99, 9.99, 19.99],
                "payment_status": ["Completed", "Completed", "Completed", "Failed", "Completed"],
                "auto_renew": [1, 1, 1, 0, 1],
            }
        )
        events_df.to_sql("subscription_events", con=self.engine, index=False)

        activity_df = pd.DataFrame(
            {
                "viewer_id": ["V101", "V101", "V102", "V103"],
                "content_id": ["C101", "C102", "C101", "C103"],
                "session_timestamp": ["2025-01-15 14:00:00", "2025-01-18 19:30:00", "2025-01-20 20:00:00", "2025-02-10 10:00:00"],
                "subscription_date": ["2025-01-01", "2025-01-01", "2025-01-10", "2025-02-01"],
                "watch_duration_mins": [45.0, 30.0, 50.0, 20.0],
                "completion_status": ["Completed", "Partial", "Completed", "Completed"],
            }
        )
        activity_df.to_sql("viewer_activity", con=self.engine, index=False)

        catalog_df = pd.DataFrame(
            {
                "content_id": ["C101", "C102", "C103"],
                "title": ["Show A", "Show B", "Movie C"],
                "total_duration_mins": [50.0, 30.0, 90.0],
                "genre": ["Drama", "Comedy", "Drama"],
            }
        )
        catalog_df.to_sql("content_catalog", con=self.engine, index=False)

    def test_load_sql_query(self):
        """Verify SQL files load without errors."""
        q_file = QUERIES_DIR / "monthly_active_viewers.sql"
        query = load_sql_query(q_file)
        self.assertIn("SELECT", query)
        self.assertIn("viewer_activity", query)

    def test_monthly_active_viewers(self):
        """Verify Monthly Active Viewers (MAV) query execution and results."""
        q_file = QUERIES_DIR / "monthly_active_viewers.sql"
        df = execute_metric_query(self.engine, q_file)
        self.assertIn("activity_month", df.columns)
        self.assertIn("active_viewers", df.columns)
        self.assertEqual(len(df), 2)  # Jan and Feb 2025
        jan_row = df[df["activity_month"] == "2025-01"].iloc[0]
        self.assertEqual(jan_row["active_viewers"], 2)  # V101 and V102

    def test_revenue_by_plan_tier(self):
        """Verify revenue and ARPU calculation by plan tier."""
        q_file = QUERIES_DIR / "revenue_by_plan_tier.sql"
        df = execute_metric_query(self.engine, q_file)
        self.assertIn("plan_tier", df.columns)
        self.assertIn("total_revenue", df.columns)
        self.assertIn("arpu", df.columns)
        prem_row = df[df["plan_tier"] == "Premium"].iloc[0]
        # V101 (2 payments * 19.99 = 39.98) + V104 (1 payment * 19.99 = 19.99) -> 59.97 / 2 users = 29.985
        self.assertAlmostEqual(prem_row["total_revenue"], 59.97, places=2)
        self.assertEqual(prem_row["paying_subscribers"], 2)

    def test_payment_conversion_rate(self):
        """Verify transaction success and conversion rates."""
        q_file = QUERIES_DIR / "payment_conversion_rate.sql"
        df = execute_metric_query(self.engine, q_file)
        self.assertIn("plan_tier", df.columns)
        self.assertIn("success_rate_pct", df.columns)
        # Total attempts in test set: 5, Completed: 4, Failed: 1 (Basic tier has 0% success)
        basic_row = df[df["plan_tier"] == "Basic"].iloc[0]
        self.assertEqual(basic_row["failed_transactions"], 1)
        self.assertEqual(basic_row["success_rate_pct"], 0.0)

    def test_monthly_revenue_trend(self):
        """Verify monthly recurring revenue trend query."""
        q_file = QUERIES_DIR / "monthly_revenue_trend.sql"
        df = execute_metric_query(self.engine, q_file)
        self.assertIn("revenue_month", df.columns)
        self.assertIn("monthly_revenue", df.columns)
        self.assertEqual(len(df), 3)  # Jan, Feb, Mar

    def test_content_completion_rate(self):
        """Verify completion rate and average duration by genre."""
        q_file = QUERIES_DIR / "content_completion_rate.sql"
        df = execute_metric_query(self.engine, q_file)
        self.assertIn("genre", df.columns)
        self.assertIn("completion_rate_pct", df.columns)
        self.assertTrue((df["completion_rate_pct"] >= 0).all() and (df["completion_rate_pct"] <= 100).all())

    def test_run_all_metrics(self):
        """Verify all SQL queries in queries/ directory execute successfully."""
        results = run_all_metrics(self.engine, queries_directory=QUERIES_DIR)
        self.assertGreaterEqual(len(results), 4)
        for metric_name, df in results.items():
            self.assertIsInstance(df, pd.DataFrame)
            self.assertFalse(df.empty)


if __name__ == "__main__":
    unittest.main()
