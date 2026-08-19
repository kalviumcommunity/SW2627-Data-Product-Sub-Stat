"""Run the sample data workflow from ingestion through output."""

from pathlib import Path


def ingest_data(filepath):
    """
    Load tabular data from a CSV file into a Pandas DataFrame.

    Input: filepath pointing to an existing CSV file.
    Output: Pandas DataFrame containing the raw records.
    Assumption: The file is a comma-separated table with a header row.
    """
    import pandas as pd

    # Read the raw CSV while preserving the source column names.
    return pd.read_csv(filepath)


def process_data(df):
    """
    Transform raw records into an analysis-ready DataFrame.

    Input: Pandas DataFrame returned by ingest_data.
    Output: Pandas DataFrame with duplicate rows removed and numeric nulls filled.
    Assumption: Numeric columns can use their column median as a fallback value.
    """
    # Remove exact duplicates where every value in a row is identical.
    df = df.drop_duplicates().copy()

    # Fill missing numeric values with the median of the available values.
    for column in df.select_dtypes(include="number").columns:
        df[column] = df[column].fillna(df[column].median())

    return df


def output_results(df, output_path):
    """
    Save processed data to a CSV file and print execution confirmation.

    Input: processed Pandas DataFrame and a destination filepath.
    Output: A CSV file at output_path; the DataFrame is not modified.
    Assumption: The process has permission to create the destination directory.
    """
    output_path = Path(output_path)

    # Create the destination directory when this is the first workflow run.
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    # Show a stable repository-relative path in the run confirmation.
    repository_root = Path(__file__).resolve().parents[1]
    try:
        display_path = output_path.relative_to(repository_root)
    except ValueError:
        display_path = output_path

    # Print concise evidence that the complete pipeline finished successfully.
    print("✓ Data successfully processed")
    print(f"✓ Rows processed: {len(df)}")
    print(f"✓ Output saved to {display_path}")


if __name__ == "__main__":
    # Resolve paths from the repository root so the script works from scripts/.
    repository_root = Path(__file__).resolve().parents[1]
    data = ingest_data(repository_root / "data/raw/sample.csv")
    processed = process_data(data)
    output_results(processed, repository_root / "output/processed.csv")