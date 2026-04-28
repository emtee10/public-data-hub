from datetime import date
from pathlib import Path
import requests

RAW_DIR = Path(__file__).resolve().parent.parent / "raw"

FILES = {
    "ORVT_Lab_Testing_Data_2024-25_2025-26.csv": "https://ws1.publichealthontario.ca/appdata/powerbi/ORVT/ORVT_Lab_Testing_Data_2024-25_2025-26.csv",
}


def download_file_bytes(url: str) -> bytes:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return response.content

def get_latest_existing_file(filename: str) -> Path | None:
    matches = sorted(RAW_DIR.glob(f"????-??-??_{filename}"))
    return matches[-1] if matches else None

def files_are_identical(new_content: bytes, existing_path: Path) -> bool:
    return existing_path.read_bytes() == new_content

def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
   
    for filename, url in FILES.items():
        new_content = download_file_bytes(url)
        latest_existing = get_latest_existing_file(filename)

        if latest_existing is not None and files_are_identical(new_content, latest_existing):
            print(f"No change detected for {filename}; latest file remains {latest_existing.name}")
            continue

        output_path = RAW_DIR / f"{today}_{filename}"
        output_path.write_bytes(new_content)
        print(f"Downloaded new version: {url} -> {output_path}")


if __name__ == "__main__":
    main()