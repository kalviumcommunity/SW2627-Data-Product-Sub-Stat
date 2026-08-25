"""Module 1 — SQL Environment & Database Integration

Provides a reproducible database integration workflow using SQLite, SQLAlchemy, and Pandas:
- Database engine creation with environment variable support for credentials/URLs.
- Automated data loading from cleaned raw datasets into relational tables.
- Table existence and schema inspection via SQLAlchemy Inspector.
- SQL-to-DataFrame query execution with parameterization.
- Schema audit reporting and integration verification.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Default SQLite database path in data/ directory
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "sub_stat.db"
DEFAULT_DATABASE_URL = f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"


def get_db_url(custom_url: Optional[str] = None) -> str:
    """
    Retrieve database URL from custom argument, environment variable, or default SQLite path.
    Keeps credentials and sensitive paths outside of source code.
    """
    if custom_url:
        return custom_url
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


def create_db_engine(db_url: Optional[str] = None, echo: bool = False) -> Engine:
    """
    Create and return an active SQLAlchemy Engine instance.
    """
    resolved_url = get_db_url(db_url)
    # Ensure parent directory exists for file-based SQLite databases
    if resolved_url.startswith("sqlite:///") and not resolved_url.startswith("sqlite:///:memory:"):
        db_file_path = Path(resolved_url.replace("sqlite:///", ""))
        db_file_path.parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(resolved_url, echo=echo)
    logger.info(f"Database engine initialized for: {resolved_url.split('@')[-1] if '@' in resolved_url else resolved_url}")
    return engine


def verify_table_exists(engine: Engine, table_name: str) -> bool:
    """
    Check whether a table exists in the database.
    """
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def load_csv_to_table(
    engine: Engine,
    csv_path: Union[str, Path],
    table_name: str,
    if_exists: str = "replace",
) -> int:
    """
    Load a CSV dataset into a SQL table using Pandas and SQLAlchemy.

    Returns:
        Number of rows inserted.
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    df = pd.read_csv(path)
    df.to_sql(name=table_name, con=engine, if_exists=if_exists, index=False)
    logger.info(f"Loaded {len(df)} rows from '{path.name}' into SQL table '{table_name}'.")
    return len(df)


def initialize_database(
    engine: Optional[Engine] = None,
    data_dir: Optional[Union[str, Path]] = None,
) -> Dict[str, int]:
    """
    Initialize the database with project datasets:
    - viewers_master.csv -> 'viewers'
    - subscription_events.csv -> 'subscription_events'
    - viewer_activity_sample.csv -> 'viewer_activity'
    - content_catalog.csv -> 'content_catalog'

    Returns:
        Dictionary mapping table names to inserted row counts.
    """
    if engine is None:
        engine = create_db_engine()

    base_dir = Path(data_dir) if data_dir else Path(__file__).resolve().parent.parent / "data" / "raw"

    dataset_table_map = {
        "viewers_master.csv": "viewers",
        "subscription_events.csv": "subscription_events",
        "viewer_activity_sample.csv": "viewer_activity",
        "content_catalog.csv": "content_catalog",
    }

    results = {}
    for filename, table_name in dataset_table_map.items():
        file_path = base_dir / filename
        if file_path.exists():
            rows = load_csv_to_table(engine, file_path, table_name)
            results[table_name] = rows
        else:
            logger.warning(f"File {filename} not found in {base_dir}, skipping.")

    return results


def inspect_database_schema(engine: Engine) -> Dict[str, Any]:
    """
    Inspect all tables in the database and return detailed schema metadata.

    Returns:
        Dictionary containing table names, column specifications, and row counts.
    """
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    schema_info: Dict[str, Any] = {"tables": {}}

    with engine.connect() as conn:
        for table in table_names:
            columns_data = inspector.get_columns(table)
            columns_summary = [
                {
                    "name": col["name"],
                    "type": str(col["type"]),
                    "nullable": col.get("nullable", True),
                    "primary_key": bool(col.get("primary_key", False)),
                }
                for col in columns_data
            ]
            row_count_res = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            schema_info["tables"][table] = {
                "columns": columns_summary,
                "row_count": row_count_res,
                "column_count": len(columns_summary),
            }

    return schema_info


def query_to_dataframe(
    engine: Engine,
    query: str,
    params: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """
    Execute a SQL query against the database and return the result as a Pandas DataFrame.
    """
    with engine.connect() as conn:
        df = pd.read_sql_query(sql=text(query), con=conn, params=params or {})
    return df


def main():
    """Main workflow demonstrating database setup, loading, querying, and inspection."""
    print("\n=======================================================")
    print("  Module 1: SQL Environment & Database Integration    ")
    print("=======================================================\n")

    engine = create_db_engine()
    print(f"[1/4] Initializing Database & Loading Tables...")
    loaded_tables = initialize_database(engine)
    for tbl, count in loaded_tables.items():
        print(f"  - Table '{tbl}': {count} rows loaded successfully.")

    print(f"\n[2/4] Inspecting Database Schema...")
    schema = inspect_database_schema(engine)
    for tbl, meta in schema["tables"].items():
        cols = [c["name"] for c in meta["columns"]]
        print(f"  - Table '{tbl}' ({meta['row_count']} rows, {meta['column_count']} cols): {', '.join(cols)}")

    print(f"\n[3/4] Testing SQL-to-DataFrame Query...")
    sample_query = """
        SELECT plan_tier, COUNT(*) AS viewer_count
        FROM viewers
        GROUP BY plan_tier
        ORDER BY viewer_count DESC;
    """
    df_result = query_to_dataframe(engine, sample_query)
    print("  Query Result:")
    print(df_result.to_string(index=False))

    print(f"\n[4/4] Testing Parameterized SQL Query...")
    param_query = """
        SELECT viewer_id, payment_amount, payment_status, event_date
        FROM subscription_events
        WHERE payment_status = :status
        ORDER BY payment_amount DESC
        LIMIT 3;
    """
    df_param = query_to_dataframe(engine, param_query, params={"status": "Completed"})
    print("  Parameterized Query Result (Top Completed Payments):")
    print(df_param.to_string(index=False))

    print("\n[SUCCESS] Module 1 database workflow executed and verified successfully.\n")


if __name__ == "__main__":
    main()
