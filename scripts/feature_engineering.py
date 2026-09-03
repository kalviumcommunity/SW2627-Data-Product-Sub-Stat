"""Module 4 — Feature Engineering & Derived Business Columns

Provides advanced feature engineering routines:
- Robust ratio feature derivation with safe division and infinity/null handling.
- Discretization and binning using domain boundaries (`pd.cut`) and quantiles (`pd.qcut`).
- Composite subscriber RFM (Recency, Frequency, Monetary) scoring and segmentation.
- Statistical distribution validation (moments, skewness, anomaly audits).
- Feature metadata and business definitions cataloging.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def safe_divide(
    numerator: Union[pd.Series, np.ndarray, float],
    denominator: Union[pd.Series, np.ndarray, float],
    fill_value: float = 0.0,
) -> pd.Series:
    """
    Perform element-wise division safely handling division by zero, nulls, and infinities.

    Parameters:
        numerator: Numerator Series or numeric array.
        denominator: Denominator Series or numeric array.
        fill_value: Value to replace division by zero or NaN results with.

    Returns:
        Cleaned pandas Series of quotient values.
    """
    num = pd.to_numeric(pd.Series(numerator), errors="coerce").fillna(0.0)
    den = pd.to_numeric(pd.Series(denominator), errors="coerce").fillna(0.0)

    # Perform division, masking zeroes in denominator
    result = np.where(den != 0.0, num / den, fill_value)
    clean_series = pd.Series(result, index=num.index, dtype=float)

    # Replace potential infinite artifacts
    clean_series = clean_series.replace([np.inf, -np.inf], fill_value).fillna(fill_value)
    return clean_series.round(4)


def create_ratio_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derive high-value business ratio features from raw activity metrics.

    Engineered features:
    - transactions_per_month: total_transactions / tenure_months
    - avg_spend_per_transaction: total_spend / total_transactions
    - completion_rate: completed_episodes / total_episodes_started
    - watch_hours_per_active_day: total_watch_hours / active_days

    Parameters:
        df: Input DataFrame containing raw transactional and viewing metrics.

    Returns:
        DataFrame enriched with ratio features.
    """
    df_copy = df.copy()

    # 1. Transactions per Month
    if "total_transactions" in df_copy.columns and "tenure_months" in df_copy.columns:
        df_copy["transactions_per_month"] = safe_divide(
            df_copy["total_transactions"],
            df_copy["tenure_months"],
            fill_value=0.0,
        )

    # 2. Average Spend per Transaction
    if "total_spend" in df_copy.columns and "total_transactions" in df_copy.columns:
        df_copy["avg_spend_per_transaction"] = safe_divide(
            df_copy["total_spend"],
            df_copy["total_transactions"],
            fill_value=0.0,
        )

    # 3. Episode Completion Rate
    if "completed_episodes" in df_copy.columns and "total_episodes_started" in df_copy.columns:
        df_copy["completion_rate"] = safe_divide(
            df_copy["completed_episodes"],
            df_copy["total_episodes_started"],
            fill_value=0.0,
        )

    # 4. Watch Hours per Active Day (Engagement Intensity)
    if "total_watch_hours" in df_copy.columns and "active_days" in df_copy.columns:
        df_copy["watch_hours_per_active_day"] = safe_divide(
            df_copy["total_watch_hours"],
            df_copy["active_days"],
            fill_value=0.0,
        )

    return df_copy


