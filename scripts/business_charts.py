"""Generate five business chart types with consistent styling and documentation."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd
import seaborn as sns


PALETTE = {
    "primary": "#1f77b4",
    "secondary": "#ff7f0e",
    "success": "#2ca02c",
    "warning": "#d62728",
    "neutral": "#7f7f7f",
}

PRODUCT_COLORS = {
    "Product A": "#1f77b4",
    "Product B": "#ff7f0e",
    "Product C": "#2ca02c",
    "Product D": "#d62728",
}


def _currency_formatter(value, _):
    """Format axis values as compact currency labels."""
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"${value / 1_000:.0f}K"
    return f"${value:.0f}"


def create_or_load_dataset(path: Path) -> pd.DataFrame:
    """Create deterministic order-level sales data if it does not already exist."""
    if path.exists():
        data = pd.read_csv(path, parse_dates=["order_date"])
        return data

    rng = np.random.default_rng(42)
    dates = pd.date_range("2025-09-01", "2026-08-31", freq="D")
    product_lines = ["Product A", "Product B", "Product C", "Product D"]
    base_orders = {"Product A": 9, "Product B": 7, "Product C": 6, "Product D": 4}
    base_amount = {"Product A": 170, "Product B": 145, "Product C": 120, "Product D": 95}

    rows = []
    for date in dates:
        month_factor = 1 + 0.25 * np.sin((date.month - 1) / 12 * 2 * np.pi)
        for product in product_lines:
            # Daily order volume varies by product and season.
            orders_today = int(max(1, rng.poisson(base_orders[product] * month_factor)))
            promo_spike = 1.25 if date.month in [11, 12] and product in ["Product A", "Product B"] else 1.0
            for _ in range(orders_today):
                amount = rng.normal(loc=base_amount[product] * promo_spike, scale=22)
                amount = float(max(20.0, round(amount, 2)))
                marketing_spend = float(
                    max(
                        10.0,
                        rng.normal(
                            loc=amount * (0.22 if product in ["Product C", "Product D"] else 0.17),
                            scale=8,
                        ),
                    )
                )
                rows.append(
                    {
                        "order_date": date,
                        "product_line": product,
                        "order_amount": amount,
                        "marketing_spend": round(marketing_spend, 2),
                    }
                )

    data = pd.DataFrame(rows)
    data.to_csv(path, index=False)
    return data


def chart1_revenue_by_product(data: pd.DataFrame, output_dir: Path) -> dict:
    """Chart 1: Horizontal bar chart for last-quarter revenue by product line."""
    end_date = data["order_date"].max()
    start_date = end_date - pd.Timedelta(days=90)
    recent = data[data["order_date"] >= start_date]
    revenue_by_product = (
        recent.groupby("product_line", as_index=False)["order_amount"].sum()
        .rename(columns={"order_amount": "revenue"})
        .sort_values("revenue", ascending=True)
    )

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(
        revenue_by_product["product_line"],
        revenue_by_product["revenue"],
        color=[PRODUCT_COLORS[name] for name in revenue_by_product["product_line"]],
        label="Revenue",
    )
    ax.set_title("Last-Quarter Revenue by Product Line", fontsize=14, fontweight="bold")
    ax.set_xlabel("Revenue ($)", fontsize=12)
    ax.set_ylabel("Product Line", fontsize=12)
    ax.xaxis.set_major_formatter(FuncFormatter(_currency_formatter))
    ax.legend(loc="lower right", fontsize=10)
    ax.grid(axis="x", alpha=0.25)

    for bar in bars:
        width = bar.get_width()
        ax.text(width * 1.01, bar.get_y() + bar.get_height() / 2, _currency_formatter(width, None), va="center")

    top_row = revenue_by_product.iloc[-1]
    ax.annotate(
        "Top product this quarter",
        xy=(top_row["revenue"], top_row["product_line"]),
        xytext=(top_row["revenue"] * 0.65, top_row["product_line"]),
        arrowprops={"arrowstyle": "->", "color": PALETTE["warning"], "lw": 2},
        bbox={"boxstyle": "round,pad=0.3", "fc": "white", "ec": PALETTE["warning"], "alpha": 0.9},
        fontsize=10,
    )

    out_path = output_dir / "chart1_revenue_by_product.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return {
        "question": "Which product line generates the most revenue in the last quarter?",
        "key_insight": f"{top_row['product_line']} leads with {_currency_formatter(top_row['revenue'], None)}.",
        "annotation": "Arrow highlights the highest-revenue product for prioritization.",
    }


def chart2_revenue_trend_top3(data: pd.DataFrame, output_dir: Path) -> dict:
    """Chart 2: Monthly revenue trend lines for top three products."""
    monthly = (
        data.assign(month=data["order_date"].dt.to_period("M").dt.to_timestamp())
        .groupby(["month", "product_line"], as_index=False)["order_amount"]
        .sum()
    )
    top_products = (
        monthly.groupby("product_line")["order_amount"].sum().sort_values(ascending=False).head(3).index.tolist()
    )
    monthly_top = monthly[monthly["product_line"].isin(top_products)]

    fig, ax = plt.subplots(figsize=(12, 6))
    for product in top_products:
        series = monthly_top[monthly_top["product_line"] == product].sort_values("month")
        ax.plot(
            series["month"],
            series["order_amount"],
            marker="o",
            linewidth=2,
            label=product,
            color=PRODUCT_COLORS[product],
        )

    ax.set_title("Monthly Revenue Trend (Top 3 Product Lines)", fontsize=14, fontweight="bold")
    ax.set_xlabel("Month", fontsize=12)
    ax.set_ylabel("Revenue ($)", fontsize=12)
    ax.yaxis.set_major_formatter(FuncFormatter(_currency_formatter))
    ax.legend(loc="upper left", fontsize=10, title="Product Line")
    ax.grid(True, alpha=0.25)

    aggregate = monthly_top.groupby("month", as_index=False)["order_amount"].sum()
    dip = aggregate.loc[aggregate["order_amount"].idxmin()]
    ax.annotate(
        f"Lowest month\n{dip['month']:%b %Y}",
        xy=(dip["month"], dip["order_amount"]),
        xytext=(dip["month"], dip["order_amount"] * 1.25),
        arrowprops={"arrowstyle": "->", "color": PALETTE["warning"], "lw": 2},
        bbox={"boxstyle": "round,pad=0.3", "fc": "white", "ec": PALETTE["warning"], "alpha": 0.9},
        ha="center",
        fontsize=10,
    )

    out_path = output_dir / "chart2_revenue_trend.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return {
        "question": "How has monthly revenue changed over 12 months for top products?",
        "key_insight": f"The combined top-3 revenue trough occurs in {dip['month']:%b %Y}.",
        "annotation": "Marker identifies the monthly revenue dip to trigger root-cause review.",
    }


def chart3_order_distribution(data: pd.DataFrame, output_dir: Path) -> dict:
    """Chart 3: Histogram for order-value distribution."""
    bins = [0, 50, 100, 150, 200, 250, 300, 400]
    fig, ax = plt.subplots(figsize=(10, 6))
    counts, edges, patches = ax.hist(
        data["order_amount"], bins=bins, color=PALETTE["primary"], alpha=0.8, edgecolor="black", label="Orders"
    )

    ax.set_title("Distribution of Order Values", fontsize=14, fontweight="bold")
    ax.set_xlabel("Order Value ($)", fontsize=12)
    ax.set_ylabel("Order Count", fontsize=12)
    ax.legend(loc="upper right", fontsize=10)
    ax.grid(axis="y", alpha=0.25)

    for count, left, right in zip(counts, edges[:-1], edges[1:]):
        if count > 0:
            ax.text((left + right) / 2, count, f"{int(count)}", ha="center", va="bottom", fontsize=8)

    peak_idx = int(np.argmax(counts))
    peak_center = (edges[peak_idx] + edges[peak_idx + 1]) / 2
    peak_count = counts[peak_idx]
    ax.annotate(
        "Most common order range",
        xy=(peak_center, peak_count),
        xytext=(peak_center + 40, peak_count * 1.15),
        arrowprops={"arrowstyle": "->", "color": PALETTE["warning"], "lw": 2},
        bbox={"boxstyle": "round,pad=0.3", "fc": "white", "ec": PALETTE["warning"], "alpha": 0.9},
        fontsize=10,
    )

    out_path = output_dir / "chart3_order_value_distribution.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return {
        "question": "What order value ranges occur most frequently?",
        "key_insight": f"Peak concentration is near ${peak_center:.0f} order values.",
        "annotation": "Callout marks the dominant bin that drives transaction volume.",
    }


def chart4_quarterly_composition(data: pd.DataFrame, output_dir: Path) -> dict:
    """Chart 4: Stacked bar for quarterly revenue composition by product line."""
    quarter_data = (
        data.assign(quarter=data["order_date"].dt.to_period("Q").astype(str))
        .groupby(["quarter", "product_line"], as_index=False)["order_amount"]
        .sum()
    )
    pivot = quarter_data.pivot(index="quarter", columns="product_line", values="order_amount").fillna(0)
    pivot = pivot[sorted(pivot.columns)]

    fig, ax = plt.subplots(figsize=(11, 6))
    bottom = np.zeros(len(pivot))
    for product in pivot.columns:
        values = pivot[product].values
        ax.bar(
            pivot.index,
            values,
            bottom=bottom,
            color=PRODUCT_COLORS[product],
            label=product,
        )
        bottom += values

    for idx, total in enumerate(bottom):
        ax.text(idx, total, _currency_formatter(total, None), ha="center", va="bottom", fontsize=9)

    ax.set_title("Quarterly Revenue Composition by Product Line", fontsize=14, fontweight="bold")
    ax.set_xlabel("Quarter", fontsize=12)
    ax.set_ylabel("Revenue ($)", fontsize=12)
    ax.yaxis.set_major_formatter(FuncFormatter(_currency_formatter))
    ax.legend(loc="upper left", fontsize=10, title="Product Line")
    ax.grid(axis="y", alpha=0.25)

    shares = pivot.div(pivot.sum(axis=1), axis=0)
    final_q = shares.iloc[-1]
    dominant = final_q.idxmax()
    ax.annotate(
        f"{dominant} highest share\nin {shares.index[-1]}",
        xy=(len(shares.index) - 1, bottom[-1]),
        xytext=(len(shares.index) - 1.3, bottom[-1] * 1.15),
        arrowprops={"arrowstyle": "->", "color": PALETTE["warning"], "lw": 2},
        bbox={"boxstyle": "round,pad=0.3", "fc": "white", "ec": PALETTE["warning"], "alpha": 0.9},
        fontsize=10,
    )

    out_path = output_dir / "chart4_revenue_composition.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return {
        "question": "How does product-line composition contribute to quarterly revenue?",
        "key_insight": f"{dominant} contributes the largest share in the latest quarter.",
        "annotation": "Callout highlights the dominant product share in the latest quarter.",
    }


def chart5_marketing_vs_revenue(data: pd.DataFrame, output_dir: Path) -> dict:
    """Chart 5: Scatter for relationship between marketing spend and revenue."""
    points = (
        data.assign(month=data["order_date"].dt.to_period("M").dt.to_timestamp())
        .groupby(["month", "product_line"], as_index=False)
        .agg(revenue=("order_amount", "sum"), marketing_spend=("marketing_spend", "sum"))
    )
    correlation = points["marketing_spend"].corr(points["revenue"])

    fig, ax = plt.subplots(figsize=(10, 6))
    for product, subset in points.groupby("product_line"):
        ax.scatter(
            subset["marketing_spend"],
            subset["revenue"],
            s=45,
            alpha=0.8,
            color=PRODUCT_COLORS[product],
            label=product,
        )

    # Add a trend line across all product-month points.
    m, b = np.polyfit(points["marketing_spend"], points["revenue"], 1)
    x_vals = np.linspace(points["marketing_spend"].min(), points["marketing_spend"].max(), 100)
    ax.plot(x_vals, m * x_vals + b, color=PALETTE["neutral"], linestyle="--", linewidth=2, label="Trend line")

    ax.set_title("Marketing Spend vs Revenue Generated", fontsize=14, fontweight="bold")
    ax.set_xlabel("Marketing Spend ($)", fontsize=12)
    ax.set_ylabel("Revenue ($)", fontsize=12)
    ax.xaxis.set_major_formatter(FuncFormatter(_currency_formatter))
    ax.yaxis.set_major_formatter(FuncFormatter(_currency_formatter))
    ax.legend(loc="upper left", fontsize=9, ncol=2)
    ax.grid(True, alpha=0.25)

    residuals = points["revenue"] - (m * points["marketing_spend"] + b)
    outlier_idx = residuals.idxmin()
    outlier = points.loc[outlier_idx]
    ax.annotate(
        "High spend, lower-than-expected revenue",
        xy=(outlier["marketing_spend"], outlier["revenue"]),
        xytext=(outlier["marketing_spend"] * 1.05, outlier["revenue"] * 1.15),
        arrowprops={"arrowstyle": "->", "color": PALETTE["warning"], "lw": 2},
        bbox={"boxstyle": "round,pad=0.3", "fc": "white", "ec": PALETTE["warning"], "alpha": 0.9},
        fontsize=9,
    )

    ax.text(
        0.02,
        0.95,
        f"Correlation: r = {correlation:.2f}",
        transform=ax.transAxes,
        va="top",
        bbox={"boxstyle": "round,pad=0.3", "fc": "white", "ec": PALETTE["neutral"], "alpha": 0.9},
    )

    out_path = output_dir / "chart5_marketing_vs_revenue.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return {
        "question": "Does higher marketing spend correlate with higher revenue?",
        "key_insight": f"The relationship is {'strong' if correlation >= 0.7 else 'moderate'} with r={correlation:.2f}.",
        "annotation": "Callout marks the weakest-performing spend-to-revenue outlier.",
    }


def write_readme(output_dir: Path, chart_notes: dict) -> None:
    """Write chart documentation including labeling, colors, and annotations."""
    palette_text = "\n".join(
        [
            "- primary (#1f77b4): baseline business metric emphasis",
            "- secondary (#ff7f0e): comparative series",
            "- success (#2ca02c): positive growth/composition",
            "- warning (#d62728): anomalies and risk highlights",
            "- neutral (#7f7f7f): reference lines and contextual guides",
        ]
    )

    readme = f"""# Analysis Visualizations

