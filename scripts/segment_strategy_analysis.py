"""Compute business-facing segment metrics, rankings, and visual comparisons."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


REQUIRED_COLUMNS = [
    "customer_id",
    "customer_type",
    "lifetime_value",
    "churn",
    "support_tickets",
    "retention_days",
]


def load_segment_profile(filepath):
    """Load and validate profile data used for strategy segmentation.

    Input: CSV path containing customer_type and required numeric metrics.
    Output: Clean DataFrame with complete rows and numeric metric columns.
    Assumption: churn is a binary 0/1 outcome per customer.
    """
    df = pd.read_csv(filepath)
    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    # Convert analysis columns to numeric and remove incomplete records.
    for column in ["customer_id", "lifetime_value", "churn", "support_tickets", "retention_days"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df = df.dropna(subset=REQUIRED_COLUMNS)
    if df["customer_type"].nunique() < 3:
        raise ValueError("At least three distinct segments are required.")
    return df


def compute_segment_metrics(df):
    """Aggregate core metrics and rankings by customer segment.

    Input: Clean customer profile DataFrame.
    Output: Segment metrics table with ranks and contribution percentages.
    Assumption: mean churn within a segment is interpreted as churn rate.
    """
    segment_metrics = df.groupby("customer_type").agg(
        {
            "lifetime_value": "mean",
            "churn": "mean",
            "support_tickets": "mean",
            "retention_days": "mean",
            "customer_id": "count",
        }
    )
    segment_metrics.columns = [
        "avg_ltv",
        "churn_rate",
        "avg_tickets",
        "avg_retention",
        "count",
    ]

    # Add relative context through rank columns for value and churn performance.
    segment_metrics["ltv_rank"] = segment_metrics["avg_ltv"].rank(ascending=False, method="dense")
    segment_metrics["churn_rank"] = segment_metrics["churn_rate"].rank(ascending=True, method="dense")
    segment_metrics["segment_share_pct"] = segment_metrics["count"] / segment_metrics["count"].sum() * 100
    return segment_metrics.sort_values("avg_ltv", ascending=False)


def format_summary(segment_metrics):
    """Create a readable table with absolute values and rankings."""
    summary = segment_metrics.copy()
    summary["avg_ltv_display"] = summary["avg_ltv"].map(lambda value: f"${value:,.0f}")
    summary["churn_rate_display"] = summary["churn_rate"].map(lambda value: f"{value:.1%}")
    summary["avg_tickets_display"] = summary["avg_tickets"].map(lambda value: f"{value:.2f}")
    summary["avg_retention_display"] = summary["avg_retention"].map(lambda value: f"{value:.0f} days")
    summary["segment_share_display"] = summary["segment_share_pct"].map(lambda value: f"{value:.1f}%")
    return summary[
        [
            "avg_ltv",
            "avg_ltv_display",
            "ltv_rank",
            "churn_rate",
            "churn_rate_display",
            "churn_rank",
            "avg_tickets_display",
            "avg_retention_display",
            "count",
            "segment_share_display",
        ]
    ]


def create_heatmap(segment_metrics, output_path):
    """Generate a heatmap comparing key segment metrics."""
    # Plot core metrics with annotations for rapid cross-segment comparison.
    plt.figure(figsize=(10, 6))
    sns.heatmap(
        segment_metrics[["avg_ltv", "churn_rate", "avg_tickets", "avg_retention"]],
        annot=True,
        fmt=".2f",
        cmap="RdYlGn",
        cbar_kws={"label": "Value"},
    )
    plt.title("Segment Comparison Heatmap")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def build_performer_insights(segment_metrics):
    """Return top-value, high-churn, and best-retention findings."""
    top_segment = segment_metrics["avg_ltv"].idxmax()
    high_churn = segment_metrics["churn_rate"].idxmax()
    best_retention = segment_metrics["avg_retention"].idxmax()
    return {
        "highest_value_segment": {
            "name": top_segment,
            "avg_ltv": float(segment_metrics.loc[top_segment, "avg_ltv"]),
        },
        "highest_churn_segment": {
            "name": high_churn,
            "churn_rate": float(segment_metrics.loc[high_churn, "churn_rate"]),
        },
        "best_retention_segment": {
            "name": best_retention,
            "avg_retention": float(segment_metrics.loc[best_retention, "avg_retention"]),
        },
    }


def build_business_summary(segment_metrics):
    """Create business-facing strategy text for each segment."""
    lines = ["SEGMENT STRATEGY SUMMARY:"]
    for segment in segment_metrics.index:
        row = segment_metrics.loc[segment]
        action = (
            "Maintain premium support and proactive retention programs"
            if row["avg_ltv"] > 50000 and row["churn_rate"] <= 0.05
            else "Improve onboarding and guided support to reduce churn risk"
            if row["churn_rate"] > 0.10
            else "Scale self-service education while monitoring churn"
        )
        lines.append(
            f"{segment} ({row['segment_share_pct']:.1f}% of base, "
            f"${row['avg_ltv']:,.0f} avg LTV, {row['churn_rate']:.1%} churn):"
        )
        lines.append(f"- Action: {action}")
    return "\n".join(lines)


def save_outputs(summary, insights, business_summary, heatmap_path, output_dir):
    """Persist tabular and narrative segment outputs for review."""
    output_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(output_dir / "segment_summary_metrics.csv")
    with (output_dir / "segment_performer_insights.json").open("w", encoding="utf-8") as handle:
        json.dump(insights, handle, indent=2)
    (output_dir / "segment_strategy_summary.txt").write_text(
        business_summary + "\n", encoding="utf-8"
    )
    with (output_dir / "segment_strategy_report.json").open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "summary_table": summary.reset_index().to_dict("records"),
                "performer_insights": insights,
                "business_summary": business_summary,
                "heatmap": str(heatmap_path),
            },
            handle,
            indent=2,
        )


if __name__ == "__main__":
    # Resolve paths from repository root so script runs consistently from CLI.
    root = Path(__file__).resolve().parents[1]
    input_path = root / "data/raw/segment_profile_sample.csv"
    output_dir = root / "output"
    heatmap_path = output_dir / "segment_heatmap.png"

    data = load_segment_profile(input_path)
    segment_metrics = compute_segment_metrics(data)
    summary = format_summary(segment_metrics)
    create_heatmap(segment_metrics, heatmap_path)
    insights = build_performer_insights(segment_metrics)
    business_summary = build_business_summary(segment_metrics)
    save_outputs(summary, insights, business_summary, heatmap_path, output_dir)

    print(segment_metrics)
    print("\nRanked summary:")
    print(summary[["avg_ltv_display", "ltv_rank", "churn_rate_display", "churn_rank", "count"]])
    print("\nPerformer insights:")
    print(
        f"HIGHEST VALUE: {insights['highest_value_segment']['name']} = "
        f"${insights['highest_value_segment']['avg_ltv']:,.0f}"
    )
    print(
        f"HIGHEST CHURN: {insights['highest_churn_segment']['name']} = "
        f"{insights['highest_churn_segment']['churn_rate']:.1%}"
    )
    print(f"BEST RETENTION: {insights['best_retention_segment']['name']}")
    print("\n" + business_summary)