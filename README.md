# Public Data Hub

This repository hosts externally sourced datasets used for dashboarding and analysis. It is designed for personal use, experimentation, and learning.

## Purpose
- Store publicly available data from external organizations
- Maintain cleaned, analysis-ready datasets
- Provide stable data sources for Power BI dashboards

## Setup

### Option 1 - Dev Container

Open the repository in GitHub Codespaces or in VS Code using "Reopen in Container".

Dependencies will be installed automatically as part of the container setup.

### Option 2 - Local Setup

Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## Structure

### `/sources/`
Each dataset has its own folder containing:
- `raw/`: original downloaded files
- `processed/`: cleaned and standardized files
- `scripts/`: dataset-specific processing scripts
  - `process_latest_raw.py`: process latest raw file
- `README.md`: source-specific readme file

### `/docs/`
Cross-cutting documentation:
- data catalog
- update processes
- conventions

## Power BI usage

Power BI should connect to: `sources/<dataset-name>/processed/current.csv`

These files are stable and updated as new data becomes available.

## Update approach

Data is updated manually or via scripts:
1. Download latest data → `raw/`
2. Clean/transform → `processed/`
3. Update `current.csv`
4. Archive dated snapshot

## Naming conventions

- Folders: lowercase-with-hyphens
- Files: ISO date prefix where applicable (`YYYY-MM-DD`)
- Columns: lowercase_with_underscores

## Notes

This is a lightweight data pipeline intended for:
- prototyping
- public dashboards
- exploratory analysis

Future enhancements may include:
- automated updates
- curated output layer
- validation scripts