All charts use complete labels: descriptive title, x-axis label with units, y-axis label with units, legend for multi-series charts, and readable value labels where practical.

## Consistent Palette
{palette_text}

## Chart 1: Revenue by Product Line
- Type: Horizontal bar chart
- Question: {chart_notes['chart1']['question']}
- Key Insight: {chart_notes['chart1']['key_insight']}
- Annotation: {chart_notes['chart1']['annotation']}

## Chart 2: Revenue Trend
- Type: Multi-series line chart
- Question: {chart_notes['chart2']['question']}
- Key Insight: {chart_notes['chart2']['key_insight']}
- Annotation: {chart_notes['chart2']['annotation']}

## Chart 3: Order Value Distribution
- Type: Histogram
- Question: {chart_notes['chart3']['question']}
- Key Insight: {chart_notes['chart3']['key_insight']}
- Annotation: {chart_notes['chart3']['annotation']}

## Chart 4: Revenue Composition
- Type: Stacked bar chart by quarter
- Question: {chart_notes['chart4']['question']}
- Key Insight: {chart_notes['chart4']['key_insight']}
- Annotation: {chart_notes['chart4']['annotation']}

## Chart 5: Marketing vs Revenue
- Type: Scatter plot with trend line
- Question: {chart_notes['chart5']['question']}
- Key Insight: {chart_notes['chart5']['key_insight']}
- Annotation: {chart_notes['chart5']['annotation']}
"""
    (output_dir / "CHARTS_README.md").write_text(readme, encoding="utf-8")


def run() -> None:
    """Generate all required charts and documentation."""
    root = Path(__file__).resolve().parents[1]
    data_path = root / "data/raw/chart_orders_sample.csv"
    output_dir = root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    sns.set_theme(style="whitegrid")
    data = create_or_load_dataset(data_path)
    data["order_date"] = pd.to_datetime(data["order_date"])

    notes = {
        "chart1": chart1_revenue_by_product(data, output_dir),
        "chart2": chart2_revenue_trend_top3(data, output_dir),
        "chart3": chart3_order_distribution(data, output_dir),
        "chart4": chart4_quarterly_composition(data, output_dir),
        "chart5": chart5_marketing_vs_revenue(data, output_dir),
    }
    write_readme(output_dir, notes)
    print("Generated 5 charts and output/CHARTS_README.md")


if __name__ == "__main__":
    run()