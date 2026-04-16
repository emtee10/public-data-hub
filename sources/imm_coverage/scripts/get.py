from datetime import date
from pathlib import Path
import requests

RAW_DIR = Path(__file__).resolve().parent.parent / "raw"

FILES = {
    "Coverage_by_age_2024_25.csv": "https://ws1.publichealthontario.ca/appdata/powerbi/Immunization/Coverage_by_age_2024_25.csv",
    "Coverage_by_milestone_2015_25.csv": "https://ws1.publichealthontario.ca/appdata/powerbi/Immunization/Coverage_by_milestone_2015_25.csv",
}


def download_file(url: str, output_path: Path) -> None:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    output_path.write_bytes(response.content)


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()

    for filename, url in FILES.items():
        output_path = RAW_DIR / f"{today}_{filename}"
        download_file(url, output_path)
        print(f"Downloaded {url} -> {output_path}")


if __name__ == "__main__":
    main()