def create_binned_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Construct domain-defined and quantile-based discretized tier features.

    Features:
    - spend_tier: Binned using pd.cut into Low, Medium, High, VIP.
    - engagement_quantile: Binned using pd.qcut into Q1_Low, Q2_Moderate, Q3_High, Q4_Power.

    Parameters:
        df: Input DataFrame.

    Returns:
        DataFrame enriched with categorical and ordinal tiered columns.
    """
    df_copy = df.copy()

    # 1. Domain-defined spend tiers using pd.cut
    if "total_spend" in df_copy.columns:
        spend_bins = [-np.inf, 50.0, 150.0, 400.0, np.inf]
        spend_labels = ["Low", "Medium", "High", "VIP"]
        df_copy["spend_tier"] = pd.cut(
            df_copy["total_spend"],
            bins=spend_bins,
            labels=spend_labels,
            right=True,
        ).astype(str)

    # 2. Quantile-based engagement tiers using pd.qcut
    if "total_watch_hours" in df_copy.columns:
        q_labels = ["Q1_Low", "Q2_Moderate", "Q3_High", "Q4_Power"]
        df_copy["engagement_quantile"] = pd.qcut(
            df_copy["total_watch_hours"].rank(method="first"),
            q=4,
            labels=q_labels,
        ).astype(str)

    return df_copy


def calculate_rfm_composite_scores(
    df: pd.DataFrame,
    recency_col: str = "days_since_last_active",
    frequency_col: str = "total_transactions",
    monetary_col: str = "total_spend",
) -> pd.DataFrame:
    """
    Calculate composite RFM (Recency, Frequency, Monetary) scores and segment subscribers.

    Scores (1 to 5 scale):
    - R_Score: Inverse rank (lower recency days = higher score 5)
    - F_Score: Direct rank (higher transaction frequency = higher score 5)
    - M_Score: Direct rank (higher total monetary spend = higher score 5)
    - Composite RFM Score = 0.20 * R + 0.30 * F + 0.50 * M (scaled to 100)

    Parameters:
        df: Input DataFrame.
        recency_col: Column measuring days since last event.
        frequency_col: Column measuring transaction frequency.
        monetary_col: Column measuring revenue/spend.

    Returns:
        DataFrame enriched with RFM component scores, composite index, and customer segment.
    """
    df_copy = df.copy()

    for col in [recency_col, frequency_col, monetary_col]:
        if col not in df_copy.columns:
            raise KeyError(f"Required RFM column '{col}' missing from DataFrame.")

    # 1. Recency Score (1-5, inverted: fewer days -> higher score)
    df_copy["r_score"] = pd.qcut(
        df_copy[recency_col].rank(method="first", ascending=False),
        q=5,
        labels=[1, 2, 3, 4, 5],
    ).astype(int)

    # 2. Frequency Score (1-5, direct: higher frequency -> higher score)
    df_copy["f_score"] = pd.qcut(
        df_copy[frequency_col].rank(method="first", ascending=True),
        q=5,
        labels=[1, 2, 3, 4, 5],
    ).astype(int)

    # 3. Monetary Score (1-5, direct: higher spend -> higher score)
    df_copy["m_score"] = pd.qcut(
        df_copy[monetary_col].rank(method="first", ascending=True),
        q=5,
        labels=[1, 2, 3, 4, 5],
    ).astype(int)

    # 4. Composite RFM Weighted Index (Scale 0 - 100)
    # Weights: R=20%, F=30%, M=50%
    raw_rfm = (
        0.20 * df_copy["r_score"]
        + 0.30 * df_copy["f_score"]
        + 0.50 * df_copy["m_score"]
    )
    df_copy["rfm_composite_score"] = (raw_rfm * 20).round(2)  # 1-5 mapped to 20-100

    # 5. Business Segmentation Classification
    def map_segment(row: pd.Series) -> str:
        score = row["rfm_composite_score"]
        r = row["r_score"]
        if score >= 80:
            return "Champion"
        elif score >= 60 and r >= 3:
            return "Loyal Subscriber"
        elif score >= 50:
            return "Potential Loyalist"
        elif r <= 2 and score >= 40:
            return "At-Risk"
        else:
            return "Hibernating"

    df_copy["rfm_segment"] = df_copy.apply(map_segment, axis=1)
    return df_copy


def validate_feature_distributions(
    df: pd.DataFrame,
    numeric_columns: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Validate statistical distributions, bounds, and absence of anomalies (NaN, Inf) in engineered features.

    Returns:
        Structured dictionary containing statistical moments and quality validation flags.
    """
    cols = numeric_columns or df.select_dtypes(include=[np.number]).columns.tolist()
    distribution_report: Dict[str, Any] = {}

    for col in cols:
        series = pd.to_numeric(df[col], errors="coerce")
        has_null = int(series.isna().sum())
        has_inf = int(np.isinf(series).sum())

        clean_series = series.dropna()
        if len(clean_series) > 0:
            stats = {
                "count": int(len(clean_series)),
                "mean": round(float(clean_series.mean()), 4),
                "std": round(float(clean_series.std()), 4) if len(clean_series) > 1 else 0.0,
                "min": round(float(clean_series.min()), 4),
                "q25": round(float(clean_series.quantile(0.25)), 4),
                "median": round(float(clean_series.median()), 4),
                "q75": round(float(clean_series.quantile(0.75)), 4),
                "max": round(float(clean_series.max()), 4),
                "skewness": round(float(clean_series.skew()), 4) if len(clean_series) > 2 else 0.0,
                "null_count": has_null,
                "inf_count": has_inf,
                "is_valid": has_null == 0 and has_inf == 0,
            }
        else:
            stats = {"count": 0, "is_valid": False, "null_count": has_null, "inf_count": has_inf}

        distribution_report[col] = stats

    return distribution_report


