"""Analyse revenue distribution shape and compare customer value segments."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from scipy import stats


def load_revenue_data(filepath):
    """Load a CSV and return a clean numeric revenue Series.

    Input: filepath to a CSV containing ``revenue`` or ``transaction_amount``.
    Output: A positive, non-null Pandas Series named ``revenue``.
    Assumption: Transaction amounts are the repository's revenue measure when
    a dedicated revenue column is not available.
    """
    # Read the existing intake fixture without changing it on disk.
    frame = pd.read_csv(filepath)
    source_column = "revenue" if "revenue" in frame.columns else "transaction_amount"
    if source_column not in frame.columns:
        raise ValueError("Input CSV must contain 'revenue' or 'transaction_amount'.")

    # Convert malformed values to missing values, then exclude unusable records.
    revenue = pd.to_numeric(frame[source_column], errors="coerce").dropna()
    revenue = revenue[revenue >= 0].rename("revenue")
    if len(revenue) < 2:
        raise ValueError("At least two non-negative revenue values are required.")
    return revenue


def calculate_distribution_metrics(revenue):
    """Calculate shape metrics, percentiles, and segment summaries.

    Input: Numeric, non-negative revenue Series.
    Output: Dictionary containing descriptive statistics and business labels.
    Assumption: SciPy's unbiased skewness and Pearson kurtosis are appropriate
    for this exploratory analysis.
    """
    # Compute distribution shape using the requested SciPy functions.
    skewness = float(stats.skew(revenue))
    kurtosis = float(stats.kurtosis(revenue))
    percentiles = revenue.quantile([0.25, 0.5, 0.75, 0.9, 0.95, 0.99])
    high_value = revenue[revenue > percentiles.loc[0.75]]
    low_value = revenue[revenue < percentiles.loc[0.25]]

    # Use a safe fallback for tiny samples where strict quartile filters empty.
    high_summary = _segment_summary(high_value if not high_value.empty else revenue)
    low_summary = _segment_summary(low_value if not low_value.empty else revenue)
    return {
        "skewness": skewness,
        "kurtosis": kurtosis,
        "describe": {key: float(value) for key, value in revenue.describe().items()},
        "percentiles": {str(key): float(value) for key, value in percentiles.items()},
        "high_value": high_summary,
        "low_value": low_summary,
        "interpretation": {
            "shape": "Highly right-skewed" if skewness > 1 else "Moderate",
            "tails": "Fat tails (outliers)" if kurtosis > 3 else "Normal",
            "business_action": (
                "Segment into small/enterprise for different strategies"
                if skewness > 1
                else "Uniform strategy"
            ),
        },
    }


def _segment_summary(segment):
    """Return mean, median, and count for one revenue segment."""
    return {
        "count": int(segment.size),
        "mean": float(segment.mean()),
        "median": float(segment.median()),
    }


def create_distribution_plots(revenue, output_directory):
    """Save overall and high/low customer revenue distribution plots.

    Input: Numeric revenue Series and an output directory.
    Output: Dictionary of generated PNG paths.
    Assumption: Matplotlib can write PNG files to the output directory.
    """
    output_directory.mkdir(parents=True, exist_ok=True)
    quartiles = revenue.quantile([0.25, 0.75])
    high_value = revenue[revenue > quartiles.loc[0.75]]
    low_value = revenue[revenue < quartiles.loc[0.25]]

    # Show the full distribution through complementary histogram and KDE views.
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    axes[0].hist(revenue, bins=min(50, max(5, revenue.nunique())), edgecolor="black")
    axes[0].set_title("Revenue Distribution (Histogram)")
    axes[0].set_xlabel("Revenue")
    axes[0].set_ylabel("Customers")
    revenue.plot(kind="density", ax=axes[1])
    axes[1].set_title("Revenue Distribution (KDE)")
    axes[1].set_xlabel("Revenue")
    fig.tight_layout()
    overall_path = output_directory / "revenue_distribution.png"
    fig.savefig(overall_path, dpi=150)
    plt.close(fig)

    # Compare the upper and lower quartile populations on one shared chart.
    fig, axis = plt.subplots(figsize=(8, 5))
    axis.hist(high_value, bins=max(1, min(30, high_value.nunique())), alpha=0.7, label="High-Value")
    axis.hist(low_value, bins=max(1, min(30, low_value.nunique())), alpha=0.7, label="Low-Value")
    axis.legend()
    axis.set_title("Revenue: High vs Low Value Customers")
    axis.set_xlabel("Revenue")
    axis.set_ylabel("Customers")
    fig.tight_layout()
    segment_path = output_directory / "revenue_segments.png"
    fig.savefig(segment_path, dpi=150)
    plt.close(fig)
    return {"distribution_plot": str(overall_path), "segment_plot": str(segment_path)}


def run_analysis(input_path, output_directory):
    """Run analysis, save plots and a JSON summary, and return the metrics."""
    # Keep ingestion, computation, visualisation, and persistence independently testable.
    revenue = load_revenue_data(input_path)
    metrics = calculate_distribution_metrics(revenue)
    plots = create_distribution_plots(revenue, output_directory)
    metrics["plots"] = plots
    summary_path = output_directory / "revenue_distribution_summary.json"
    with summary_path.open("w", encoding="utf-8") as file_handle:
        json.dump(metrics, file_handle, indent=2)
    return metrics


if __name__ == "__main__":
    # Resolve paths from the repository root so the command works from any directory.
    repository_root = Path(__file__).resolve().parents[1]
    result = run_analysis(
        repository_root / "data/raw/sample.csv", repository_root / "output"
    )
    print(f"Skewness: {result['skewness']:.2f}")
    print(f"Kurtosis: {result['kurtosis']:.2f}")
    print(result["interpretation"])
    print(f"High-value: mean={result['high_value']['mean']:.0f}, median={result['high_value']['median']:.0f}")
    print(f"Low-value: mean={result['low_value']['mean']:.0f}, median={result['low_value']['median']:.0f}")
    print("Plots and summary saved to output/")