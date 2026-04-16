# orvt-lab-testing

## Source
Public Health Ontario [\[Link\]](https://www.publichealthontario.ca/)

## Description
This dataset contains laboratory testing data downloaded from the Ontario Respiratory Virus Tool, hosted by Public Health Ontario. Includes all available public health units, viruses, and surveillance periods. Includes columns for Surveillance period and Surveillance week.

## Original source
[\[Link to source\]](https://www.publichealthontario.ca/en/Data-and-Analysis/Infectious-Disease/Respiratory-Virus-Tool)

## Update frequency
Weekly

## Folder contents

- `raw/`: original downloaded files
- `processed/`: cleaned files used for analysis
- `metadata/`: data dictionary and source details
- `scripts/`: data processing scripts

## Power BI file

`processed\current.csv`

## Key Transformations

- Standardized field names
- Remove percent positivity (can be derived more reliably)
- Removed non-data rows
- Removed footer row
- Converted .xlsx to .csv

## Data Fields (Processed File)

| Field Name        | Description |
|------------------------|---------|
| `public_health_unit`  | Public health unit (or province of Ontario) |
| `virus`                 | Virus being tested |
| `surveillance_period`           | Surveillance season |
| `surveillance_week`           | Week within surveillance season |
| `start_of_time_period`       | Calendar date for start of surveillance week |
| `end_of_time_period`    | Calendar date for end of surveillance week |
| `positive_tests`    | Number of positive tests (numerator for percent positivity) |
| `total_tests`    | Total number of tests (denominator for percent positivity) |