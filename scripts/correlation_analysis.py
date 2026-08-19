"""Analyse feature relationships with Pearson and Spearman correlations."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


EXPECTED_FEATURES = [
    "engagement",
    "transactions_per_month",
    "support_tickets",
    "churn",
]


def load_correlation_data(filepath):
    """Load the numeric feature data required for correlation analysis.

    Input: CSV filepath containing EXPECTED_FEATURES.
    Output: DataFrame restricted to the expected numeric analysis columns.
    Assumption: Rows with missing values are removed before correlation.
    """
    frame = pd.read_csv(filepath)
    missing = set(EXPECTED_FEATURES) - set(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    # Correlation requires numeric values, so fail clearly on non-numeric input.
    features = frame[EXPECTED_FEATURES].apply(pd.to_numeric, errors="coerce").dropna()
    if len(features) < 3:
        raise ValueError("At least three complete rows are required for correlation.")
    return features


def calculate_correlations(df):
    """Compute Pearson, Spearman, strong pairs, and selected features.

    Input: DataFrame with engagement, transaction frequency, support tickets, and churn.
    Output: Dictionary containing both correlation matrices and feature-selection results.
    Assumption: Absolute Pearson correlation above 0.7 indicates a strong relationship.
    """
    # Pearson captures linear relationships; Spearman captures monotonic relationships.
    pearson_corr = df.corr(method="pearson")
    spearman_corr = df.corr(method="spearman")
    comparison = pd.DataFrame(
        {"pearson": pearson_corr["churn"], "spearman": spearman_corr["churn"]}
    )

    # Flatten the matrix, remove self-correlations, and deduplicate mirrored pairs.
    corr_flat = pearson_corr.where(~pd.DataFrame(
        [[row >= column for column in pearson_corr.columns] for row in pearson_corr.columns],
        index=pearson_corr.index,
        columns=pearson_corr.columns,
    )).stack()
    strong_pairs = corr_flat[corr_flat.abs() > 0.7].sort_values(ascending=False)
    strong_pairs = strong_pairs[strong_pairs != 1.0].head(10)

    # Keep the more interpretable transaction-frequency feature instead of redundant engagement.
    selected = df[["engagement", "transactions_per_month", "support_tickets", "churn"]].drop(
        columns="engagement"
    )
    return {
        "pearson": pearson_corr,
        "spearman": spearman_corr,
        "comparison": comparison,
        "strong_pairs": strong_pairs,
        "selected_features": selected,
    }


def create_heatmap(correlation, output_path):
    """Save an annotated Pearson correlation heatmap as a PNG file."""
    # A centered diverging palette makes positive and negative relationships readable.
    figure, axis = plt.subplots(figsize=(12, 10))
    sns.heatmap(correlation, annot=True, cmap="coolwarm", center=0, ax=axis, vmin=-1, vmax=1)
    axis.set_title("Feature Correlation Matrix")
    figure.tight_layout()
    figure.savefig(output_path, dpi=150)
    plt.close(figure)


def build_business_interpretation(correlation):
    """Translate strong relationships into cautious, non-causal business guidance."""
    support_churn = float(correlation.loc["support_tickets", "churn"])
    return {
        "support_tickets <-> churn": {
            "correlation": support_churn,
            "possible_directions": [
                "support_tickets -> churn (customer gives up after contacting support)",
                "churn -> support_tickets (unhappy customers contact support before leaving)",
                "customer_pain -> both (underlying issue causes both)",
            ],
            "data_indicates": "Correlation alone cannot establish causation; customer pain may confound both measures.",
            "action": "Focus on reducing customer pain and improving support outcomes, not blocking tickets.",
        }
    }


def run_analysis(input_path, output_directory):
    """Run correlation analysis and save all requested outputs."""
    output_directory.mkdir(parents=True, exist_ok=True)
    df = load_correlation_data(input_path)
    results = calculate_correlations(df)
    heatmap_path = output_directory / "correlation_heatmap.png"
    create_heatmap(results["pearson"], heatmap_path)
    interpretation = build_business_interpretation(results["pearson"])

    # Convert Pandas objects to JSON-safe dictionaries for a portable report.
    report = {
        "pearson": results["pearson"].round(4).to_dict(),
        "spearman": results["spearman"].round(4).to_dict(),
        "comparison_to_churn": results["comparison"].round(4).to_dict(),
        "strong_pairs": {str(key): float(value) for key, value in results["strong_pairs"].items()},
        "selected_features": list(results["selected_features"].columns),
        "business_interpretation": interpretation,
        "heatmap": str(heatmap_path),
    }
    with (output_directory / "correlation_analysis.json").open("w", encoding="utf-8") as file_handle:
        json.dump(report, file_handle, indent=2)
    results["report"] = report
    return results


if __name__ == "__main__":
    # Resolve paths from the repository root for consistent command-line execution.
    root = Path(__file__).resolve().parents[1]
    results = run_analysis(root / "data/raw/correlation_sample.csv", root / "output")
    print("Pearson vs Spearman correlation with churn:")
    print(results["comparison"])
    print("\nStrongly correlated pairs:")
    print(results["strong_pairs"])
    print("\nSelected features:")
    print(list(results["selected_features"].columns))
    print("\nBusiness interpretation:")
    print(json.dumps(results["report"]["business_interpretation"], indent=2))
    print("Correlation analysis saved to output/")