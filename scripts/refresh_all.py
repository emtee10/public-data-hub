from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent

DATASETS = [
    "sources/imm-coverage",
    "sources/orvt-lab-testing",
    "sources/orvt-outcomes",
]

def run_script(script_path: Path) -> None:
    print(f"\nRunning {script_path}...")
    result = subprocess.run([sys.executable, str(script_path)], cwd=REPO_ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Script failed: {script_path}")

def main() -> None:
    for dataset in DATASETS:
        dataset_path = REPO_ROOT / dataset / "scripts"

        get_script = dataset_path / "get.py"
        process_script = dataset_path / "process.py"

        if get_script.exists():
            run_script(get_script)

        if process_script.exists():
            run_script(process_script)

    print("\nAll datasets refreshed successfully.")

if __name__ == "__main__":
    main()