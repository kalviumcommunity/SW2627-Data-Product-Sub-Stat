"""Module 3 — SQL Filtering, Grouping & Aggregation

Demonstrates SQL filtering, grouping, and aggregation techniques:
- Pre-aggregation row-level filtering using WHERE.
- Multi-dimensional categorical aggregation with GROUP BY (COUNT, SUM, AVG, MIN, MAX).
- Post-aggregation group-level filtering using HAVING.
- Explicit comparison and verification of WHERE (row filter) vs HAVING (group filter).
- Top-N ranking with multi-column ORDER BY and LIMIT.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

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


def execute_sql_file(
    engine: Engine,
    query_file_path: Union[str, Path],
    params: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """Load and execute a SQL query file and return the resulting DataFrame."""
    path = Path(query_file_path)
    if not path.exists():
        raise FileNotFoundError(f"Query file not found: {path}")
    sql_text = path.read_text(encoding="utf-8")
    with engine.connect() as conn:
        df = pd.read_sql_query(sql=text(sql_text), con=conn, params=params or {})
    return df


def demonstrate_where_vs_having(engine: Engine) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Demonstrates the fundamental difference between WHERE and HAVING:
    - WHERE filters individual transaction records before aggregation.
    - HAVING filters aggregated group metrics after GROUP BY.
    """
    # 1. Total unfiltered records
    with engine.connect() as conn:
        total_rows = conn.execute(text("SELECT COUNT(*) FROM subscription_events;")).scalar()

    # 2. Pre-aggregation filtered records (WHERE)
    where_query = (
        "SELECT event_id, viewer_id, payment_amount, payment_status "
        "FROM subscription_events WHERE payment_status = 'Completed';"
    )
    with engine.connect() as conn:
        df_where = pd.read_sql_query(text(where_query), conn)

    # 3. Aggregated groups with HAVING
    having_query = (
        "SELECT viewer_id, COUNT(event_id) AS event_count, SUM(payment_amount) AS total_spent "
        "FROM subscription_events "
        "WHERE payment_status = 'Completed' "
        "GROUP BY viewer_id "
        "HAVING COUNT(event_id) >= 2 AND SUM(payment_amount) >= 30.00;"
    )
    with engine.connect() as conn:
        df_having = pd.read_sql_query(text(having_query), conn)

    # 4. Total groups without HAVING
    group_query = (
        "SELECT viewer_id, COUNT(event_id) AS event_count, SUM(payment_amount) AS total_spent "
        "FROM subscription_events "
        "WHERE payment_status = 'Completed' "
        "GROUP BY viewer_id;"
    )
    with engine.connect() as conn:
        df_all_groups = pd.read_sql_query(text(group_query), conn)

    comparison_summary = {
        "raw_total_rows": total_rows,
        "rows_after_where": len(df_where),
        "rows_filtered_by_where": total_rows - len(df_where),
        "total_groups_formed": len(df_all_groups),
        "groups_retained_by_having": len(df_having),
        "groups_filtered_by_having": len(df_all_groups) - len(df_having),
    }

    return df_where, df_having, comparison_summary


def run_filtering_aggregation_pipeline(
    engine: Optional[Engine] = None,
) -> Dict[str, pd.DataFrame]:
    """Execute all four filtering, grouping, having, and ranking queries."""
    eng = engine or get_db_engine()
    ensure_database_populated(eng)

    queries = {
        "where_filtering": QUERIES_DIR / "filter_where_demo.sql",
        "group_by_aggregation": QUERIES_DIR / "group_by_aggregation.sql",
        "having_filtering": QUERIES_DIR / "filter_having_demo.sql",
        "ranking_order_limit": QUERIES_DIR / "ranking_order_limit.sql",
    }

    results: Dict[str, pd.DataFrame] = {}
    for name, file_path in queries.items():
        results[name] = execute_sql_file(eng, file_path)

    return results


def main():
    """Main workflow runner for Module 3."""
    print("\n=======================================================")
    print("  Module 3: SQL Filtering, Grouping & Aggregation     ")
    print("=======================================================\n")

    engine = get_db_engine()
    ensure_database_populated(engine)

    print("[1/4] Executing WHERE Filtering Demo...")
    df_where = execute_sql_file(engine, QUERIES_DIR / "filter_where_demo.sql")
    print(df_where.head(5).to_string(index=False))
    print(f"Total Rows Passed WHERE: {len(df_where)}")

    print("\n[2/4] Executing Multi-Dimensional GROUP BY & Aggregation...")
    df_group = execute_sql_file(engine, QUERIES_DIR / "group_by_aggregation.sql")
    print(df_group.to_string(index=False))

    print("\n[3/4] Demonstrating WHERE vs HAVING Distinction...")
    _, df_having, summary = demonstrate_where_vs_having(engine)
    print(f"  - Total Raw Rows: {summary['raw_total_rows']}")
    print(f"  - Rows after WHERE (payment_status='Completed'): {summary['rows_after_where']} ({summary['rows_filtered_by_where']} rows excluded)")
    print(f"  - Total Groups Formed: {summary['total_groups_formed']}")
    print(f"  - Groups Passing HAVING (count >= 2 & sum >= $30): {summary['groups_retained_by_having']} ({summary['groups_filtered_by_having']} groups excluded)")
    print("\n  HAVING Filtered Result:")
    print(df_having.to_string(index=False))

    print("\n[4/4] Executing Top-N Ranking (ORDER BY & LIMIT)...")
    df_rank = execute_sql_file(engine, QUERIES_DIR / "ranking_order_limit.sql")
    print(df_rank.to_string(index=False))

    print("\n[SUCCESS] Module 3 filtering, grouping, and aggregation verified successfully.\n")


if __name__ == "__main__":
    main()
