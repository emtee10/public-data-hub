#!/usr/bin/env python3
"""
Combine immunization coverage files from raw/ into a single processed/current.csv.

Expected raw filenames include:
- YYYY-MM-DD_*coverage_by_age*.csv
- YYYY-MM-DD_*coverage_by_milestone*.csv

What the script does:
1. Finds the most recent raw file for each type based on the YYYY-MM-DD prefix.
2. Standardizes column headers.
3. Combines the two files into one table.
4. Resolves conflicts between the two input files using these rules:
   - The more recent input file wins.
   - If both files have the same date, coverage_by_age wins.
   - A terminal message reports the number of conflicts and how they were handled.
5. If processed/current.csv already exists, merges new rows into it.
6. Resolves conflicts between new rows and existing current.csv by keeping the new row.
   - A terminal message reports the number of conflicts and how they were handled.
7. Removes exact duplicate rows.
8. Saves the result to processed/current.csv.

Run from the dataset root or from scripts/.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


DATE_PREFIX_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})_")
STANDARD_COLUMNS = {
    "year": "school_year",
    "antigen": "antigen",
    "age": "age",
    "public_health_unit": "public_health_unit",
    "coverage": "coverage",
}
OUTPUT_COLUMNS = ["school_year", "antigen", "age", "public_health_unit", "coverage"]
DEDUP_KEYS = ["school_year", "antigen", "age", "public_health_unit"]


def standardize_header(value: str) -> str:
    value = str(value).strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return STANDARD_COLUMNS.get(value, value)


def get_dataset_root() -> Path:
    here = Path(__file__).resolve().parent
    if (here / "raw").exists():
        return here
    if (here.parent / "raw").exists():
        return here.parent
    raise FileNotFoundError(
        "Could not find a dataset root containing a raw/ folder. "
        "Run this script from the dataset root or store it in scripts/ beneath it."
    )


def parse_date_prefix(path: Path) -> str | None:
    match = DATE_PREFIX_RE.match(path.name)
    return match.group(1) if match else None


def find_latest_raw_file(raw_dir: Path, keyword: str) -> tuple[Path, str]:
    matches: list[tuple[str, Path]] = []
    for path in raw_dir.glob("*.csv"):
        date_prefix = parse_date_prefix(path)
        if date_prefix and keyword in path.name.lower():
            matches.append((date_prefix, path))

    if not matches:
        raise FileNotFoundError(
            f"No raw CSV file found in {raw_dir} containing '{keyword}' "
            "with a YYYY-MM-DD filename prefix."
        )

    latest_date, latest_path = max(matches, key=lambda item: item[0])
    return latest_path, latest_date


def load_and_standardize(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df.columns = [standardize_header(col) for col in df.columns]

    missing = [col for col in OUTPUT_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(
            f"{csv_path.name} is missing expected columns after standardization: {missing}"
        )

    df = df[OUTPUT_COLUMNS].copy()

    df["school_year"] = df["school_year"].astype(str).str.strip()
    df["antigen"] = df["antigen"].astype(str).str.strip()
    df["public_health_unit"] = df["public_health_unit"].astype(str).str.strip()
    df["age"] = pd.to_numeric(df["age"], errors="coerce").astype("Int64")
    df["coverage"] = pd.to_numeric(df["coverage"], errors="coerce")

    df = df.dropna(subset=["school_year", "antigen", "age", "public_health_unit", "coverage"])
    return df


def load_existing_current(current_path: Path) -> pd.DataFrame:
    if not current_path.exists():
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    df = pd.read_csv(current_path)
    df.columns = [standardize_header(col) for col in df.columns]

    missing = [col for col in OUTPUT_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(
            f"Existing current.csv is missing expected columns after standardization: {missing}"
        )

    df = df[OUTPUT_COLUMNS].copy()
    df["school_year"] = df["school_year"].astype(str).str.strip()
    df["antigen"] = df["antigen"].astype(str).str.strip()
    df["public_health_unit"] = df["public_health_unit"].astype(str).str.strip()
    df["age"] = pd.to_numeric(df["age"], errors="coerce").astype("Int64")
    df["coverage"] = pd.to_numeric(df["coverage"], errors="coerce")
    df = df.dropna(subset=["school_year", "antigen", "age", "public_health_unit", "coverage"])
    return df


def count_conflicts(left: pd.DataFrame, right: pd.DataFrame) -> int:
    if left.empty or right.empty:
        return 0
    left_cmp = left[DEDUP_KEYS + ["coverage"]].rename(columns={"coverage": "coverage_left"})
    right_cmp = right[DEDUP_KEYS + ["coverage"]].rename(columns={"coverage": "coverage_right"})
    merged = left_cmp.merge(right_cmp, on=DEDUP_KEYS, how="inner")
    if merged.empty:
        return 0
    return int((merged["coverage_left"] != merged["coverage_right"]).sum())


def choose_input_priority(
    age_df: pd.DataFrame,
    age_date: str,
    milestone_df: pd.DataFrame,
    milestone_date: str,
) -> tuple[pd.DataFrame, pd.DataFrame, str, str]:
    if age_date > milestone_date:
        return age_df, milestone_df, "coverage_by_age", "more recent input file"
    if milestone_date > age_date:
        return milestone_df, age_df, "coverage_by_milestone", "more recent input file"
    return age_df, milestone_df, "coverage_by_age", "same file date, so coverage_by_age was preferred"

def derive_year_of_birth(school_year: str, age: int) -> int | None:
    if pd.isna(school_year) or pd.isna(age):
        return None

    school_year = str(school_year).strip()

    # expects formats like "2024-25" or "2024-2025"
    if "-" not in school_year:
        return None

    first_part = school_year.split("-")[0].strip()

    try:
        assessment_year = int(first_part)
        return assessment_year - int(age)
    except ValueError:
        return None

def main() -> None:
    dataset_root = get_dataset_root()
    raw_dir = dataset_root / "raw"
    processed_dir = dataset_root / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    age_path, age_date = find_latest_raw_file(raw_dir, "coverage_by_age")
    milestone_path, milestone_date = find_latest_raw_file(raw_dir, "coverage_by_milestone")

    age_df = load_and_standardize(age_path)
    milestone_df = load_and_standardize(milestone_path)

    preferred_input_df, secondary_input_df, preferred_input_name, preferred_reason = choose_input_priority(
        age_df, age_date, milestone_df, milestone_date
    )
    input_conflicts = count_conflicts(age_df, milestone_df)

    new_rows = pd.concat([secondary_input_df, preferred_input_df], ignore_index=True)
    new_rows = new_rows.drop_duplicates(subset=DEDUP_KEYS, keep="last")

    current_path = processed_dir / "current.csv"
    dated_path = processed_dir / f"current_{max(age_date, milestone_date)}.csv"

    existing_df = load_existing_current(current_path)
    current_conflicts = count_conflicts(existing_df, new_rows)

    combined = pd.concat([existing_df, new_rows], ignore_index=True)
    combined = combined.drop_duplicates(subset=DEDUP_KEYS, keep="last")
    combined = combined.drop_duplicates(keep="last")

    combined = combined.sort_values(
        by=["school_year", "antigen", "public_health_unit", "age"],
        kind="stable",
    ).reset_index(drop=True)

    combined["age"] = combined["age"].astype("Int64")
    combined["year_of_birth"] = combined.apply(
        lambda row: derive_year_of_birth(row["school_year"], row["age"]),
        axis=1,
    )
    combined["year_of_birth"] = combined["year_of_birth"].astype("Int64")

    combined.to_csv(current_path, index=False)
    combined.to_csv(dated_path, index=False)

    print(f"Loaded age file: {age_path.name}")
    print(f"Loaded milestone file: {milestone_path.name}")

    if input_conflicts == 0:
        print("No conflicts found between coverage_by_age and coverage_by_milestone.")
    else:
        print(
            f"Found {input_conflicts} conflict(s) between coverage_by_age and coverage_by_milestone. "
            f"They were resolved by treating {preferred_input_name} as the source of truth "
            f"because it was the {preferred_reason}."
        )

    if current_conflicts == 0:
        print("No conflicts found between new input data and existing current.csv.")
    else:
        print(
            f"Found {current_conflicts} conflict(s) between new input data and existing current.csv. "
            "They were resolved by treating the new input data as the source of truth."
        )

    print(f"Merged rows written to: {current_path}")
    print(f"Total rows in current.csv: {len(combined)}")


if __name__ == "__main__":
    main()
