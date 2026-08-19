"""Analyse daily revenue with resampling, rolling windows, and trend metrics."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def load_time_series(filepath):
    """Load daily revenue data indexed by date.

    Input: CSV containing date, revenue, and orders columns.
    Output: DataFrame sorted by a DatetimeIndex.
    Assumption: Each row represents one calendar day.
    """
    frame = pd.read_csv(filepath, parse_dates=["date"])
    required = {"date", "revenue", "orders"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    frame["revenue"] = pd.to_numeric(frame["revenue"], errors="coerce")
    frame["orders"] = pd.to_numeric(frame["orders"], errors="coerce")
    frame = frame.dropna(subset=["date", "revenue", "orders"]).sort_values("date")
    if len(frame) < 30:
        raise ValueError("At least 30 daily observations are required.")
    return frame.set_index("date")


def calculate_time_metrics(df):
    """Calculate weekly/monthly summaries, rolling averages, MoM change, and totals.

    Input: Daily DataFrame indexed by date with revenue and orders columns.
    Output: Dictionary containing time-series metrics and trend interpretation.
    Assumption: Calendar month-end buckets are used for monthly comparisons.
    """
    # Aggregate the same daily data at two time scales with different functions.
    weekly = pd.DataFrame(
        {
            "revenue_sum": df["revenue"].resample("W").sum(),
            "orders_count": df["orders"].resample("W").count(),
            "revenue_mean": df["revenue"].resample("W").mean(),
        }
    )
    monthly = pd.DataFrame(
        {
            "revenue_sum": df["revenue"].resample("ME").sum(),
            "orders_count": df["orders"].resample("ME").count(),
            "revenue_mean": df["revenue"].resample("ME").mean(),
        }
    )

    # Smooth daily noise with the requested seven- and thirty-day windows.
    enriched = df.copy()
    enriched["revenue_ma7"] = enriched["revenue"].rolling(window=7).mean()
    enriched["revenue_ma30"] = enriched["revenue"].rolling(window=30).mean()
    monthly["mom_change_pct"] = monthly["revenue_sum"].pct_change() * 100
    growth_months = monthly[monthly["mom_change_pct"] > 0]
    decline_months = monthly[monthly["mom_change_pct"] < 0]

    # Compare the endpoints of the latest complete rolling window for direction.
    recent_ma30 = enriched["revenue_ma30"].dropna().tail(30)
    change = float(recent_ma30.iloc[-1] - recent_ma30.iloc[0])
    magnitude = float(change / recent_ma30.iloc[0] * 100)
    direction = "up" if change > 0 else "down" if change < 0 else "stable"
    total_revenue = float(enriched["revenue"].cumsum().iloc[-1])
    return {
        "data": enriched,
        "weekly": weekly,
        "monthly": monthly,
        "growth_months": growth_months,
        "decline_months": decline_months,
        "total_revenue": total_revenue,
        "trend_direction": direction,
        "trend_magnitude_pct": magnitude,
        "interpretation": (
            "Accelerating growth - maintain current strategy"
            if direction == "up"
            else "Declining momentum - investigate causes"
            if direction == "down"
            else "Stable momentum - maintain and monitor current strategy"
        ),
    }


def create_plots(metrics, output_directory):
    """Save rolling-average and cumulative-revenue visualisations.

    Input: Dictionary returned by calculate_time_metrics and an output directory.
    Output: Dictionary of generated PNG paths.
    Assumption: Matplotlib can write image files to the output directory.
    """
    output_directory.mkdir(parents=True, exist_ok=True)
    data = metrics["data"]

    # Plot raw daily noise beside both requested smoothing windows.
    figure, axis = plt.subplots(figsize=(12, 6))
    axis.plot(data.index, data["revenue"], label="Raw", alpha=0.3)
    axis.plot(data.index, data["revenue_ma7"], label="7-day MA")
    axis.plot(data.index, data["revenue_ma30"], label="30-day MA")
    axis.set_title("Daily Revenue with Rolling Averages")
    axis.set_xlabel("Date")
    axis.set_ylabel("Revenue")
    axis.legend()
    figure.tight_layout()
    rolling_path = output_directory / "rolling_avg.png"
    figure.savefig(rolling_path, dpi=150)
    plt.close(figure)

    # Show accumulated revenue, which should never decrease for non-negative input.
    figure, axis = plt.subplots(figsize=(12, 6))
    axis.plot(data.index, data["revenue"].cumsum(), label="Cumulative revenue")
    axis.set_title("Cumulative Revenue Over Time")
    axis.set_xlabel("Date")
    axis.set_ylabel("Cumulative revenue")
    axis.legend()
    figure.tight_layout()
    cumulative_path = output_directory / "cumulative.png"
    figure.savefig(cumulative_path, dpi=150)
    plt.close(figure)
    return {"rolling_plot": str(rolling_path), "cumulative_plot": str(cumulative_path)}


def save_report(metrics, plots, output_path):
    """Save a JSON report with period comparisons and business interpretation."""
    monthly = metrics["monthly"]
    highest_period = monthly["revenue_sum"].idxmax()
    weekly_report = metrics["weekly"].round(2).copy()
    monthly_report = monthly.round(2).copy()
    weekly_report.index = weekly_report.index.strftime("%Y-%m-%d")
    monthly_report.index = monthly_report.index.strftime("%Y-%m-%d")
    report = {
        "weekly": weekly_report.to_dict("index"),
        "monthly": monthly_report.to_dict("index"),
        "highest_revenue_month": str(highest_period.date()),
        "growth_months": [str(index.date()) for index in metrics["growth_months"].index],
        "decline_months": [str(index.date()) for index in metrics["decline_months"].index],
        "total_revenue": metrics["total_revenue"],
        "trend_direction": metrics["trend_direction"],
        "trend_magnitude_pct": metrics["trend_magnitude_pct"],
        "business_interpretation": metrics["interpretation"],
        "plots": plots,
    }
    with output_path.open("w", encoding="utf-8") as file_handle:
        json.dump(report, file_handle, indent=2, default=str)
    return report


if __name__ == "__main__":
    # Resolve paths from the repository root for reliable command-line execution.
    root = Path(__file__).resolve().parents[1]
    metrics = calculate_time_metrics(load_time_series(root / "data/raw/daily_revenue_sample.csv"))
    plots = create_plots(metrics, root / "output")
    report = save_report(metrics, plots, root / "output/time_series_analysis.json")
    print(metrics["weekly"])
    print(metrics["monthly"][["revenue_sum", "mom_change_pct"]])
    print(f"Highest revenue month: {report['highest_revenue_month']}")
    print(f"Growth months: {report['growth_months']}")
    print(f"Decline months: {report['decline_months']}")
    print(f"Total revenue: ${metrics['total_revenue']:,.0f}")
    print(f"Trend: {metrics['trend_direction'].upper()} ({metrics['trend_magnitude_pct']:.1f}%)")
    print(metrics["interpretation"])