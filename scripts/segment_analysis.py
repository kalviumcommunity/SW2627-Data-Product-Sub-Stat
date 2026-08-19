"""Summarise customer segments, products, revenue, and churn outcomes."""

import json
from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = [
    "customer_id",
    "customer_type",
    "product",
    "revenue",
    "support_tickets",
    "churn",
]


def load_segment_data(filepath):
    """Load and validate the customer-level data used for segmentation.

    Input: CSV filepath containing REQUIRED_COLUMNS.
    Output: DataFrame with numeric measures converted to numeric types.
    Assumption: ``churn`` is encoded as 0/1 and each row represents one customer.
    """
    frame = pd.read_csv(filepath)
    missing = set(REQUIRED_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    # Keep only complete records so aggregation denominators remain explicit.
    frame = frame[REQUIRED_COLUMNS].copy()
    for column in ["customer_id", "revenue", "support_tickets", "churn"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=REQUIRED_COLUMNS)
    if frame.empty:
        raise ValueError("No complete customer records are available for analysis.")
    return frame


def calculate_segment_metrics(df):
    """Calculate segment summaries, product cross-tabs, rankings, and insights.

    Input: Validated customer-level DataFrame.
    Output: Dictionary of DataFrames for each requested analysis view.
    Assumption: A churn mean is interpreted as the segment churn rate.
    """
    # Single-level groupby with multiple business aggregations.
    segment_metrics = df.groupby("customer_type").agg(
        {
            "churn": "mean",
            "revenue": "sum",
            "customer_id": "count",
            "support_tickets": "mean",
        }
    )
    segment_metrics.columns = [
        "churn_rate",
        "total_revenue",
        "customer_count",
        "avg_support_tickets",
    ]

    # Add rank and revenue contribution so the worst and most valuable groups are visible.
    segment_metrics["churn_rank"] = segment_metrics["churn_rate"].rank(
        ascending=False, method="dense"
    )
    segment_metrics["revenue_contribution"] = (
        segment_metrics["total_revenue"] / segment_metrics["total_revenue"].sum() * 100
    )
    worst_first = segment_metrics.sort_values("churn_rate", ascending=False)

    # Aggregate two dimensions simultaneously, then expose products as columns.
    product_segment = df.groupby(["customer_type", "product"]).agg(
        total_revenue=("revenue", "sum"), customer_count=("customer_id", "count")
    )
    product_segment_pivot = product_segment.unstack(fill_value=0)

    # A direct pivot table provides the requested customer-type by product revenue view.
    revenue_pivot = pd.pivot_table(
        df, values="revenue", index="customer_type", columns="product", aggfunc="sum", fill_value=0
    )

    # Turn metrics into concise action recommendations for downstream users.
    insights = []
    for segment, row in segment_metrics.iterrows():
        if row["churn_rate"] > 0.10:
            action = "HIGH PRIORITY: Churn above 10%. Investigate pain points."
        elif row["churn_rate"] < 0.02:
            action = "Healthy. Maintain current service level."
        else:
            action = "Monitor. No immediate action needed."
        insights.append(
            {
                "segment": segment,
                "customer_count": int(row["customer_count"]),
                "churn_rate": f"{row['churn_rate']:.1%}",
                "total_revenue": f"${row['total_revenue']:.0f}",
                "revenue_contribution": f"{row['revenue_contribution']:.1f}%",
                "action": action,
            }
        )
    insights_df = pd.DataFrame(insights)

    return {
        "segment_metrics": segment_metrics,
        "worst_first": worst_first,
        "product_segment": product_segment,
        "product_segment_pivot": product_segment_pivot,
        "revenue_pivot": revenue_pivot,
        "insights": insights_df,
    }


def save_segment_outputs(results, output_directory):
    """Save segment insights and machine-readable aggregation results.

    Input: Results returned by calculate_segment_metrics and an output directory.
    Output: CSV and JSON files containing the requested analysis results.
    Assumption: Pandas and JSON can write to the supplied directory.
    """
    output_directory.mkdir(parents=True, exist_ok=True)
    results["insights"].to_csv(output_directory / "segment_insights.csv", index=False)

    # Preserve the key summary tables in JSON for easy reuse by dashboards or reports.
    report = {
        "segment_metrics": results["segment_metrics"].round(4).reset_index().to_dict("records"),
        "worst_first": results["worst_first"].round(4).reset_index().to_dict("records"),
        "product_revenue_pivot": results["revenue_pivot"].round(2).reset_index().to_dict("records"),
        "insights": results["insights"].to_dict("records"),
    }
    with (output_directory / "segment_analysis.json").open("w", encoding="utf-8") as file_handle:
        json.dump(report, file_handle, indent=2)


if __name__ == "__main__":
    # Resolve paths from the repository root for reliable command-line execution.
    repository_root = Path(__file__).resolve().parents[1]
    data = load_segment_data(repository_root / "data/raw/segment_sample.csv")
    analysis = calculate_segment_metrics(data)
    save_segment_outputs(analysis, repository_root / "output")

    print("Segment metrics:")
    print(analysis["segment_metrics"])
    print("\nProduct revenue pivot:")
    print(analysis["revenue_pivot"])
    print("\nActionable segment insights:")
    print(analysis["insights"].to_string(index=False))
    print("\nSegment analysis saved to output/")