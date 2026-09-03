"""Module 3 — Data Dictionary & Business Context Mapping

Provides programmatic access to the project's data dictionary, domain schemas,
business context mappings, and dataset schema compliance validation.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


DATA_DICTIONARY: Dict[str, Dict[str, Any]] = {
    # 1. User & Subscription Domain
    "viewer_id": {
        "domain": "User & Subscription",
        "data_type": "string",
        "nullable": False,
        "is_primary_key": True,
        "meaning": "Unique viewer identifier",
        "business_purpose": "Cross-session user tracking and lifecycle analytics",
    },
    "user_name": {
        "domain": "User & Subscription",
        "data_type": "string",
        "nullable": False,
        "is_primary_key": False,
        "meaning": "Full name or display name of the account holder",
        "business_purpose": "Account identification and personalization",
    },
    "country": {
        "domain": "User & Subscription",
        "data_type": "string",
        "nullable": False,
        "is_primary_key": False,
        "meaning": "Two-letter country code (ISO-3166-1 alpha-2)",
        "business_purpose": "Geographic segmentation and regional acquisition planning",
    },
    "signup_date": {
        "domain": "User & Subscription",
        "data_type": "datetime",
        "nullable": False,
        "is_primary_key": False,
        "meaning": "Date of initial account creation",
        "business_purpose": "Cohort retention and tenure analysis",
    },
    "subscription_plan": {
        "domain": "User & Subscription",
        "data_type": "category",
        "allowed_values": ["Basic", "Standard", "Premium"],
        "nullable": False,
        "is_primary_key": False,
        "meaning": "Active subscription tier",
        "business_purpose": "Assessing retention and engagement variations across pricing tiers",
    },
    "monthly_fee": {
        "domain": "User & Subscription",
        "data_type": "float",
        "min_value": 0.0,
        "nullable": False,
        "is_primary_key": False,
        "meaning": "Monthly subscription charge in USD",
        "business_purpose": "Monthly Recurring Revenue (MRR) and CLV calculation",
    },
    "auto_renew": {
        "domain": "User & Subscription",
        "data_type": "boolean",
        "nullable": False,
        "is_primary_key": False,
        "meaning": "Automatic billing renewal flag",
        "business_purpose": "Early churn risk indicator when toggled off",
    },

    # 2. Viewing Consumption Domain
    "content_id": {
        "domain": "Viewing Consumption",
        "data_type": "string",
        "nullable": False,
        "is_primary_key": False,
        "meaning": "Unique media asset identifier",
        "business_purpose": "Catalog performance tracking and licensing valuation",
    },
    "content_title": {
        "domain": "Viewing Consumption",
        "data_type": "string",
        "nullable": False,
        "is_primary_key": False,
        "meaning": "Title of movie or series",
        "business_purpose": "Executive reporting on top-performing assets",
    },
    "genre": {
        "domain": "Viewing Consumption",
        "data_type": "category",
        "nullable": False,
        "is_primary_key": False,
        "meaning": "Primary content genre category",
        "business_purpose": "Genre affinity analysis to guide licensing decisions",
    },
    "watch_date": {
        "domain": "Viewing Consumption",
        "data_type": "datetime",
        "nullable": False,
        "is_primary_key": False,
        "meaning": "Timestamp or date of viewing session",
        "business_purpose": "Time-series trend analysis and viewing seasonality",
    },
    "watch_duration_minutes": {
        "domain": "Viewing Consumption",
        "data_type": "float",
        "min_value": 0.0,
        "nullable": False,
        "is_primary_key": False,
        "meaning": "Total duration watched in minutes",
        "business_purpose": "Core consumption volume metric",
    },
    "total_content_duration_minutes": {
        "domain": "Viewing Consumption",
        "data_type": "float",
        "min_value": 0.0,
        "nullable": False,
        "is_primary_key": False,
        "meaning": "Total runtime of the media asset",
        "business_purpose": "Baseline for calculating completion rates",
    },

    # 3. Engagement Dynamics Domain
    "completion_rate": {
        "domain": "Engagement Dynamics",
        "data_type": "float",
        "min_value": 0.0,
        "max_value": 1.0,
        "nullable": False,
        "is_primary_key": False,
        "meaning": "Proportion of content runtime completed (0.0 to 1.0)",
        "business_purpose": "Key proxy for content satisfaction and stickiness",
    },
    "pause_frequency": {
        "domain": "Engagement Dynamics",
        "data_type": "integer",
        "min_value": 0,
        "nullable": False,
        "is_primary_key": False,
        "meaning": "Count of playback pauses during session",
        "business_purpose": "Viewing friction and attention metric",
    },
    "episodes_watched": {
        "domain": "Engagement Dynamics",
        "data_type": "integer",
        "min_value": 0,
        "nullable": False,
        "is_primary_key": False,
        "meaning": "Cumulative count of episodes watched",
        "business_purpose": "Episodic stickiness and series completion tracking",
    },
    "viewing_frequency_per_week": {
        "domain": "Engagement Dynamics",
        "data_type": "integer",
        "min_value": 0,
        "max_value": 7,
        "nullable": False,
        "is_primary_key": False,
        "meaning": "Distinct active viewing days per week",
        "business_purpose": "Habituation and platform engagement intensity",
    },
    "binge_watching_flag": {
        "domain": "Engagement Dynamics",
        "data_type": "boolean",
        "nullable": False,
        "is_primary_key": False,
        "meaning": "1 if >=3 consecutive episodes watched in a day, else 0",
        "business_purpose": "Identifies high-propensity retained user behavior",
    },

    # 4. Retention & Churn Domain
    "subscription_status": {
        "domain": "Retention & Churn",
        "data_type": "category",
        "allowed_values": ["Active", "Paused", "Cancelled"],
        "nullable": False,
        "is_primary_key": False,
        "meaning": "Current subscriber account status",
        "business_purpose": "Operational KPI for active subscriber base",
    },
    "churn": {
        "domain": "Retention & Churn",
        "data_type": "binary",
        "allowed_values": [0, 1],
        "nullable": False,
        "is_primary_key": False,
        "meaning": "1 if subscriber churned within window, 0 if retained",
        "business_purpose": "Primary target variable for predictive retention modeling",
    },
    "retention_risk_tier": {
        "domain": "Retention & Churn",
        "data_type": "category",
        "allowed_values": ["Low", "Medium", "High", "Critical"],
        "nullable": False,
        "is_primary_key": False,
        "meaning": "Algorithm-assigned churn risk category",
        "business_purpose": "Guides proactive retention campaigns and offers",
    },
    "customer_lifetime_value": {
        "domain": "Retention & Churn",
        "data_type": "float",
        "min_value": 0.0,
        "nullable": False,
        "is_primary_key": False,
        "meaning": "Cumulative historical revenue generated",
        "business_purpose": "Customer profitability and acquisition ROI tracking",
    },
}


def get_data_dictionary() -> Dict[str, Dict[str, Any]]:
    """Return the complete data dictionary."""
    return DATA_DICTIONARY


def get_fields_by_domain(domain_name: str) -> Dict[str, Dict[str, Any]]:
    """
    Filter fields belonging to a specific domain:
    'User & Subscription', 'Viewing Consumption', 'Engagement Dynamics', 'Retention & Churn'.
    """
    return {k: v for k, v in DATA_DICTIONARY.items() if v.get("domain") == domain_name}


def validate_dataframe_schema(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate DataFrame columns against the data dictionary schema.

    Parameters:
        df: Pandas DataFrame to validate.

    Returns:
        Dictionary containing matched fields, unmatched fields, and domain coverage.
    """
    known_fields = set(DATA_DICTIONARY.keys())
    df_fields = set(df.columns)

    matched = sorted(list(known_fields.intersection(df_fields)))
    unmatched_in_df = sorted(list(df_fields - known_fields))
    missing_standard_fields = sorted(list(known_fields - df_fields))

    domain_coverage: Dict[str, Dict[str, int]] = {}
    for domain in ["User & Subscription", "Viewing Consumption", "Engagement Dynamics", "Retention & Churn"]:
        domain_fields = set(get_fields_by_domain(domain).keys())
        present_in_df = domain_fields.intersection(df_fields)
        domain_coverage[domain] = {
            "total_domain_fields": len(domain_fields),
            "present_in_dataset": len(present_in_df),
            "coverage_pct": round((len(present_in_df) / max(len(domain_fields), 1)) * 100, 1),
        }

    return {
        "total_dataset_columns": len(df.columns),
        "matched_columns_count": len(matched),
        "matched_columns": matched,
        "unmatched_dataset_columns": unmatched_in_df,
        "missing_standard_fields_count": len(missing_standard_fields),
        "domain_coverage": domain_coverage,
    }


