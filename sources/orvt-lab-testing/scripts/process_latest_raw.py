from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


FILENAME_PATTERN = re.compile(r'^(\d{4}-\d{2}-\d{2})_.*\.(xlsx|xls|csv)$', re.IGNORECASE)


def dataset_base_dir() -> Path:
    script_dir = Path(__file__).resolve().parent
    if script_dir.name == 'scripts' and (script_dir.parent / 'raw').exists():
        return script_dir.parent
    return Path.cwd()


def find_latest_raw_file(raw_dir: Path) -> tuple[Path, str]:
    candidates: list[tuple[str, Path]] = []
    for path in raw_dir.iterdir():
        if not path.is_file():
            continue
        match = FILENAME_PATTERN.match(path.name)
        if match:
            candidates.append((match.group(1), path))

    if not candidates:
        raise FileNotFoundError(
            f'No raw file found in {raw_dir} matching YYYY-MM-DD_filename.xlsx/csv'
        )

    latest_date, latest_path = max(candidates, key=lambda item: item[0])
    return latest_path, latest_date


def standardize_header(header: str) -> str:
    header = str(header).strip().lower()
    header = header.replace('%', ' percent ')
    header = re.sub(r'\([^)]*\)', '', header)
    header = header.replace('/', ' ')
    header = re.sub(r'[^a-z0-9]+', '_', header)
    header = re.sub(r'_+', '_', header).strip('_')
    return header


def load_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix in {'.xlsx', '.xls'}:
        return pd.read_excel(path)
    if suffix == '.csv':
        return pd.read_csv(path)
    raise ValueError(f'Unsupported file type: {path.suffix}')


def main() -> None:
    base_dir = dataset_base_dir()
    raw_dir = base_dir / 'raw'
    processed_dir = base_dir / 'processed'
    processed_dir.mkdir(parents=True, exist_ok=True)

    latest_file, file_date = find_latest_raw_file(raw_dir)
    df = load_table(latest_file)

    df.columns = [standardize_header(col) for col in df.columns]

    rename_map = {
        'percent_positivity': 'percent_positivity',
        'total_number_of_positive_tests': 'positive_tests',
        'total_number_of_tests': 'total_tests',
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    if 'percent_positivity' in df.columns:
        df = df.drop(columns=['percent_positivity'])

    # Normalize empty strings to NA so blank rows are easy to remove.
    df = df.replace(r'^\s*$', pd.NA, regex=True)

    # Remove the footer row like "Applied filters..." if present.
    first_col = df.columns[0]
    df = df[
        ~df[first_col]
        .astype('string')
        .str.startswith('Applied filters', na=False)
    ]

    key_columns = [
        'public_health_unit',
        'virus',
        'surveillance_period',
        'surveillance_week',
        'start_of_time_period',
        'end_of_time_period',
        'positive_tests',
        'total_tests',
    ]
    present_key_columns = [col for col in key_columns if col in df.columns]
    df = df.dropna(subset=present_key_columns)

    for date_col in ['start_of_time_period', 'end_of_time_period']:
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce').dt.strftime('%Y-%m-%d')

    current_path = processed_dir / 'current.csv'
    dated_path = processed_dir / f'current_{file_date}.csv'

    df.to_csv(current_path, index=False)
    df.to_csv(dated_path, index=False)

    print(f'Latest raw file: {latest_file.name}')
    print(f'Rows written: {len(df):,}')
    print(f'Saved: {current_path}')
    print(f'Saved: {dated_path}')


if __name__ == '__main__':
    main()
