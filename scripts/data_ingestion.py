"""Module 1 — CSV & JSON Data Ingestion

Provides robust ingestion for CSV and JSON datasets with:
- Explicit delimiter and character encoding specification
- Automatic encoding fallback (e.g., UTF-8, Latin-1, CP1252, ISO-8859-1)
- Nested JSON flattening using pandas.json_normalize
- Structured ingestion reporting (source, dimensions, dtypes, sample records)
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd


DEFAULT_FALLBACK_ENCODINGS = ("utf-8", "latin1", "cp1252", "iso-8859-1")


def ingest_csv(
    filepath: Union[str, Path],
    delimiter: str = ",",
    encoding: str = "utf-8",
    fallback_encodings: Tuple[str, ...] = DEFAULT_FALLBACK_ENCODINGS,
    **kwargs: Any,
) -> Tuple[pd.DataFrame, str]:
    """
    Ingest a CSV file with an explicit delimiter, encoding, and fallback logic.

    Parameters:
        filepath: Path to the CSV file.
        delimiter: Column separator (default is ',').
        encoding: Initial character encoding to attempt (default 'utf-8').
        fallback_encodings: Encodings to try sequentially if encoding errors occur.
        **kwargs: Additional keyword arguments passed to pd.read_csv.

    Returns:
        Tuple of (DataFrame, encoding_used).

    Raises:
        FileNotFoundError: If the file does not exist.
        UnicodeDecodeError: If all encoding attempts fail.
        ValueError: If file is empty or corrupted.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    if path.stat().st_size == 0:
        raise ValueError(f"CSV file is empty: {path}")

    # Build sequence of encodings to try (initial encoding first, then fallbacks)
    encodings_to_try: List[str] = [encoding]
    for enc in fallback_encodings:
        if enc.lower() not in [e.lower() for e in encodings_to_try]:
            encodings_to_try.append(enc)

    last_error: Optional[Exception] = None

    for enc in encodings_to_try:
        try:
            df = pd.read_csv(path, sep=delimiter, encoding=enc, **kwargs)
            return df, enc
        except (UnicodeDecodeError, UnicodeError) as err:
            last_error = err
            continue

    raise UnicodeDecodeError(
        f"Failed to decode {path} using encodings {encodings_to_try}. Last error: {last_error}"
    )


