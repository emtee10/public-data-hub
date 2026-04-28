from pathlib import Path
import re
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
DATASET_DIR = SCRIPT_DIR.parent
RAW_DIR = DATASET_DIR / "raw"
PROCESSED_DIR = DATASET_DIR / "processed"

DEDUP_KEYS = [
    "public_health_unit",
    "virus",
    "start_of_time_period",
]

OUTPUT_COLUMNS = [
    "public_health_unit",
    "virus",
    "surveillance_period",
    "surveillance_week",
    "start_of_time_period",
    "end_of_time_period",
    "positive_tests",
    "total_tests",
]

COLUMN_MAP = {
    "public_health_unit": "public_health_unit",
    "virus": "virus",
    "surveillance_period": "surveillance_period",
    "surveillance_week": "surveillance_week",
    "start_of_time_period": "start_of_time_period",
    "end_of_time_period": "end_of_time_period",
    "week_start_date": "start_of_time_period",
    "week_end_date": "end_of_time_period",
    "total_number_of_positive_tests": "positive_tests",
    "number_of_positive_tests": "positive_tests",
    "of_positive_tests": "positive_tests",
    "positive_tests": "positive_tests",
    "total_number_of_tests": "total_tests",
    "number_of_tests": "total_tests",
    "total_tests": "total_tests",
}


def extract_file_date(path: Path) -> str:
    match = re.match(r"(\d{4}-\d{2}-\d{2})_", path.name)
    if not match:
        raise ValueError(f"Raw file does not start with YYYY-MM-DD_: {path.name}")
    return match.group(1)


def get_latest_raw_file() -> Path:
    dated_files = []

    for file in RAW_DIR.glob("*.csv"):
        try:
            file_date = extract_file_date(file)
            dated_files.append((file_date, file))
        except ValueError:
            continue

    if not dated_files:
        raise FileNotFoundError(
            f"No raw CSV files with YYYY-MM-DD_ prefix found in {RAW_DIR}"
        )

    return sorted(dated_files, key=lambda x: x[0])[-1][1]


def standardize_column_name(name: str) -> str:
    name = str(name).strip().lower()
    name = name.replace("#", "number")
    name = name.replace("%", "percent")
    name = re.sub(r"[^a-z0-9]+", "_", name)
    name = re.sub(r"_+", "_", name)
    return name.strip("_")


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [standardize_column_name(col) for col in df.columns]
    df = df.rename(columns={col: COLUMN_MAP.get(col, col) for col in df.columns})
    return df


def clean_lab_data(df: pd.DataFrame) -> pd.DataFrame:
    df = standardize_columns(df)

    missing_columns = [col for col in OUTPUT_COLUMNS if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing expected columns: {missing_columns}")

    # Keep only the canonical processed fields.
    # This intentionally drops percent positivity and any other source-only fields.
    df = df[OUTPUT_COLUMNS].copy()

    df["start_of_time_period"] = pd.to_datetime(
        df["start_of_time_period"], errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    df["end_of_time_period"] = pd.to_datetime(
        df["end_of_time_period"], errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    df["surveillance_week"] = pd.to_numeric(
        df["surveillance_week"], errors="coerce"
    ).astype("Int64")

    df["positive_tests"] = pd.to_numeric(
        df["positive_tests"], errors="coerce"
    ).astype("Int64")

    df["total_tests"] = pd.to_numeric(
        df["total_tests"], errors="coerce"
    ).astype("Int64")

    df = df.dropna(subset=DEDUP_KEYS)

    return df


def load_existing_current(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    existing = pd.read_csv(path)
    existing = clean_lab_data(existing)

    return existing


def count_conflicts(existing_df: pd.DataFrame, new_df: pd.DataFrame) -> int:
    if existing_df.empty:
        return 0

    merged = existing_df.merge(
        new_df,
        on=DEDUP_KEYS,
        how="inner",
        suffixes=("_existing", "_new"),
    )

    if merged.empty:
        return 0

    compare_columns = [
        col for col in OUTPUT_COLUMNS
        if col not in DEDUP_KEYS
    ]

    conflict_mask = pd.Series(False, index=merged.index)

    for col in compare_columns:
        existing_col = f"{col}_existing"
        new_col = f"{col}_new"

        conflict_mask = conflict_mask | (
            merged[existing_col].astype("string").fillna("")
            != merged[new_col].astype("string").fillna("")
        )

    return int(conflict_mask.sum())


def dataframes_are_equal(df1: pd.DataFrame, df2: pd.DataFrame) -> bool:
    df1 = df1[OUTPUT_COLUMNS].reset_index(drop=True)
    df2 = df2[OUTPUT_COLUMNS].reset_index(drop=True)

    return df1.astype("string").equals(df2.astype("string"))


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    raw_file = get_latest_raw_file()
    raw_file_date = extract_file_date(raw_file)

    print(f"Processing latest raw file: {raw_file.name}")

    new_rows = pd.read_csv(raw_file)
    new_rows = clean_lab_data(new_rows)

    duplicate_new_rows = int(new_rows.duplicated(subset=DEDUP_KEYS).sum())

    if duplicate_new_rows:
        print(
            f"Found {duplicate_new_rows} duplicate row(s) within the new raw file. "
            "Keeping the last row for each public health unit, virus, and week."
        )
        new_rows = new_rows.drop_duplicates(subset=DEDUP_KEYS, keep="last")
    else:
        print("No duplicate rows found within the new raw file.")

    current_path = PROCESSED_DIR / "current.csv"
    dated_path = PROCESSED_DIR / f"current_{raw_file_date}.csv"

    existing_df = load_existing_current(current_path)

    current_conflicts = count_conflicts(existing_df, new_rows)

    if current_conflicts:
        print(
            f"Found {current_conflicts} conflict(s) between new data and existing "
            "current.csv. They were resolved by treating the new data as the "
            "source of truth."
        )
    else:
        print("No conflicts found between new data and existing current.csv.")

    combined = pd.concat([existing_df, new_rows], ignore_index=True)

    # Existing rows come first and new rows come second.
    # Therefore, keep='last' means new data overwrites existing rows.
    combined = combined.drop_duplicates(subset=DEDUP_KEYS, keep="last")
    combined = combined.drop_duplicates(keep="last")

    combined = combined.sort_values(
        by=["start_of_time_period", "public_health_unit", "virus"],
        ascending=[False, True, True],
        kind="stable",
    ).reset_index(drop=True)

    combined = combined[OUTPUT_COLUMNS]

    if not existing_df.empty and dataframes_are_equal(existing_df, combined):
        print("Processed output is unchanged. No files were updated.")
        return

    combined.to_csv(current_path, index=False)
    combined.to_csv(dated_path, index=False)

    print(f"Saved updated dataset to {current_path}")
    print(f"Saved dated archive copy to {dated_path}")
    print(f"Final row count: {len(combined):,}")


if __name__ == "__main__":
    main()