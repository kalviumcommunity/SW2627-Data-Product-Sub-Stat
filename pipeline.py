"""End-to-end data pipeline: ingest, clean, aggregate, and output."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def ingest(path: str) -> pd.DataFrame:
    logger.info("Ingesting: %s", path)
    df = pd.read_csv(path)
    logger.info("Rows ingested: %s", len(df))
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Cleaning...")
    required_columns = {"customer_id", "order_id", "amount", "segment"}
    missing = sorted(required_columns - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns for cleaning: {missing}")

    initial = len(df)
    cleaned = df.dropna(subset=["customer_id", "amount"]).copy()
    cleaned["amount"] = pd.to_numeric(cleaned["amount"], errors="coerce")
    cleaned = cleaned.dropna(subset=["amount"])
    cleaned = cleaned[cleaned["amount"] > 0]
    logger.info("Cleaned: %s -> %s", initial, len(cleaned))
    return cleaned


def aggregate(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Aggregating...")
    agg = (
        df.groupby("segment", as_index=False)
        .agg(revenue=("amount", "sum"), orders=("order_id", "count"))
        .sort_values("segment")
    )
    logger.info("Segments: %s", len(agg))
    return agg


def output(cleaned_df: pd.DataFrame, agg_df: pd.DataFrame, out_dir: str) -> None:
    output_dir = Path(out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    cleaned_path = output_dir / "cleaned.csv"
    aggregated_path = output_dir / "aggregated.csv"
    cleaned_df.to_csv(cleaned_path, index=False)
    agg_df.to_csv(aggregated_path, index=False)
    logger.info("Output written to: %s", output_dir)
    logger.info("Pipeline complete")


def load_config(config_path: str | None) -> dict[str, str]:
    if not config_path:
        return {}
    with open(config_path, "r", encoding="utf-8") as config_file:
        config = json.load(config_file)
    if not isinstance(config, dict):
        raise ValueError("Config must be a JSON object")
    return config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the ingestion-clean-aggregation pipeline.")
    parser.add_argument("--config", help="Path to a JSON config file with 'input' and/or 'output'.")
    parser.add_argument("--input", help="Path to input CSV file.")
    parser.add_argument("--output", help="Directory to write output CSV files.")
    args = parser.parse_args()

    config = load_config(args.config)
    input_path = args.input or config.get("input")
    output_path = args.output or config.get("output") or "output"
    if not input_path:
        parser.error("Input path is required via --input or config file key 'input'.")

    args.input = input_path
    args.output = output_path
    return args


if __name__ == "__main__":
    cli_args = parse_args()
    raw = ingest(cli_args.input)
    cleaned = clean(raw)
    aggregated = aggregate(cleaned)
    output(cleaned, aggregated, cli_args.output)
