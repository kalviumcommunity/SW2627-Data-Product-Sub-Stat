"""Reusable KPI calculation and validation functions."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def _resolve_reference_date(df: pd.DataFrame, reference_date: pd.Timestamp | None) -> pd.Timestamp:
    """Return the explicit reference date or infer it from the data."""
    return reference_date if reference_date is not None else df["transaction_date"].max()


def calculate_mau(
    df: pd.DataFrame, days: int = 30, reference_date: pd.Timestamp | None = None
) -> dict:
    """Monthly Active Users: distinct customers active in the last N days."""
    anchor = _resolve_reference_date(df, reference_date)
    cutoff = anchor - pd.Timedelta(days=days)
    value = int(df[df["transaction_date"] >= cutoff]["customer_id"].nunique())
    return {"value": value, "formatted": f"{value:,}"}


def calculate_revenue_per_customer(df: pd.DataFrame) -> dict:
    """Average revenue per unique customer."""
    unique_customers = df["customer_id"].nunique()
    value = float(df["amount"].sum() / unique_customers) if unique_customers else 0.0
    return {"value": value, "formatted": f"${value:,.2f}"}


def calculate_churn_rate(
    df: pd.DataFrame, period_days: int = 30, reference_date: pd.Timestamp | None = None
) -> dict:
    """Customers active in period 1 but not active in period 2."""
    anchor = _resolve_reference_date(df, reference_date)
    period_2_end = anchor
    period_2_start = anchor - pd.Timedelta(days=period_days)
    period_1_end = period_2_start
    period_1_start = period_1_end - pd.Timedelta(days=period_days)

    active_p1 = set(
        df[
            (df["transaction_date"] >= period_1_start)
            & (df["transaction_date"] <= period_1_end)
        ]["customer_id"].unique()
    )
    active_p2 = set(
        df[
            (df["transaction_date"] >= period_2_start)
            & (df["transaction_date"] <= period_2_end)
        ]["customer_id"].unique()
    )
    churned = len([customer for customer in active_p1 if customer not in active_p2])
    value = float(churned / len(active_p1)) if active_p1 else 0.0
    return {"value": value, "formatted": f"{value:.1%}"}


def calculate_payment_success_rate(df: pd.DataFrame) -> dict:
    """Share of transactions with successful payment outcomes."""
    total = len(df)
    successful = int((df["payment_status"].str.lower() == "success").sum())
    value = float(successful / total) if total else 0.0
    return {"value": value, "formatted": f"{value:.1%}"}


def calculate_customer_acquisition_cost(df: pd.DataFrame) -> dict:
    """Average acquisition cost across unique customers."""
    per_customer_cost = df.groupby("customer_id", as_index=False)["acquisition_cost"].first()
    value = float(per_customer_cost["acquisition_cost"].mean()) if not per_customer_cost.empty else 0.0
    return {"value": value, "formatted": f"${value:,.2f}"}


def calculate_total_revenue(df: pd.DataFrame) -> dict:
    """Total revenue value across all observed transactions."""
    value = float(df["amount"].sum())
    return {"value": value, "formatted": f"${value:,.2f}"}


def compute_all_kpis(df: pd.DataFrame, reference_date: pd.Timestamp | None = None) -> dict:
    """Compute all KPI values from one DataFrame for reuse in reporting."""
    return {
        "monthly_active_users": calculate_mau(df, days=30, reference_date=reference_date),
        "revenue_per_customer": calculate_revenue_per_customer(df),
        "churn_rate": calculate_churn_rate(df, period_days=30, reference_date=reference_date),
        "payment_success_rate": calculate_payment_success_rate(df),
        "customer_acquisition_cost": calculate_customer_acquisition_cost(df),
        "total_revenue": calculate_total_revenue(df),
    }


def validate_against_targets(kpis: dict, targets: dict) -> pd.DataFrame:
    """Compare KPI numeric values against min/max targets and label pass/alert."""
    rows = []
    for kpi_name, target_range in targets.items():
        actual = float(kpis[kpi_name]["value"])
        min_val = float(target_range["min"])
        max_val = float(target_range["max"])
        status = "PASS" if min_val <= actual <= max_val else "ALERT"
        rows.append(
            {
                "kpi": kpi_name,
                "actual": actual,
                "formatted": kpis[kpi_name]["formatted"],
                "target_min": min_val,
                "target_max": max_val,
                "status": status,
            }
        )
    return pd.DataFrame(rows)


def decompose_total_revenue(df: pd.DataFrame) -> dict:
    """Break total revenue into segment and product sub-components."""
    total_revenue = float(df["amount"].sum())
    by_segment = df.groupby("customer_type")["amount"].sum().sort_values(ascending=False)
    by_product = df.groupby("product")["amount"].sum().sort_values(ascending=False)
    return {
        "total_revenue": total_revenue,
        "revenue_by_segment": by_segment.to_dict(),
        "revenue_by_product": by_product.to_dict(),
        "segment_sum_matches_total": abs(float(by_segment.sum()) - total_revenue) < 1e-9,
        "product_sum_matches_total": abs(float(by_product.sum()) - total_revenue) < 1e-9,
    }


def load_transactions(filepath: Path) -> pd.DataFrame:
    """Load KPI transaction data and normalize expected data types."""
    df = pd.read_csv(filepath, parse_dates=["transaction_date"])
    required = {
        "customer_id",
        "transaction_date",
        "amount",
        "customer_type",
        "product",
        "payment_status",
        "acquisition_cost",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["acquisition_cost"] = pd.to_numeric(df["acquisition_cost"], errors="coerce")
    df = df.dropna(subset=["customer_id", "transaction_date", "amount", "acquisition_cost"])
    return df


def run_kpi_workflow(
    transactions_path: Path, targets_path: Path, output_dir: Path
) -> dict:
    """Run KPI computation, validation, and decomposition with saved artifacts."""
    output_dir.mkdir(parents=True, exist_ok=True)
    df = load_transactions(transactions_path)
    with targets_path.open("r", encoding="utf-8") as handle:
        targets = json.load(handle)

    reference_date = df["transaction_date"].max()
    kpis = compute_all_kpis(df, reference_date=reference_date)
    validation = validate_against_targets(kpis, targets)
    decomposition = decompose_total_revenue(df)

    validation.to_csv(output_dir / "kpi_validation_report.csv", index=False)
    with (output_dir / "kpi_current_values.json").open("w", encoding="utf-8") as handle:
        json.dump(kpis, handle, indent=2)
    with (output_dir / "kpi_decomposition.json").open("w", encoding="utf-8") as handle:
        json.dump(decomposition, handle, indent=2)

    failures = validation[validation["status"] == "ALERT"]
    summary_line = (
        f"ALERT: {len(failures)} KPI(s) outside target range"
        if not failures.empty
        else f"PASS: all {len(validation)} KPI(s) within target range"
    )
    return {
        "kpis": kpis,
        "validation": validation,
        "decomposition": decomposition,
        "summary": summary_line,
    }


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    result = run_kpi_workflow(
        root / "data/raw/kpi_transactions_sample.csv",
        root / "kpis/kpi_validation_targets.json",
        root / "output",
    )

    print("Current KPIs:")
    for name, payload in result["kpis"].items():
        print(f"- {name}: {payload['formatted']}")

    print("\nValidation report:")
    print(result["validation"])
    print(f"\n{result['summary']}")

    decomp = result["decomposition"]
    print("\nKPI DECOMPOSITION: Total Revenue")
    print(f"Top-level: ${decomp['total_revenue']:,.0f}")
    print("By Segment:")
    for segment, value in decomp["revenue_by_segment"].items():
        print(f"  {segment}: ${value:,.0f}")
    print("By Product:")
    for product, value in decomp["revenue_by_product"].items():
        print(f"  {product}: ${value:,.0f}")