def export_data_dictionary_json(output_path: Optional[Path] = None) -> Path:
    """Export the data dictionary to a JSON file."""
    repo_root = Path(__file__).resolve().parents[1]
    save_path = output_path or (repo_root / "output/data_dictionary.json")
    save_path.parent.mkdir(parents=True, exist_ok=True)

    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(DATA_DICTIONARY, f, indent=2)

    return save_path


def run_data_dictionary_demo() -> None:
    """Demonstrate data dictionary inspection and JSON export."""
    repo_root = Path(__file__).resolve().parents[1]
    json_path = export_data_dictionary_json()

    print("=" * 70)
    print("MODULE 3: DATA DICTIONARY & BUSINESS CONTEXT MAPPING")
    print("=" * 70)

    domains = ["User & Subscription", "Viewing Consumption", "Engagement Dynamics", "Retention & Churn"]
    for domain in domains:
        fields = get_fields_by_domain(domain)
        print(f"\n[{domain.upper()}] ({len(fields)} fields)")
        for col_name, meta in fields.items():
            print(f"  - {col_name} ({meta['data_type']}): {meta['meaning']}")

    print(f"\n[OK] Data dictionary successfully exported to: {json_path.relative_to(repo_root)}")
    print("=" * 70)


if __name__ == "__main__":
    run_data_dictionary_demo()
