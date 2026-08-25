"""Unit tests for Module 1 — SQL Environment & Database Integration."""

import unittest
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

from scripts.database_integration import (
    create_db_engine,
    get_db_url,
    initialize_database,
    inspect_database_schema,
    load_csv_to_table,
    query_to_dataframe,
    verify_table_exists,
)


class TestDatabaseIntegration(unittest.TestCase):
    """Test suite for database connection, loading, querying, and schema inspection."""

    def setUp(self):
        """Set up an isolated in-memory SQLite engine for fast testing."""
        self.engine = create_engine("sqlite:///:memory:")
        self.test_data = pd.DataFrame(
            {
                "viewer_id": ["V101", "V102", "V103"],
                "plan_tier": ["Premium", "Standard", "Basic"],
                "monthly_fee": [19.99, 14.99, 9.99],
            }
        )

    def test_get_db_url_default_and_custom(self):
        """Verify default and custom database URL retrieval."""
        custom = "sqlite:///custom_test.db"
        self.assertEqual(get_db_url(custom), custom)
        default_url = get_db_url()
        self.assertTrue(default_url.startswith("sqlite:///"))

    def test_create_engine(self):
        """Verify engine instantiation and connectivity."""
        engine = create_db_engine("sqlite:///:memory:")
        self.assertIsNotNone(engine)
        with engine.connect() as conn:
            self.assertFalse(conn.closed)

    def test_table_loading_and_existence(self):
        """Verify DataFrame can be loaded into table and verified."""
        self.test_data.to_sql("test_viewers", con=self.engine, index=False)
        self.assertTrue(verify_table_exists(self.engine, "test_viewers"))
        self.assertFalse(verify_table_exists(self.engine, "non_existent_table"))

    def test_schema_inspection(self):
        """Verify schema inspector accurately reports column names and row counts."""
        self.test_data.to_sql("test_viewers", con=self.engine, index=False)
        schema = inspect_database_schema(self.engine)

        self.assertIn("test_viewers", schema["tables"])
        table_meta = schema["tables"]["test_viewers"]
        self.assertEqual(table_meta["row_count"], 3)
        self.assertEqual(table_meta["column_count"], 3)
        col_names = [col["name"] for col in table_meta["columns"]]
        self.assertListEqual(col_names, ["viewer_id", "plan_tier", "monthly_fee"])

    def test_query_to_dataframe(self):
        """Verify SQL queries return matching Pandas DataFrames."""
        self.test_data.to_sql("test_viewers", con=self.engine, index=False)
        query = "SELECT viewer_id, plan_tier FROM test_viewers WHERE plan_tier = 'Premium'"
        df = query_to_dataframe(self.engine, query)

        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]["viewer_id"], "V101")
        self.assertEqual(df.iloc[0]["plan_tier"], "Premium")

    def test_query_to_dataframe_parameterized(self):
        """Verify parameterized queries execute correctly and protect against injection."""
        self.test_data.to_sql("test_viewers", con=self.engine, index=False)
        query = "SELECT * FROM test_viewers WHERE monthly_fee > :min_fee"
        df = query_to_dataframe(self.engine, query, params={"min_fee": 10.00})

        self.assertEqual(len(df), 2)
        self.assertListEqual(df["viewer_id"].tolist(), ["V101", "V102"])

    def test_initialize_database_with_raw_data(self):
        """Verify full project database initialization loads core tables."""
        raw_dir = Path(__file__).resolve().parent.parent / "data" / "raw"
        if raw_dir.exists() and (raw_dir / "viewers_master.csv").exists():
            loaded = initialize_database(self.engine, data_dir=raw_dir)
            self.assertIn("viewers", loaded)
            self.assertIn("subscription_events", loaded)
            self.assertTrue(verify_table_exists(self.engine, "viewers"))
            self.assertTrue(verify_table_exists(self.engine, "subscription_events"))


if __name__ == "__main__":
    unittest.main()
