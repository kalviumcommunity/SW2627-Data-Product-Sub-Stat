"""Validate an incoming dataset before it enters the analysis pipeline."""

import json
import os
from datetime import datetime
from pathlib import Path

import pandas as pd

try:
    import chardet
except ModuleNotFoundError:
    chardet = None


def validate_file_exists(filepath):
    """
    Check whether a file exists and contains at least one byte.

    Input: filepath pointing to the expected source file.
    Output: Tuple of a boolean result and a human-readable validation message.
    Assumption: The current process has permission to inspect the path.
    """
    # Confirm the path exists before checking its size.
    if not os.path.exists(filepath):
        return False, f"File does not exist: {filepath}"

    # An empty file cannot provide a usable dataset.
    if os.path.getsize(filepath) == 0:
        return False, f"File is empty: {filepath}"

    return True, "File exists and has content"


def validate_file_format(filepath, allowed_formats=("csv", "json", "xlsx")):
    """
    Check whether a file uses one of the supported extensions.

    Input: filepath and an optional iterable of lowercase extensions.
    Output: Tuple of a boolean result and a format validation message.
    Assumption: The extension is the final suffix after the last dot.
    """
    # Normalize the suffix so CSV, csv, and Csv are treated identically.
    extension = str(filepath).rsplit(".", 1)[-1].lower()

    if extension not in allowed_formats:
        return False, f"Unsupported format: {extension}. Allowed: {list(allowed_formats)}"

    return True, f"Format valid: {extension}"


def validate_schema(df, expected_columns):
    """
    Compare DataFrame columns with the required incoming schema.

    Input: Pandas DataFrame and an iterable of expected column names.
    Output: Tuple of a boolean result and a message listing schema issues.
    Assumption: Column names are compared exactly, including capitalization.
    """
    # Use sets to identify missing and unexpected columns independently.
    missing = set(expected_columns) - set(df.columns)
    extra = set(df.columns) - set(expected_columns)

    issues = []
    if missing:
        issues.append(f"Missing columns: {sorted(missing)}")
    if extra:
        issues.append(f"Unexpected columns: {sorted(extra)}")

    if not issues:
        return True, f"Schema valid: {len(df.columns)} columns present"
    return False, " | ".join(issues)


def detect_encoding(filepath):
    """
    Detect a source file's character encoding and confidence.

    Input: filepath pointing to a readable binary file.
    Output: Tuple of the detected encoding and a formatted confidence message.
    Assumption: The first 10,000 bytes are representative of the file encoding.
    """
    # Read a bounded sample so detection remains inexpensive for large files.
    with open(filepath, "rb") as file_handle:
        sample = file_handle.read(10000)

    # Prefer chardet; the fallback keeps UTF-8 validation usable offline.
    if chardet is not None:
        result = chardet.detect(sample)
    else:
        try:
            sample.decode("utf-8")
            result = {"encoding": "utf-8", "confidence": 1.0}
        except UnicodeDecodeError:
            result = {"encoding": "unknown", "confidence": 0}

    encoding = result.get("encoding") or "utf-8"
    confidence = result.get("confidence") or 0
    return encoding, f"Detected: {encoding.lower()} (confidence: {confidence:.1%})"


def capture_dataset_stats(filepath, df):
    """
    Capture baseline dimensions and storage size for a loaded dataset.

    Input: filepath for the source file and its loaded Pandas DataFrame.
    Output: Dictionary containing row count, column count, megabytes, and bytes.
    Assumption: The source path exists and can be measured with os.path.getsize.
    """
    # Record both human-readable megabytes and exact bytes for reproducibility.
    file_size_bytes = os.path.getsize(filepath)
    return {
        "rows": len(df),
        "columns": len(df.columns),
        "file_size_mb": round(file_size_bytes / (1024 * 1024), 5),
        "bytes": file_size_bytes,
    }


def generate_intake_report(filepath, expected_columns, report_path=None):
    """
    Run every intake validation and save the structured JSON report.

    Input: source filepath, expected column names, and optional report filepath.
    Output: A dictionary containing validation messages, statuses, and statistics.
    Assumption: CSV input is used for this sample workflow.
    """
    source_path = Path(filepath)
    repository_root = Path(__file__).resolve().parents[1]
    report_path = Path(report_path or repository_root / "output/intake_report.json")
    report = {
        "timestamp": datetime.now().isoformat(),
        "filepath": str(source_path),
        "validations": {},
        "validation_status": {},
    }

    # Stop early when the source is absent or empty; these checks gate all others.
    file_exists, message = validate_file_exists(source_path)
    report["validations"]["file_exists"] = message
    report["validation_status"]["file_exists"] = file_exists
    if not file_exists:
        _save_report(report, report_path)
        return report

    # Check the extension before loading the sample as a CSV.
    format_valid, message = validate_file_format(source_path)
    report["validations"]["format"] = message
    report["validation_status"]["format"] = format_valid

    # Load the source table for schema and dimension checks.
    df = pd.read_csv(source_path)

    schema_valid, message = validate_schema(df, expected_columns)
    report["validations"]["schema"] = message
    report["validation_status"]["schema"] = schema_valid

    # Detect and document the source encoding independently from pandas loading.
    _, message = detect_encoding(source_path)
    report["validations"]["encoding"] = message
    report["validation_status"]["encoding"] = True

    report["statistics"] = capture_dataset_stats(source_path, df)
    _save_report(report, report_path)
    return report


def _save_report(report, report_path):
    """Write a report dictionary as indented UTF-8 JSON."""
    # Ensure the report can be written even when output/ did not exist yet.
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as file_handle:
        json.dump(report, file_handle, indent=2, default=str)


if __name__ == "__main__":
    # Resolve the fixture from the repository root for consistent CLI execution.
    repository_root = Path(__file__).resolve().parents[1]
    sample_path = repository_root / "data/raw/sample.csv"
    expected_schema = [
        "customer_id",
        "customer_name",
        "transaction_amount",
        "transaction_date",
    ]
    intake_report = generate_intake_report(sample_path, expected_schema)

    # Print a compact summary so command-line runs clearly show the gate result.
    all_valid = all(intake_report["validation_status"].values())
    print(f"Intake validation: {'PASS' if all_valid else 'FAIL'}")
    print(f"Report saved to: {repository_root / 'output/intake_report.json'}")