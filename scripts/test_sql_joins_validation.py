"""Unit tests for Module 4 — SQL Joins & Multi-Table Analysis."""

import unittest
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

from scripts.sql_joins_validation import (
    QUERIES_DIR,
    audit_relational_join,
    load_and_execute_query,
    run_joins_pipeline,
)


class TestSQLJoinsValidation(unittest.TestCase):
    """Test suite for relational joins, cardinality, unmatched key tracking, and full outer emulation."""

    def setUp(self):
        """Set up in-memory database populated with controlled join fixture data."""
        self.engine = create_engine("sqlite:///:memory:")

        # Populating viewers master fixture (V101, V102, V103, V104)
        viewers_df = pd.DataFrame(
            {
                "viewer_id": ["V101", "V102", "V103", "V104"],
                "signup_date": ["2025-01-01", "2025-01-05", "2025-01-10", "2025-01-15"],
                "plan_tier": ["Premium", "Standard", "Basic", "Premium"],
                "country": ["US", "CA", "UK", "US"],
                "device_type": ["SmartTV", "Mobile", "Web", "Tablet"],
            }
        )
        viewers_df.to_sql("viewers", con=self.engine, index=False)

        # Populating events fixture (V101 has 2 events (1:N), V102 has 1, V999 is orphan (no viewer in master))
        # Note: V103 and V104 have 0 events (unmatched left)
        events_df = pd.DataFrame(
            {
                "event_id": [1, 2, 3, 4],
                "viewer_id": ["V101", "V101", "V102", "V999"],
                "event_date": ["2025-01-15", "2025-02-15", "2025-01-20", "2025-03-01"],
                "payment_amount": [19.99, 19.99, 14.99, 29.99],
                "payment_status": ["Completed", "Completed", "Completed", "Completed"],
                "auto_renew": [1, 1, 1, 1],
            }
        )
        events_df.to_sql("subscription_events", con=self.engine, index=False)

        # Populating viewer activity and content catalog fixtures
        activity_df = pd.DataFrame(
            {
                "viewer_id": ["V101", "V102", "V103"],
                "content_id": ["C101", "C102", "C999"],  # C999 uncataloged
                "session_timestamp": ["2025-01-15 14:00:00", "2025-01-20 20:00:00", "2025-02-10 10:00:00"],
                "subscription_date": ["2025-01-01", "2025-01-05", "2025-01-10"],
                "watch_duration_mins": [45.0, 30.0, 60.0],
                "completion_status": ["Completed", "Partial", "Completed"],
            }
        )
        activity_df.to_sql("viewer_activity", con=self.engine, index=False)

        catalog_df = pd.DataFrame(
            {
                "content_id": ["C101", "C102"],
                "title": ["Stranger Streams", "Tech Valley"],
                "total_duration_mins": [60.0, 45.0],
                "genre": ["Sci-Fi", "Drama"],
            }
        )
        catalog_df.to_sql("content_catalog", con=self.engine, index=False)

    def test_audit_relational_join_cardinality_and_counts(self):
        """Verify audit correctly determines 1:N cardinality and isolates unmatched keys."""
        audit = audit_relational_join(self.engine, "viewers", "subscription_events", "viewer_id", "viewer_id")

        self.assertEqual(audit["left_row_count"], 4)
        self.assertEqual(audit["right_row_count"], 4)
        self.assertEqual(audit["cardinality"], "1:N (One-to-Many)")

        # Unmatched left: V103 and V104 have no events
        self.assertEqual(audit["unmatched_left_count"], 2)
        self.assertSetEqual(set(audit["unmatched_left_keys"]), {"V103", "V104"})

        # Unmatched right: V999 has no master record
        self.assertEqual(audit["unmatched_right_count"], 1)
        self.assertSetEqual(set(audit["unmatched_right_keys"]), {"V999"})

        # Post-join counts:
        # INNER: V101(2) + V102(1) = 3
        self.assertEqual(audit["inner_join_row_count"], 3)
        # LEFT: V101(2) + V102(1) + V103(1) + V104(1) = 5
        self.assertEqual(audit["left_join_row_count"], 5)
        # FULL OUTER: Left Join (5) + Orphan Right (1) = 6
        self.assertEqual(audit["full_outer_join_row_count"], 6)

    def test_inner_join_query(self):
        """Verify inner join excludes unmatched keys on both sides."""
        df = load_and_execute_query(self.engine, QUERIES_DIR / "join_inner_viewers_events.sql")
        self.assertEqual(len(df), 3)
        self.assertNotIn("V103", df["viewer_id"].values)
        self.assertNotIn("V104", df["viewer_id"].values)
        self.assertNotIn("V999", df["viewer_id"].values)

    def test_left_join_query(self):
        """Verify left join retains all viewers and populates NULL for unmatched events."""
        df = load_and_execute_query(self.engine, QUERIES_DIR / "join_left_viewers_events.sql")
        self.assertEqual(len(df), 5)
        # Check that V103 and V104 are present with NULL event_id
        unmatched_rows = df[df["event_id"].isna()]
        self.assertEqual(len(unmatched_rows), 2)
        self.assertSetEqual(set(unmatched_rows["viewer_id"]), {"V103", "V104"})

    def test_full_outer_emulation_query(self):
        """Verify SQLite UNION ALL emulation produces complete set with classification."""
        df = load_and_execute_query(self.engine, QUERIES_DIR / "join_full_outer_emulation.sql")
        self.assertEqual(len(df), 6)
        categories = df["match_category"].value_counts().to_dict()
        self.assertEqual(categories.get("Matched"), 3)
        self.assertEqual(categories.get("Master Viewer Only (No Events)"), 2)
        self.assertEqual(categories.get("Orphan Event Only (No Viewer Record)"), 1)

    def test_multi_table_engagement_query(self):
        """Verify 3-way join links viewers, activity, and content catalog correctly."""
        df = load_and_execute_query(self.engine, QUERIES_DIR / "join_multi_table_engagement.sql")
        self.assertEqual(len(df), 3)
        # Check fallback genre for uncataloged C999
        v103_row = df[df["viewer_id"] == "V103"].iloc[0]
        self.assertEqual(v103_row["content_genre"], "General")

    def test_run_joins_pipeline(self):
        """Verify run_joins_pipeline executes all join queries."""
        results = run_joins_pipeline(self.engine)
        self.assertEqual(len(results), 4)
        for key in ["inner_join", "left_join", "full_outer_emulation", "multi_table_engagement"]:
            self.assertIn(key, results)


if __name__ == "__main__":
    unittest.main()
