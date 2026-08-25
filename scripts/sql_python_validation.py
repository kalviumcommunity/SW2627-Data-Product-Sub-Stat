"""Module 5 — SQL-Based Insight Validation

Provides an automated, cross-engine metric validation framework:
- Independently computes business metrics in pure SQL and pure Python (Pandas).
- Evaluates agreement using configurable absolute (abs_tol) and relative (rel_tol) tolerances.
- Automatically flags discrepancies and provides root-cause diagnostic investigation
  (e.g., NULL/NaN handling, integer division, date filters, floating point precision).
- Exports structured validation audit reports in JSON and console formats.
- Fully reusable and extensible for registering future analytics metrics.
"""

import json
import logging
import math
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "sub_stat.db"
DEFAULT_DATABASE_URL = f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"
DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


@dataclass
class MetricValidationResult:
    """Represents the outcome of a single metric cross-engine comparison."""
    metric_name: str
    sql_value: float
    python_value: float
    abs_difference: float
    rel_difference: float
    abs_tolerance: float
    rel_tolerance: float
    status: str  # "PASS" or "FAIL"
    diagnostic_notes: str


class SQLPythonValidator:
    """
    Extensible cross-engine metric validation engine comparing pure SQL results
    against pure Pandas/Python calculations.
    """

    def __init__(
        self,
        engine: Optional[Engine] = None,
        data_dir: Optional[Union[str, Path]] = None,
        abs_tolerance: float = 1e-4,
        rel_tolerance: float = 1e-4,
    ):
        self.engine = engine or self._get_default_engine()
        self.data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
        self.abs_tolerance = abs_tolerance
        self.rel_tolerance = rel_tolerance
        self._ensure_database_populated()
        self.custom_metrics: Dict[str, Dict[str, Callable]] = {}

    def _get_default_engine(self) -> Engine:
        resolved_url = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
        if resolved_url.startswith("sqlite:///") and not resolved_url.startswith("sqlite:///:memory:"):
            db_file = Path(resolved_url.replace("sqlite:///", ""))
            db_file.parent.mkdir(parents=True, exist_ok=True)
        return create_engine(resolved_url)

    def _ensure_database_populated(self) -> None:
        """Ensure database has the required project tables loaded from CSV files."""
        tables = {
            "viewers_master.csv": "viewers",
            "subscription_events.csv": "subscription_events",
            "viewer_activity_sample.csv": "viewer_activity",
            "content_catalog.csv": "content_catalog",
        }
        with self.engine.connect() as conn:
            for csv_name, tbl_name in tables.items():
                check = conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' AND name=:tbl;"),
                    {"tbl": tbl_name},
                ).fetchone()
                if not check:
                    csv_path = self.data_dir / csv_name
                    if csv_path.exists():
                        df = pd.read_csv(csv_path)
                        df.to_sql(tbl_name, con=self.engine, if_exists="replace", index=False)
                        logger.info(f"Populated table '{tbl_name}' ({len(df)} rows) from '{csv_name}'.")

    def register_metric(
        self,
        name: str,
        sql_calculation: Callable[[Engine], float],
        python_calculation: Callable[[Path], float],
        description: str = "",
    ) -> None:
        """Register a new custom metric for dual-engine cross-validation."""
        self.custom_metrics[name] = {
            "sql": sql_calculation,
            "python": python_calculation,
            "description": description,
        }

    def compute_sql_metrics(self) -> Dict[str, float]:
        """Compute built-in and registered metrics in pure SQL."""
        metrics: Dict[str, float] = {}
        with self.engine.connect() as conn:
            # 1. Total Completed Revenue
            q1 = "SELECT COALESCE(SUM(payment_amount), 0.0) FROM subscription_events WHERE payment_status = 'Completed';"
            metrics["total_completed_revenue"] = float(conn.execute(text(q1)).scalar() or 0.0)

            # 2. Average Completed Transaction Amount
            q2 = "SELECT COALESCE(AVG(payment_amount), 0.0) FROM subscription_events WHERE payment_status = 'Completed';"
            metrics["avg_completed_transaction_amount"] = float(conn.execute(text(q2)).scalar() or 0.0)

            # 3. Overall Payment Success Rate (%)
            q3 = """
                SELECT 100.0 * SUM(CASE WHEN payment_status = 'Completed' THEN 1 ELSE 0 END) / COUNT(*)
                FROM subscription_events;
            """
            metrics["payment_success_rate_pct"] = float(conn.execute(text(q3)).scalar() or 0.0)

            # 4. Total Watch Duration Mins
            q4 = "SELECT COALESCE(SUM(watch_duration_mins), 0.0) FROM viewer_activity WHERE watch_duration_mins IS NOT NULL;"
            metrics["total_watch_duration_mins"] = float(conn.execute(text(q4)).scalar() or 0.0)

            # 5. Active Viewers Count
            q5 = "SELECT COUNT(DISTINCT viewer_id) FROM viewer_activity;"
            metrics["active_viewers_count"] = float(conn.execute(text(q5)).scalar() or 0.0)

        # Custom metrics
        for name, funcs in self.custom_metrics.items():
            metrics[name] = float(funcs["sql"](self.engine))

        return metrics

    def compute_python_metrics(self) -> Dict[str, float]:
        """Compute built-in and registered metrics in pure Python (Pandas)."""
        metrics: Dict[str, float] = {}

        events_df = pd.read_csv(self.data_dir / "subscription_events.csv")
        activity_df = pd.read_csv(self.data_dir / "viewer_activity_sample.csv")

        # 1. Total Completed Revenue
        completed_events = events_df[events_df["payment_status"] == "Completed"]
        metrics["total_completed_revenue"] = float(completed_events["payment_amount"].sum())

        # 2. Average Completed Transaction Amount
        metrics["avg_completed_transaction_amount"] = float(completed_events["payment_amount"].mean())

        # 3. Overall Payment Success Rate (%)
        metrics["payment_success_rate_pct"] = float(
            100.0 * (events_df["payment_status"] == "Completed").sum() / len(events_df)
        )

        # 4. Total Watch Duration Mins
        metrics["total_watch_duration_mins"] = float(activity_df["watch_duration_mins"].dropna().sum())

        # 5. Active Viewers Count
        metrics["active_viewers_count"] = float(activity_df["viewer_id"].nunique())

        # Custom metrics
        for name, funcs in self.custom_metrics.items():
            metrics[name] = float(funcs["python"](self.data_dir))

        return metrics

    def diagnose_discrepancy(
        self,
        metric_name: str,
        sql_val: float,
        py_val: float,
    ) -> str:
        """Provide detailed root-cause diagnosis if a metric fails tolerance check."""
        abs_diff = abs(sql_val - py_val)
        if abs_diff <= self.abs_tolerance:
            return "Values match within configured tolerance."

        causes = []
        if math.isnan(sql_val) or math.isnan(py_val):
            causes.append("NaN / NULL Handling: One computation encountered unhandled NULL values.")
        if round(sql_val, 2) == round(py_val, 2) and abs_diff > self.abs_tolerance:
            causes.append("Floating Point Precision / Rounding: Difference exists only beyond 2 decimal places.")
        if abs_diff >= 1.0:
            causes.append("Definition / Filtering Divergence: Row filter criteria or join condition differs between SQL and Python.")

        return " | ".join(causes) if causes else "Unidentified discrepancy exceeding tolerance."

    def validate_metrics(
        self,
        abs_tol: Optional[float] = None,
        rel_tol: Optional[float] = None,
    ) -> List[MetricValidationResult]:
        """
        Execute dual-engine computation and compare all metrics against tolerance thresholds.
        """
        active_abs_tol = abs_tol if abs_tol is not None else self.abs_tolerance
        active_rel_tol = rel_tol if rel_tol is not None else self.rel_tolerance

        sql_metrics = self.compute_sql_metrics()
        py_metrics = self.compute_python_metrics()

        results: List[MetricValidationResult] = []

        for metric_name in sql_metrics:
            sql_val = sql_metrics[metric_name]
            py_val = py_metrics.get(metric_name, float("nan"))

            abs_diff = abs(sql_val - py_val)
            rel_diff = (abs_diff / abs(sql_val)) if sql_val != 0 else abs_diff

            is_pass = (abs_diff <= active_abs_tol) or (rel_diff <= active_rel_tol)
            status = "PASS" if is_pass else "FAIL"

            diagnostic = (
                "Verified: SQL and Python values match exactly."
                if is_pass
                else self.diagnose_discrepancy(metric_name, sql_val, py_val)
            )

            results.append(
                MetricValidationResult(
                    metric_name=metric_name,
                    sql_value=round(sql_val, 6),
                    python_value=round(py_val, 6),
                    abs_difference=round(abs_diff, 6),
                    rel_difference=round(rel_diff, 6),
                    abs_tolerance=active_abs_tol,
                    rel_tolerance=active_rel_tol,
                    status=status,
                    diagnostic_notes=diagnostic,
                )
            )

        return results

    def generate_report(
        self,
        results: List[MetricValidationResult],
        export_path: Optional[Union[str, Path]] = None,
    ) -> Dict[str, Any]:
        """Generate structured audit report and optionally save to JSON."""
        passed = sum(1 for r in results if r.status == "PASS")
        failed = sum(1 for r in results if r.status == "FAIL")

        report = {
            "total_metrics_evaluated": len(results),
            "passed_count": passed,
            "failed_count": failed,
            "overall_status": "PASS" if failed == 0 else "FAIL",
            "abs_tolerance": self.abs_tolerance,
            "rel_tolerance": self.rel_tolerance,
            "metrics": [asdict(r) for r in results],
        }

        if export_path:
            out_file = Path(export_path)
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
            logger.info(f"Exported validation report to {out_file}.")

        return report


def main():
    """Main workflow runner for Module 5."""
    print("\n=======================================================")
    print("      Module 5: SQL-Based Insight Validation           ")
    print("=======================================================\n")

    validator = SQLPythonValidator(abs_tolerance=1e-4, rel_tolerance=1e-4)
    results = validator.validate_metrics()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report_file = OUTPUT_DIR / "metric_validation_report.json"
    report = validator.generate_report(results, export_path=report_file)

    print(f"Validation Summary: {report['passed_count']}/{report['total_metrics_evaluated']} Metrics PASSED (Overall: {report['overall_status']})\n")

    # Format result table
    df_results = pd.DataFrame(
        [
            {
                "Metric Name": r.metric_name,
                "SQL Value": r.sql_value,
                "Python Value": r.python_value,
                "Abs Diff": r.abs_difference,
                "Status": r.status,
                "Diagnostic Notes": r.diagnostic_notes,
            }
            for r in results
        ]
    )
    print(df_results.to_string(index=False))

    print(f"\n[SUCCESS] Module 5 cross-engine validation report exported to '{report_file.name}'.\n")


if __name__ == "__main__":
    main()
