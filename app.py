"""Interactive Streamlit dashboard for the subscription analytics project."""

from pathlib import Path

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data/raw/segment_profile_sample.csv"
TIME_SERIES_PATH = ROOT / "data/raw/daily_revenue_sample.csv"


st.set_page_config(page_title="Subscription Analytics", page_icon="📊", layout="wide")

dark_mode = st.toggle("Dark mode", value=False)
theme = {
    "background": "#172522" if dark_mode else "#f7f8f3",
    "text": "#e8f0eb" if dark_mode else "#29433f",
    "heading": "#b9e0c8" if dark_mode else "#1f5148",
    "surface": "#22352f" if dark_mode else "#edf4ef",
    "border": "#3d5b50" if dark_mode else "#d3e3d8",
    "muted": "#a7c1b4" if dark_mode else "#52736a",
    "hover": "#315147" if dark_mode else "#e5eee8",
    "alert": "#4a332c" if dark_mode else "#fff1e8",
    "alert_text": "#ffd1bd" if dark_mode else "#704436",
    "header": "#101918" if dark_mode else "#eef2ed",
    "control": "#1e302b" if dark_mode else "#ffffff",
}

st.markdown(
    f"""
    <style>
    :root {{
        color-scheme: {"dark" if dark_mode else "light"};
    }}
    html, body, #root, .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stAppViewContainer"] > .main,
    [data-testid="stAppViewContainer"] .main,
    [data-testid="stAppViewContainer"] .block-container {{
        background: {theme["background"]} !important;
        color: {theme["text"]} !important;
    }}
    [data-testid="stAppViewContainer"] .block-container {{
        max-width: 100% !important;
    }}
    [data-testid="stAppViewContainer"],
    [data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"] {{
        background: {theme["header"]} !important;
        border-color: {theme["border"]} !important;
    }}
    [data-testid="stToolbar"] button,
    [data-testid="stHeader"] button,
    [data-testid="stToolbar"] svg,
    [data-testid="stHeader"] svg {{
        color: {theme["text"]} !important;
        fill: {theme["text"]} !important;
    }}
    .stApp p, .stApp label, .stApp span,
    .stApp [data-testid="stCaptionContainer"],
    .stApp [data-testid="stMarkdownContainer"] {{
        color: {theme["text"]} !important;
    }}
    .stApp h1, .stApp h2, .stApp h3, .stApp h4 {{
        color: {theme["heading"]} !important;
    }}
    [data-testid="stRadio"] label {{
        padding: 0.45rem 0.6rem;
        border-radius: 0.4rem;
    }}
    [data-testid="stRadio"] label:hover {{
        background: {theme["hover"]};
    }}
    label:has(input[role="switch"]) > div {{
        background: {theme["border"]} !important;
    }}
    label:has(input[role="switch"]:checked) > div {{
        background: #e98263 !important;
    }}
    label:has(input[role="switch"]) > div > div {{
        background: #ffffff !important;
    }}
    [data-testid="stMetric"] {{
        background: {theme["surface"]} !important;
        border: 1px solid {theme["border"]} !important;
        padding: 0.8rem;
        border-radius: 0.5rem;
    }}
    [data-testid="stMetricLabel"] {{
        color: {theme["muted"]} !important;
    }}
    [data-testid="stMetricValue"] {{
        color: {theme["heading"]} !important;
    }}
    .stTextInput input,
    .stNumberInput input,
    [data-baseweb="select"] > div,
    [data-baseweb="input"] > div {{
        background: {theme["control"]} !important;
        color: {theme["text"]} !important;
        border-color: {theme["border"]} !important;
    }}
    [data-baseweb="select"] input,
    [data-baseweb="input"] input {{
        color: {theme["text"]} !important;
        caret-color: {theme["text"]} !important;
    }}
    [data-baseweb="select"] svg {{
        fill: {theme["text"]};
    }}
    [data-testid="stExpander"] {{
        background: {theme["surface"]} !important;
        border-color: {theme["border"]} !important;
    }}
    [data-testid="stAlert"] {{
        background: {theme["alert"]} !important;
        border-left-color: #e98263 !important;
        color: {theme["alert_text"]} !important;
    }}
    .stButton > button, .stDownloadButton > button {{
        width: 100%;
        min-height: 3rem;
        background: #1f5148;
        color: #ffffff !important;
        border: 1px solid #1f5148;
        font-weight: 700;
    }}
    .stButton > button:hover, .stDownloadButton > button:hover {{
        background: #d56f54;
        border-color: #d56f54;
        color: #ffffff !important;
    }}
    [data-testid="stDataFrame"] {{
        border: 1px solid {theme["border"]} !important;
        background: {theme["surface"]} !important;
    }}
    [data-testid="stDataFrame"] iframe {{
        background: {theme["surface"]} !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


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
    st.title("Start here")
    st.caption("The headline view of your customer base.")

    # Keep the most important business measures at the top of the first view.
    total_revenue = segment_data["lifetime_value"].sum()
    average_ltv = segment_data["lifetime_value"].mean()
    churn_rate = segment_data["churn"].mean()
    average_retention = segment_data["retention_days"].mean()
    customer_count = segment_data["customer_id"].nunique()
    cards = st.columns(5)
    cards[0].metric("Total customer value", f"${total_revenue:,.0f}")
    cards[1].metric("Customers", f"{customer_count:,}")
    cards[2].metric("Average customer value", f"${average_ltv:,.0f}")
    cards[3].metric("Churn rate", f"{churn_rate:.1%}", delta_color="inverse")
    cards[4].metric("Average active days", f"{average_retention:.0f}")

    st.divider()
    st.header("What needs attention?")
    st.caption("The comparison below highlights the customer type with the highest risk and value.")
    left, right = st.columns(2)
    with left:
        st.subheader("Compare customer types")
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
        st.subheader("Key takeaway")
        highest_churn = segment_summary["churn"].idxmax()
        highest_value = segment_summary["avg_ltv"].idxmax()
        st.info(
            f"{highest_churn} has the highest churn at {segment_summary.loc[highest_churn, 'churn']:.1%}. "
            f"{highest_value} has the highest average LTV at ${segment_summary.loc[highest_value, 'avg_ltv']:,.0f}."
        )

def render_trends(time_series):
    """Render revenue trends, rolling averages, and time-series details."""
    st.title("Revenue trends")
    st.caption("See how revenue is moving over time.")

    time_series = time_series.sort_values("date").copy()
    time_series["revenue_ma7"] = time_series["revenue"].rolling(7).mean()
    time_series["revenue_ma30"] = time_series["revenue"].rolling(30).mean()
    monthly = time_series.set_index("date")["revenue"].resample("ME").sum()
    monthly_change = monthly.pct_change().iloc[-1]

    st.header("Revenue over time")
    st.subheader("Daily revenue")
    chart_data = time_series.set_index("date")[["revenue", "revenue_ma7", "revenue_ma30"]]
    st.line_chart(chart_data, y_label="Revenue ($)")
    st.caption(
        f"Latest month-over-month change: {monthly_change:.1%}. "
        "Rolling averages smooth daily variation to expose direction."
    )

    st.divider()
    st.header("Monthly performance")
    monthly_columns = st.columns(2)
    with monthly_columns[0]:
        st.subheader("Revenue by month")
        st.bar_chart(monthly, y_label="Revenue ($)")
    with monthly_columns[1]:
        st.subheader("At a glance")
        best_month = monthly.idxmax()
        st.metric("Best Month", best_month.strftime("%B %Y"), f"${monthly.max():,.0f}")
        st.metric("Total Revenue", f"${time_series['revenue'].sum():,.0f}")

def render_data_explorer(segment_data):
    """Render filters, a data table, and a download option."""
    st.title("Customer records")
    st.caption("Find specific customers or download a filtered list.")

    st.header("Choose filters")
    controls = st.columns(3)
    segment_options = sorted(segment_data["customer_type"].unique())
    with controls[0]:
        selected_segments = st.multiselect(
            "Customer type",
            segment_options,
            default=segment_options,
            help="Select one or more customer types.",
        )
    with controls[1]:
        minimum_ltv = st.number_input(
            "Minimum customer value ($)",
            min_value=0,
            value=0,
            step=1000,
            help="Only show customers at or above this value.",
        )
    with controls[2]:
        churn_only = st.checkbox("Churned customers only")

    filtered = segment_data[segment_data["customer_type"].isin(selected_segments)]
    filtered = filtered[filtered["lifetime_value"] >= minimum_ltv]
    if churn_only:
        filtered = filtered[filtered["churn"] == 1]

    st.divider()
    st.header("Matching customers")
    st.subheader(f"{len(filtered):,} records")
    st.caption("The table and download below use the filters above.")
    st.dataframe(filtered, use_container_width=True, hide_index=True)
    st.download_button(
        "Download CSV",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="filtered_customer_segments.csv",
        mime="text/csv",
        type="primary",
        use_container_width=True,
    )

st.title("Subscription Analytics")
st.caption("A simple view of customer value, revenue, and retention.")
page = st.radio(
    "Choose a view",
    ["1. Overview", "2. Revenue trends", "3. Customer records"],
    horizontal=True,
    label_visibility="visible",
)
st.divider()

if page == "1. Overview":
    render_overview(load_segment_data())
elif page == "2. Revenue trends":
    render_trends(load_time_series())
else:
    render_data_explorer(load_segment_data())