def run_feature_engineering_pipeline(
    input_path: Union[str, Path] = "data/raw/viewer_engagement_features.csv",
    output_data_path: Union[str, Path] = "data/processed/feature_engineered_data.csv",
    output_report_path: Union[str, Path] = "output/feature_engineering_report.json",
) -> Dict[str, Any]:
    """
    Execute full feature engineering pipeline, generating ratio, binned, and composite RFM features.
    """
    input_file = Path(input_path)
    output_file = Path(output_data_path)
    report_file = Path(output_report_path)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Loading feature engineering intake from %s", input_file)
    df = pd.read_csv(input_file)
    initial_shape = df.shape

    # 1. Ratios
    df_ratios = create_ratio_features(df)

    # 2. Binning & Quantiles
    df_binned = create_binned_features(df_ratios)

    # 3. Composite RFM Scoring
    df_engineered = calculate_rfm_composite_scores(df_binned)

    # 4. Statistical Distribution Validation
    engineered_numeric_cols = [
        "transactions_per_month",
        "avg_spend_per_transaction",
        "completion_rate",
        "watch_hours_per_active_day",
        "r_score",
        "f_score",
        "m_score",
        "rfm_composite_score",
    ]
    dist_report = validate_feature_distributions(df_engineered, engineered_numeric_cols)

    # 5. Save Output Dataset
    df_engineered.to_csv(output_file, index=False)

    # 6. Build Comprehensive Summary & Business Metadata Catalog
    feature_catalog = {
        "transactions_per_month": {
            "type": "Ratio (Float)",
            "formula": "total_transactions / tenure_months (safe division)",
            "business_meaning": "Velocity of purchasing/subscription renewal transactions per month of customer tenure.",
        },
        "avg_spend_per_transaction": {
            "type": "Ratio (Float)",
            "formula": "total_spend / total_transactions (safe division)",
            "business_meaning": "Average monetary value generated per transaction event.",
        },
        "completion_rate": {
            "type": "Ratio (Float)",
            "formula": "completed_episodes / total_episodes_started (safe division)",
            "business_meaning": "Ratio of content finished to content started, indicating viewer engagement quality.",
        },
        "watch_hours_per_active_day": {
            "type": "Ratio (Float)",
            "formula": "total_watch_hours / active_days (safe division)",
            "business_meaning": "Viewing intensity representing average daily hours consumed on active platform days.",
        },
        "spend_tier": {
            "type": "Categorical (pd.cut)",
            "formula": "pd.cut on total_spend into [Low, Medium, High, VIP]",
            "business_meaning": "Monetary value tier classification for marketing incentives and acquisition analysis.",
        },
        "engagement_quantile": {
            "type": "Categorical (pd.qcut)",
            "formula": "pd.qcut on total_watch_hours into 4 quartiles",
            "business_meaning": "Quantile-based consumption classification comparing viewer behavior across the platform cohort.",
        },
        "rfm_composite_score": {
            "type": "Composite Metric (Float 20-100)",
            "formula": "(0.20 * R + 0.30 * F + 0.50 * M) * 20",
            "business_meaning": "Holistic subscriber health index balancing recent engagement, transaction frequency, and total lifetime spend.",
        },
        "rfm_segment": {
            "type": "Categorical Segment",
            "formula": "Threshold mapping on rfm_composite_score and recency",
            "business_meaning": "Actionable subscriber lifecycle segment (Champion, Loyal Subscriber, Potential Loyalist, At-Risk, Hibernating).",
        },
    }

    report = {
        "status": "SUCCESS",
        "timestamp": datetime.now().isoformat(),
        "input_file": str(input_file),
        "output_file": str(output_file),
        "initial_dimensions": {"rows": initial_shape[0], "columns": initial_shape[1]},
        "engineered_dimensions": {"rows": len(df_engineered), "columns": len(df_engineered.columns)},
        "new_features_created_count": len(df_engineered.columns) - initial_shape[1],
        "feature_catalog": feature_catalog,
        "distribution_validation": dist_report,
        "segment_distribution": df_engineered["rfm_segment"].value_counts().to_dict(),
        "spend_tier_distribution": df_engineered["spend_tier"].value_counts().to_dict(),
    }

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info("Saved feature engineering artifacts to %s and %s", output_file, report_file)
    return report


if __name__ == "__main__":
    run_feature_engineering_pipeline()
