"""Interactive Streamlit dashboard for the subscription analytics project."""

from pathlib import Path

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data/raw/segment_profile_sample.csv"
TIME_SERIES_PATH = ROOT / "data/raw/daily_revenue_sample.csv"


st.set_page_config(page_title="Analytics Dashboard", page_icon="📊", layout="wide")


@st.cache_data
def load_segment_data():
    """Load customer segment data from the repository's raw data folder."""
    return pd.read_csv(DATA_PATH)


@st.cache_data
def load_time_series():
    """Load daily revenue data and parse its date column."""
    return pd.read_csv(TIME_SERIES_PATH, parse_dates=["date"])


def render_overview(segment_data):
    """Render KPI cards and segment highlights for the Overview page."""
    st.title("Business Overview")

    # Keep the most important business measures at the top of the first view.
    total_revenue = segment_data["lifetime_value"].sum()
    average_ltv = segment_data["lifetime_value"].mean()
    churn_rate = segment_data["churn"].mean()
    average_retention = segment_data["retention_days"].mean()
    customer_count = segment_data["customer_id"].nunique()
    cards = st.columns(5)
    cards[0].metric("Lifetime Value", f"${total_revenue:,.0f}")
    cards[1].metric("Customers", f"{customer_count:,}")
    cards[2].metric("Average LTV", f"${average_ltv:,.0f}")
    cards[3].metric("Churn", f"{churn_rate:.1%}", delta_color="inverse")
    cards[4].metric("Avg Retention", f"{average_retention:.0f} days")

    st.divider()
    st.header("Segment Health")
    left, right = st.columns(2)
    with left:
        st.subheader("Value and Retention")
        segment_summary = (
            segment_data.groupby("customer_type")
            .agg(avg_ltv=("lifetime_value", "mean"), churn=("churn", "mean"), retention=("retention_days", "mean"))
            .sort_values("avg_ltv", ascending=False)
        )
        st.dataframe(
            segment_summary.style.format(
                {"avg_ltv": "${:,.0f}", "churn": "{:.1%}", "retention": "{:.0f} days"}
            ),
            use_container_width=True,
        )
    with right:
        st.subheader("Priority Signal")
        highest_churn = segment_summary["churn"].idxmax()
        highest_value = segment_summary["avg_ltv"].idxmax()
        st.info(
            f"{highest_churn} has the highest churn at {segment_summary.loc[highest_churn, 'churn']:.1%}. "
            f"{highest_value} has the highest average LTV at ${segment_summary.loc[highest_value, 'avg_ltv']:,.0f}."
        )

    with st.expander("About These Metrics"):
        st.write(
            "Lifetime value is summed or averaged from the customer profile sample. "
            "Churn is the share of records marked as churned, and retention is the "
            "average number of days customers remain active."
        )


def render_trends(time_series):
    """Render revenue trends, rolling averages, and time-series details."""
    st.title("Trend Analysis")

    time_series = time_series.sort_values("date").copy()
    time_series["revenue_ma7"] = time_series["revenue"].rolling(7).mean()
    time_series["revenue_ma30"] = time_series["revenue"].rolling(30).mean()
    monthly = time_series.set_index("date")["revenue"].resample("ME").sum()
    monthly_change = monthly.pct_change().iloc[-1]

    st.header("Revenue Trends")
    st.subheader("Daily Revenue and Rolling Averages")
    chart_data = time_series.set_index("date")[["revenue", "revenue_ma7", "revenue_ma30"]]
    st.line_chart(chart_data, y_label="Revenue ($)")
    st.caption(
        f"Latest month-over-month change: {monthly_change:.1%}. "
        "Rolling averages smooth daily variation to expose direction."
    )

    st.divider()
    st.header("Monthly Performance")
    monthly_columns = st.columns(2)
    with monthly_columns[0]:
        st.subheader("Revenue by Month")
        st.bar_chart(monthly, y_label="Revenue ($)")
    with monthly_columns[1]:
        st.subheader("Trend Readout")
        best_month = monthly.idxmax()
        st.metric("Best Month", best_month.strftime("%B %Y"), f"${monthly.max():,.0f}")
        st.metric("Total Revenue", f"${time_series['revenue'].sum():,.0f}")

    with st.expander("Methodology"):
        st.write(
            "Revenue is summed by calendar month. The 7-day and 30-day rolling "
            "averages use trailing daily windows; the first rows remain blank until "
            "enough observations are available."
        )


def render_data_explorer(segment_data):
    """Render filters, a data table, and a download option."""
    st.title("Data Explorer")

    st.header("Filter Customer Records")
    controls = st.columns(3)
    segment_options = sorted(segment_data["customer_type"].unique())
    with controls[0]:
        selected_segments = st.multiselect("Customer type", segment_options, default=segment_options)
    with controls[1]:
        minimum_ltv = st.number_input("Minimum lifetime value ($)", min_value=0, value=0, step=1000)
    with controls[2]:
        churn_only = st.checkbox("Show churned customers only")

    filtered = segment_data[segment_data["customer_type"].isin(selected_segments)]
    filtered = filtered[filtered["lifetime_value"] >= minimum_ltv]
    if churn_only:
        filtered = filtered[filtered["churn"] == 1]

    st.divider()
    st.header("Customer Records")
    st.subheader(f"{len(filtered):,} records match the current filters")
    st.dataframe(filtered, use_container_width=True, hide_index=True)
    st.download_button(
        "Download filtered CSV",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="filtered_customer_segments.csv",
        mime="text/csv",
    )

    with st.expander("Data Notes"):
        st.write(
            "This explorer uses the repository sample profile data. Filters update "
            "the visible table and downloaded CSV together."
        )


st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Overview", "Trends", "Data Explorer"])
st.sidebar.divider()
st.sidebar.caption("Subscription analytics workspace")

if page == "Overview":
    render_overview(load_segment_data())
elif page == "Trends":
    render_trends(load_time_series())
else:
    render_data_explorer(load_segment_data())