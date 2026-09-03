"""Module 2 — SQL Business Metrics Query Design

Provides a modular Python workflow to execute reusable SQL metric query files:
- Loads modular .sql query files from the queries/ directory.
- Connects to SQLite (or configured database) via SQLAlchemy.
- Populates database tables if needed to guarantee reproducible execution.
- Returns and formats metric results as clean Pandas DataFrames.
- Generates business analytics summaries for stakeholder reporting.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "sub_stat.db"
DEFAULT_DATABASE_URL = f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"
QUERIES_DIR = Path(__file__).resolve().parent.parent / "queries"


def get_db_engine(db_url: Optional[str] = None) -> Engine:
    """Create and return an active SQLAlchemy Engine instance."""
    resolved_url = db_url or os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    if resolved_url.startswith("sqlite:///") and not resolved_url.startswith("sqlite:///:memory:"):
        db_file = Path(resolved_url.replace("sqlite:///", ""))
        db_file.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(resolved_url)


def ensure_database_populated(engine: Engine, raw_data_dir: Optional[Union[str, Path]] = None) -> None:
    """Ensure database has the required project tables loaded from CSV files."""
    data_dir = Path(raw_data_dir) if raw_data_dir else Path(__file__).resolve().parent.parent / "data" / "raw"
    tables = {
        "viewers_master.csv": "viewers",
        "subscription_events.csv": "subscription_events",
        "viewer_activity_sample.csv": "viewer_activity",
        "content_catalog.csv": "content_catalog",
    }
    with engine.connect() as conn:
        for csv_name, tbl_name in tables.items():
            check = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name=:tbl;"),
                {"tbl": tbl_name},
            ).fetchone()
            if not check:
                csv_path = data_dir / csv_name
                if csv_path.exists():
                    df = pd.read_csv(csv_path)
                    df.to_sql(tbl_name, con=engine, if_exists="replace", index=False)
                    logger.info(f"Populated table '{tbl_name}' ({len(df)} rows) from '{csv_name}'.")


def load_sql_query(query_file_path: Union[str, Path]) -> str:
    """
    Load a raw SQL query from a .sql file.
    """
    path = Path(query_file_path)
    if not path.exists():
        raise FileNotFoundError(f"Query file not found: {path}")
    return path.read_text(encoding="utf-8")


def execute_metric_query(
    engine: Engine,
    query_file_path: Union[str, Path],
    params: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """
    Load and execute a .sql metric query file, returning a Pandas DataFrame.
    """
    sql_text = load_sql_query(query_file_path)
    with engine.connect() as conn:
        df = pd.read_sql_query(sql=text(sql_text), con=conn, params=params or {})
    logger.info(f"Executed '{Path(query_file_path).name}' -> {len(df)} rows returned.")
    return df


def run_all_metrics(
    engine: Optional[Engine] = None,
    queries_directory: Optional[Union[str, Path]] = None,
) -> Dict[str, pd.DataFrame]:
    """
    Execute all available SQL metric query files in queries/ directory.

    Returns:
        Dictionary mapping metric query names to result DataFrames.
    """
    eng = engine or get_db_engine()
    ensure_database_populated(eng)
    q_dir = Path(queries_directory) if queries_directory else QUERIES_DIR

    results: Dict[str, pd.DataFrame] = {}
    sql_files = sorted(q_dir.glob("*.sql"))

    for sql_file in sql_files:
        metric_name = sql_file.stem
        try:
            df = execute_metric_query(eng, sql_file)
            results[metric_name] = df
        except Exception as e:
            logger.error(f"Failed to execute query '{sql_file.name}': {e}")
            raise e

    return results


def main():
    """Main workflow executing and formatting all business metric queries."""
    print("\n=======================================================")
    print("      Module 2: SQL Business Metrics Query Runner      ")
    print("=======================================================\n")

    engine = get_db_engine()
    ensure_database_populated(engine)

    metric_dfs = run_all_metrics(engine)

    for metric_name, df in metric_dfs.items():
        print(f"\n--- [Metric: {metric_name.replace('_', ' ').title()}] ---")
        if df.empty:
            print("  (No records found)")
        else:
            print(df.to_string(index=False))
        print(f"Total Rows: {len(df)}")

    print("\n[SUCCESS] All SQL business metrics executed and verified successfully.\n")


if __name__ == "__main__":
    main()
