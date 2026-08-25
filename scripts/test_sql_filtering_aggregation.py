"""Unit tests for Module 3 — SQL Filtering, Grouping & Aggregation."""

import unittest
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

from scripts.sql_filtering_aggregation import (
    QUERIES_DIR,
    demonstrate_where_vs_having,
    execute_sql_file,
    run_filtering_aggregation_pipeline,
)


class TestSQLFilteringAggregation(unittest.TestCase):
    """Test suite for WHERE, GROUP BY, HAVING, and ORDER BY queries."""

    def setUp(self):
        """Set up in-memory SQLite database populated with controlled fixture data."""
        self.engine = create_engine("sqlite:///:memory:")

        # Populating viewers fixture
        viewers_df = pd.DataFrame(
            {
                "viewer_id": ["V101", "V102", "V103", "V104"],
                "signup_date": ["2025-01-01", "2025-01-05", "2025-01-10", "2025-01-15"],
                "plan_tier": ["Premium", "Premium", "Basic", "Standard"],
                "country": ["US", "US", "UK", "CA"],
                "device_type": ["SmartTV", "Mobile", "Web", "Tablet"],
            }
        )
        viewers_df.to_sql("viewers", con=self.engine, index=False)

        # Populating events fixture (including Completed and Failed statuses, and varying amounts)
        events_df = pd.DataFrame(
            {
                "event_id": [1, 2, 3, 4, 5, 6],
                "viewer_id": ["V101", "V101", "V102", "V102", "V103", "V104"],
                "event_date": ["2025-01-15", "2025-02-15", "2025-01-20", "2025-02-20", "2025-02-22", "2025-03-01"],
                "payment_amount": [19.99, 19.99, 19.99, 19.99, 9.99, 14.99],
                "payment_status": ["Completed", "Completed", "Completed", "Completed", "Failed", "Completed"],
                "auto_renew": [1, 1, 1, 1, 0, 1],
            }
        )
        events_df.to_sql("subscription_events", con=self.engine, index=False)

        # Populating viewer activity fixture
        activity_df = pd.DataFrame(
            {
                "viewer_id": ["V101", "V101", "V102", "V103", "V104", "V104", "V104"],
                "content_id": ["C101", "C102", "C101", "C103", "C101", "C102", "C103"],
                "session_timestamp": [
                    "2025-01-15 14:00:00",
                    "2025-01-18 19:30:00",
                    "2025-01-20 20:00:00",
                    "2025-02-10 10:00:00",
                    "2025-02-12 12:00:00",
                    "2025-02-14 15:00:00",
                    "2025-02-16 18:00:00",
                ],
                "subscription_date": ["2025-01-01"] * 7,
                "watch_duration_mins": [60.0, 45.0, 30.0, 15.0, 50.0, 55.0, 40.0],
                "completion_status": ["Completed", "Completed", "Partial", "Completed", "Completed", "Completed", "Partial"],
            }
        )
        activity_df.to_sql("viewer_activity", con=self.engine, index=False)

    def test_where_row_filtering(self):
        """Verify WHERE filters row records before grouping."""
        df = execute_sql_file(self.engine, QUERIES_DIR / "filter_where_demo.sql")
        # In fixture: 6 total events, 1 is Failed (event_id 5), 5 are Completed with payment_amount >= 10.00
        self.assertEqual(len(df), 5)
        self.assertTrue((df["payment_status"] == "Completed").all())
        self.assertTrue((df["payment_amount"] >= 10.00).all())

    def test_group_by_aggregation(self):
        """Verify multi-column GROUP BY calculates aggregate stats correctly."""
        df = execute_sql_file(self.engine, QUERIES_DIR / "group_by_aggregation.sql")
        self.assertIn("plan_tier", df.columns)
        self.assertIn("country", df.columns)
        self.assertIn("total_amount", df.columns)
        self.assertIn("avg_amount", df.columns)
        # Premium US has 2 viewers (V101, V102) with 4 events of 19.99 = 79.96
        prem_us = df[(df["plan_tier"] == "Premium") & (df["country"] == "US")].iloc[0]
        self.assertEqual(prem_us["total_events"], 4)
        self.assertEqual(prem_us["distinct_viewers"], 2)
        self.assertAlmostEqual(prem_us["total_amount"], 79.96, places=2)

    def test_having_group_filtering(self):
        """Verify HAVING filters aggregated groups based on aggregate criteria."""
        df = execute_sql_file(self.engine, QUERIES_DIR / "filter_having_demo.sql")
        self.assertIn("viewer_id", df.columns)
        self.assertIn("completed_transactions", df.columns)
        self.assertIn("total_spent", df.columns)
        # Only V101 ($39.98, 2 tx) and V102 ($39.98, 2 tx) satisfy count >= 2 and total_spent >= 30.00
        self.assertEqual(len(df), 2)
        self.assertSetEqual(set(df["viewer_id"]), {"V101", "V102"})

    def test_demonstrate_where_vs_having(self):
        """Verify where_vs_having correctly isolates row vs group reduction metrics."""
        df_where, df_having, summary = demonstrate_where_vs_having(self.engine)
        self.assertEqual(summary["raw_total_rows"], 6)
        self.assertEqual(summary["rows_after_where"], 5)
        self.assertEqual(summary["rows_filtered_by_where"], 1)
        self.assertEqual(summary["total_groups_formed"], 3)  # V101, V102, V104 have completed tx
        self.assertEqual(summary["groups_retained_by_having"], 2)  # V101 and V102
        self.assertEqual(summary["groups_filtered_by_having"], 1)  # V104 filtered out by HAVING

    def test_ranking_order_limit(self):
        """Verify top-N ranking returns ordered rows capped by LIMIT."""
        df = execute_sql_file(self.engine, QUERIES_DIR / "ranking_order_limit.sql")
        self.assertLessEqual(len(df), 5)
        # V104 total_watch_mins = 50 + 55 + 40 = 145.0, should be rank #1
        self.assertEqual(df.iloc[0]["viewer_id"], "V104")
        self.assertEqual(df.iloc[0]["total_watch_mins"], 145.0)
        # Check sorting order is non-ascending
        self.assertTrue(df["total_watch_mins"].is_monotonic_decreasing)

    def test_run_filtering_aggregation_pipeline(self):
        """Verify full pipeline returns dictionary of all 4 query results."""
        results = run_filtering_aggregation_pipeline(self.engine)
        self.assertEqual(len(results), 4)
        for key in ["where_filtering", "group_by_aggregation", "having_filtering", "ranking_order_limit"]:
            self.assertIn(key, results)
            self.assertIsInstance(results[key], pd.DataFrame)


if __name__ == "__main__":
    unittest.main()
