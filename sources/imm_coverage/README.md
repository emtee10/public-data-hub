# imm_coverage

## Source
Public Health Ontario [\[Link\]](https://www.publichealthontario.ca/)

## Description
This dataset contains immunization coverage data by antigen and public health unit. It combines two publicly available data files from Public Health Ontario's Immunization Data Tool:
- Coverage by age (detailed ages, most recent school year only)
- Coverage by milestone (selected ages, multiple historical years)

The processed dataset integrates both sources into a single, longitudinal dataset suitable for analysis and dashboarding.

## Original source
[\[Link to source\]](https://www.publichealthontario.ca/en/Data-and-Analysis/Infectious-Disease/Immunization-Tool)

## Update frequency
Periodic (typically annual or as updated by Public Health Ontario)

## Folder contents

- `raw/`: original downloaded files
- `processed/`: cleaned files used for analysis
- `scripts/`: data processing scripts

## Power BI file

`processed/current.csv`

## Scripts

- `get.py`: Load updated data to `raw/`
- `process.py`: Process most recent data from `raw/` and save to `processed/`

## Key Transformations

- Standardized field names across both input datasets
- Combined the most recent `coverage_by_age` and `coverage_by_milestone` into a single dataset
- Resolved overlapping records using deterministic rules
- Removed duplicate records
- Calculated year of birth based on age and school year
- Merged new data with existing dataset

## Data Fields (Processed File)

| Field Name        | Description |
|------------------------|---------|
| `school_year`  | School year of reporting (e.g. 2024-2025) |
| `public_health_unit` | Public health unit (or province of Ontario) |
| `antigen`           | Vaccine antigen |
| `age`           | Age of cohort (in years), based on the age that children would reach by December 31 of the school year |
| `coverage`       | Immunization coverage (%) |
| `year_of_birth`    | Year of birth of cohort |