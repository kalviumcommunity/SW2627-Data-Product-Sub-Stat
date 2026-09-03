"""Unit and integration tests for Module 1 — CSV & JSON Data Ingestion."""

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
from data_ingestion import generate_ingestion_report, ingest_csv, ingest_json


class TestDataIngestion(unittest.TestCase):
    """Test suite for CSV and JSON ingestion with encoding fallback and normalization."""

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.test_dir.name)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_csv_ingestion_standard(self):
        csv_file = self.temp_path / "test_standard.csv"
        csv_file.write_text("id,name,val\n1,Alice,10.5\n2,Bob,20.0\n", encoding="utf-8")

        df, enc = ingest_csv(csv_file, delimiter=",", encoding="utf-8")
        self.assertEqual(len(df), 2)
        self.assertEqual(list(df.columns), ["id", "name", "val"])
        self.assertEqual(enc, "utf-8")

    def test_csv_custom_delimiter(self):
        csv_file = self.temp_path / "test_semicolon.csv"
        csv_file.write_text("id;name;category\n1;ProductA;Tech\n2;ProductB;Home\n", encoding="utf-8")

        df, enc = ingest_csv(csv_file, delimiter=";", encoding="utf-8")
        self.assertEqual(len(df), 2)
        self.assertEqual(list(df.columns), ["id", "name", "category"])

    def test_csv_encoding_fallback(self):
        csv_file = self.temp_path / "test_latin1.csv"
        # Write bytes that are invalid in UTF-8 but valid in Latin-1
        latin1_bytes = "id,name,city\n1,Hélène,Montréal\n2,München,Bavaria\n".encode("latin1")
        csv_file.write_bytes(latin1_bytes)

        # Ingest with default UTF-8 initial, should gracefully fallback to latin1
        df, enc = ingest_csv(csv_file, delimiter=",", encoding="utf-8")
        self.assertEqual(len(df), 2)
        self.assertIn(enc.lower(), ["latin1", "cp1252", "iso-8859-1"])
        self.assertIn("Hélène", df["name"].values)

    def test_json_ingestion_flat(self):
        json_file = self.temp_path / "test_flat.json"
        json_data = [{"id": 101, "score": 95}, {"id": 102, "score": 88}]
        json_file.write_text(json.dumps(json_data), encoding="utf-8")

        df, enc = ingest_json(json_file, flatten=False)
        self.assertEqual(len(df), 2)
        self.assertEqual(list(df.columns), ["id", "score"])

    def test_json_ingestion_nested_flattening(self):
        json_file = self.temp_path / "test_nested.json"
        json_data = [
            {"user_id": "U1", "details": {"tier": "gold", "points": 500}},
            {"user_id": "U2", "details": {"tier": "silver", "points": 250}},
        ]
        json_file.write_text(json.dumps(json_data), encoding="utf-8")

        df, enc = ingest_json(json_file, flatten=True, sep="_")
        self.assertEqual(len(df), 2)
        self.assertIn("details_tier", df.columns)
        self.assertIn("details_points", df.columns)
        self.assertEqual(df["details_tier"].tolist(), ["gold", "silver"])

    def test_generate_ingestion_report(self):
        df = pd.DataFrame({"col_a": [1, 2, None], "col_b": ["x", "y", "z"]})
        report_file = self.temp_path / "test_report.json"
        dummy_source = self.temp_path / "dummy.csv"
        dummy_source.write_text("a,b\n1,x\n", encoding="utf-8")

        report = generate_ingestion_report(
            df=df,
            source_filepath=dummy_source,
            file_type="csv",
            encoding_used="utf-8",
            delimiter_used=",",
            report_path=report_file,
        )

        self.assertEqual(report["shape"]["rows"], 3)
        self.assertEqual(report["shape"]["columns"], 2)
        self.assertEqual(report["null_counts"]["col_a"], 1)
        self.assertTrue(report_file.exists())

    def test_missing_file_error(self):
        with self.assertRaises(FileNotFoundError):
            ingest_csv(self.temp_path / "non_existent.csv")


if __name__ == "__main__":
    unittest.main()