def ingest_json(
    filepath: Union[str, Path],
    flatten: bool = True,
    record_path: Optional[Union[str, List[str]]] = None,
    meta: Optional[List[Union[str, List[str]]]] = None,
    encoding: str = "utf-8",
    fallback_encodings: Tuple[str, ...] = DEFAULT_FALLBACK_ENCODINGS,
    sep: str = "_",
    **kwargs: Any,
) -> Tuple[pd.DataFrame, str]:
    """
    Ingest a JSON file with support for nested structure flattening via json_normalize.

    Parameters:
        filepath: Path to the JSON file.
        flatten: Whether to flatten nested dictionaries using pd.json_normalize.
        record_path: Path in each object to list of records (for deep nesting).
        meta: Fields to use as metadata for each record in resulting table.
        encoding: Initial character encoding to attempt.
        fallback_encodings: Encodings to try if decoding fails.
        sep: Separator used for joined flattened column names (default '_').
        **kwargs: Additional keyword arguments passed to json_normalize or pd.read_json.

    Returns:
        Tuple of (DataFrame, encoding_used).

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If JSON content is invalid or empty.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")

    if path.stat().st_size == 0:
        raise ValueError(f"JSON file is empty: {path}")

    encodings_to_try: List[str] = [encoding]
    for enc in fallback_encodings:
        if enc.lower() not in [e.lower() for e in encodings_to_try]:
            encodings_to_try.append(enc)

    data = None
    successful_encoding = None
    last_error: Optional[Exception] = None

    for enc in encodings_to_try:
        try:
            with open(path, "r", encoding=enc) as f:
                data = json.load(f)
            successful_encoding = enc
            break
        except (UnicodeDecodeError, UnicodeError) as err:
            last_error = err
            continue
        except json.JSONDecodeError as err:
            raise ValueError(f"Invalid JSON format in {path}: {err}") from err

    if data is None or successful_encoding is None:
        raise UnicodeDecodeError(
            f"Failed to decode {path} using encodings {encodings_to_try}. Last error: {last_error}"
        )

    if flatten:
        df = pd.json_normalize(data, record_path=record_path, meta=meta, sep=sep, **kwargs)
    else:
        df = pd.DataFrame(data)

    return df, successful_encoding


def generate_ingestion_report(
    df: pd.DataFrame,
    source_filepath: Union[str, Path],
    file_type: str,
    encoding_used: str,
    delimiter_used: Optional[str] = None,
    flattened: bool = False,
    report_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """
    Generate an ingestion audit report containing dataset dimensions, data types, and sample data.

    Parameters:
        df: Ingested Pandas DataFrame.
        source_filepath: Path to the ingested source file.
        file_type: Type of the source file ('csv' or 'json').
        encoding_used: Character encoding successfully applied.
        delimiter_used: Column delimiter (if CSV).
        flattened: Whether nested structures were flattened (if JSON).
        report_path: Optional path to save report as JSON.

    Returns:
        Dictionary containing ingestion metadata and profiling summary.
    """
    path = Path(source_filepath)
    file_size_bytes = path.stat().st_size if path.exists() else 0

    report: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "source_file": str(path.name),
        "source_path": str(path.as_posix()),
        "file_type": file_type.upper(),
        "file_size_bytes": file_size_bytes,
        "file_size_kb": round(file_size_bytes / 1024, 2),
        "encoding_used": encoding_used,
        "delimiter_used": delimiter_used,
        "flattened_nested_structures": flattened,
        "shape": {
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
        },
        "columns": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "null_counts": {col: int(df[col].isna().sum()) for col in df.columns},
        "sample_records": df.head(3).to_dict(orient="records"),
    }

    if report_path is not None:
        save_path = Path(report_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)

    return report


def run_ingestion_demo() -> None:
    """Execute ingestion demonstration on sample CSV and nested JSON datasets."""
    repo_root = Path(__file__).resolve().parents[1]
    raw_data_dir = repo_root / "data/raw"
    output_dir = repo_root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("MODULE 1: CSV & JSON DATA INGESTION PIPELINE")
    print("=" * 70)

    # 1. Ingest Sample CSV
    csv_file = raw_data_dir / "sample.csv"
    if csv_file.exists():
        print(f"\n[1] Ingesting CSV: {csv_file.name} (delimiter=',', encoding='utf-8')")
        df_csv, enc_csv = ingest_csv(csv_file, delimiter=",", encoding="utf-8")
        report_csv = generate_ingestion_report(
            df_csv,
            source_filepath=csv_file,
            file_type="csv",
            encoding_used=enc_csv,
            delimiter_used=",",
            report_path=output_dir / "ingestion_report_csv.json",
        )
        print(f"  [OK] Rows: {report_csv['shape']['rows']}, Columns: {report_csv['shape']['columns']}")
        print(f"  [OK] Columns: {', '.join(report_csv['columns'])}")
        print(f"  [OK] Encoding: {enc_csv}")
        print(f"  [OK] Report saved to: output/ingestion_report_csv.json")

    # 2. Ingest Nested JSON
    json_file = raw_data_dir / "viewers_nested.json"
    if json_file.exists():
        print(f"\n[2] Ingesting Nested JSON with json_normalize: {json_file.name}")
        df_json, enc_json = ingest_json(json_file, flatten=True, encoding="utf-8")
        report_json = generate_ingestion_report(
            df_json,
            source_filepath=json_file,
            file_type="json",
            encoding_used=enc_json,
            flattened=True,
            report_path=output_dir / "ingestion_report_json.json",
        )
        print(f"  [OK] Rows: {report_json['shape']['rows']}, Columns: {report_json['shape']['columns']}")
        print(f"  [OK] Flattened Columns: {', '.join(report_json['columns'])}")
        print(f"  [OK] Encoding: {enc_json}")
        print(f"  [OK] Report saved to: output/ingestion_report_json.json")

    print("\n" + "=" * 70)
    print("[SUCCESS] Ingestion pipeline completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    run_ingestion_demo()
