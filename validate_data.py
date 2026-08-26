"""Data validation script used by CI to validate processed CSVs.

Checks:
- Required columns present
- Expected dtypes (amount numeric)
- Minimum row count (100)
- No fully-null columns

Exits with non-zero code on any validation failure so CI jobs fail.
"""

import sys
from pathlib import Path

import pandas as pd


def validate(path):
    path = Path(path)
    if not path.exists():
        print(f"ERROR: File not found: {path}")
        sys.exit(2)

    try:
        df = pd.read_csv(path, parse_dates=["date"])
    except Exception as e:
        print(f"ERROR: Failed to read CSV {path}: {e}")
        sys.exit(2)

    errors = []

    # Required columns
    required = ["customer_id", "order_id", "amount", "date", "segment"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        errors.append("Missing columns: " + str(missing))
        print("ERROR: Missing required columns:", missing)
    else:
        print("PASS: Required columns present")

    # Data types
    if "amount" in df.columns:
        if not pd.api.types.is_numeric_dtype(df["amount"]):
            errors.append("amount column is not numeric")
            print("ERROR: 'amount' column is not numeric")
        else:
            print("PASS: amount is numeric")

    # Minimum rows
    row_count = len(df)
    if row_count < 100:
        errors.append(f"Row count {row_count} below minimum 100")
        print(f"ERROR: Row count {row_count} below minimum 100")
    else:
        print(f"PASS: Row count {row_count} meets minimum")

    # Null columns
    null_cols = [c for c in df.columns if df[c].isnull().all()]
    if null_cols:
        errors.append("Fully null columns: " + str(null_cols))
        print("ERROR: Fully null columns:", null_cols)
    else:
        print("PASS: No fully null columns")

    if errors:
        print("\nVALIDATION FAILED:")
        for e in errors:
            print("  ERROR:", e)
        # non-zero exit -> CI failure
        sys.exit(1)
    else:
        print("\nALL CHECKS PASSED")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_data.py <path/to/csv>")
        sys.exit(2)
    validate(sys.argv[1])
