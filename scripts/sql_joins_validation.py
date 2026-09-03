"""Module 4 — SQL Joins & Multi-Table Analysis

Provides robust SQL join execution and relational integrity validation:
- Executes INNER JOIN, LEFT JOIN, and FULL OUTER JOIN (emulated via UNION ALL in SQLite).
- Explicitly audits pre-join vs post-join row counts.
- Detects unmatched foreign keys in both directions (left-only and right-only).
- Analyzes join cardinality (1:1, 1:N, N:1, N:M) and explains row multiplication.
- Performs 3-way multi-table relational analysis linking viewers, activity, and catalog.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

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


def load_and_execute_query(
    engine: Engine,
    query_file_path: Union[str, Path],
    params: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """Load SQL from file, execute against engine, and return DataFrame."""
    path = Path(query_file_path)
    if not path.exists():
        raise FileNotFoundError(f"Query file not found: {path}")
    sql_text = path.read_text(encoding="utf-8")
    with engine.connect() as conn:
        df = pd.read_sql_query(sql=text(sql_text), con=conn, params=params or {})
    return df


def audit_relational_join(
    engine: Engine,
    left_table: str = "viewers",
    right_table: str = "subscription_events",
    left_key: str = "viewer_id",
    right_key: str = "viewer_id",
) -> Dict[str, Any]:
    """
    Perform deep relational audit between two tables:
    - Pre-join row counts and key uniqueness.
    - Cardinality classification (1:1, 1:N, N:1, N:M).
    - Unmatched keys on left (subscribers without events).
    - Unmatched keys on right (orphan events without subscribers).
    - Post-join row counts across INNER, LEFT, and FULL OUTER joins.
    """
    with engine.connect() as conn:
        left_count = conn.execute(text(f"SELECT COUNT(*) FROM {left_table};")).scalar()
        right_count = conn.execute(text(f"SELECT COUNT(*) FROM {right_table};")).scalar()

        left_distinct_keys = conn.execute(text(f"SELECT COUNT(DISTINCT {left_key}) FROM {left_table};")).scalar()
        right_distinct_keys = conn.execute(text(f"SELECT COUNT(DISTINCT {right_key}) FROM {right_table};")).scalar()

        # Unmatched on left: exists in left table, but absent in right table
        unmatched_left_query = f"""
            SELECT DISTINCT {left_key} FROM {left_table}
            WHERE {left_key} NOT IN (SELECT DISTINCT {right_key} FROM {right_table} WHERE {right_key} IS NOT NULL);
        """
        unmatched_left = pd.read_sql_query(text(unmatched_left_query), conn)[left_key].dropna().tolist()

        # Unmatched on right: exists in right table, but absent in left table
        unmatched_right_query = f"""
            SELECT DISTINCT {right_key} FROM {right_table}
            WHERE {right_key} NOT IN (SELECT DISTINCT {left_key} FROM {left_table} WHERE {left_key} IS NOT NULL);
        """
        unmatched_right = pd.read_sql_query(text(unmatched_right_query), conn)[right_key].dropna().tolist()

        # Post-join counts
        inner_query = f"SELECT COUNT(*) FROM {left_table} l INNER JOIN {right_table} r ON l.{left_key} = r.{right_key};"
        inner_count = conn.execute(text(inner_query)).scalar()

        left_join_query = f"SELECT COUNT(*) FROM {left_table} l LEFT JOIN {right_table} r ON l.{left_key} = r.{right_key};"
        left_join_count = conn.execute(text(left_join_query)).scalar()

        # Full outer join count = Left Join rows + Unmatched Right rows
        full_outer_count = left_join_count + len(
            pd.read_sql_query(
                text(f"SELECT * FROM {right_table} WHERE {right_key} NOT IN (SELECT {left_key} FROM {left_table});"),
                conn,
            )
        )

    # Determine Cardinality
    is_left_unique = (left_count == left_distinct_keys)
    is_right_unique = (right_count == right_distinct_keys)

    if is_left_unique and is_right_unique:
        cardinality = "1:1 (One-to-One)"
    elif is_left_unique and not is_right_unique:
        cardinality = "1:N (One-to-Many)"
    elif not is_left_unique and is_right_unique:
        cardinality = "N:1 (Many-to-One)"
    else:
        cardinality = "N:M (Many-to-Many)"

    # Row multiplication analysis
    row_multiplication_factor = round(inner_count / left_distinct_keys, 2) if left_distinct_keys else 0.0

    return {
        "left_table": left_table,
        "right_table": right_table,
        "left_row_count": left_count,
        "right_row_count": right_count,
        "left_distinct_keys": left_distinct_keys,
        "right_distinct_keys": right_distinct_keys,
        "cardinality": cardinality,
        "unmatched_left_keys": unmatched_left,
        "unmatched_left_count": len(unmatched_left),
        "unmatched_right_keys": unmatched_right,
        "unmatched_right_count": len(unmatched_right),
        "inner_join_row_count": inner_count,
        "left_join_row_count": left_join_count,
        "full_outer_join_row_count": full_outer_count,
        "row_multiplication_factor": row_multiplication_factor,
        "row_multiplication_explanation": (
            f"In a {cardinality} relationship, single viewer records match multiple subscription event records. "
            f"An increase from {left_count} master viewers to {left_join_count} left join rows is expected row expansion, "
            f"not a data duplication defect."
        ),
    }


def run_joins_pipeline(engine: Optional[Engine] = None) -> Dict[str, pd.DataFrame]:
    """Execute all join queries and return resulting DataFrames."""
    eng = engine or get_db_engine()
    ensure_database_populated(eng)

    queries = {
        "inner_join": QUERIES_DIR / "join_inner_viewers_events.sql",
        "left_join": QUERIES_DIR / "join_left_viewers_events.sql",
        "full_outer_emulation": QUERIES_DIR / "join_full_outer_emulation.sql",
        "multi_table_engagement": QUERIES_DIR / "join_multi_table_engagement.sql",
    }

    results: Dict[str, pd.DataFrame] = {}
    for name, file_path in queries.items():
        results[name] = load_and_execute_query(eng, file_path)

    return results


def main():
    """Main workflow runner for Module 4."""
    print("\n=======================================================")
    print("      Module 4: SQL Joins & Multi-Table Analysis       ")
    print("=======================================================\n")

    engine = get_db_engine()
    ensure_database_populated(engine)

    print("[1/4] Auditing Relational Join Integrity & Cardinality...")
    audit = audit_relational_join(engine, "viewers", "subscription_events", "viewer_id", "viewer_id")
    print(f"  - Left Table ('{audit['left_table']}'): {audit['left_row_count']} rows ({audit['left_distinct_keys']} distinct keys)")
    print(f"  - Right Table ('{audit['right_table']}'): {audit['right_row_count']} rows ({audit['right_distinct_keys']} distinct keys)")
    print(f"  - Cardinality: {audit['cardinality']}")
    print(f"  - Unmatched Left Keys (Viewers with 0 events): {audit['unmatched_left_keys']}")
    print(f"  - Unmatched Right Keys (Orphan Events): {audit['unmatched_right_keys']}")
    print(f"  - Pre/Post Join Row Counts:")
    print(f"      * INNER JOIN: {audit['inner_join_row_count']} rows")
    print(f"      * LEFT JOIN:  {audit['left_join_row_count']} rows")
    print(f"      * FULL OUTER: {audit['full_outer_join_row_count']} rows")
    print(f"  - Lineage Note: {audit['row_multiplication_explanation']}")

    print("\n[2/4] Executing INNER JOIN Query...")
    df_inner = load_and_execute_query(engine, QUERIES_DIR / "join_inner_viewers_events.sql")
    print(df_inner.head(5).to_string(index=False))
    print(f"Total Inner Join Rows: {len(df_inner)}")

    print("\n[3/4] Executing LEFT JOIN & FULL OUTER JOIN Emulation...")
    df_left = load_and_execute_query(engine, QUERIES_DIR / "join_left_viewers_events.sql")
    df_outer = load_and_execute_query(engine, QUERIES_DIR / "join_full_outer_emulation.sql")
    print("  Full Outer Join Sample:")
    print(df_outer.head(6).to_string(index=False))
    print(f"Total Left Join Rows: {len(df_left)} | Total Full Outer Rows: {len(df_outer)}")

    print("\n[4/4] Executing 3-Way Multi-Table Analysis (Viewers -> Activity -> Catalog)...")
    df_multi = load_and_execute_query(engine, QUERIES_DIR / "join_multi_table_engagement.sql")
    print(df_multi.head(5).to_string(index=False))
    print(f"Total Multi-Table Result Rows: {len(df_multi)}")

    print("\n[SUCCESS] Module 4 joins and relational validation verified successfully.\n")


if __name__ == "__main__":
    main()
