import json
import os
import re
import shutil
import subprocess
import sys
from typing import Dict, List


def parse_kaggle_dataset_slug(kaggle_url: str) -> str:
    """
    Convert a Kaggle URL to owner/dataset slug.
    Example: https://www.kaggle.com/datasets/zusmani/qs-top-universities -> zusmani/qs-top-universities
    """
    pattern = r"kaggle\.com/datasets/([^/]+/[^/?#]+)"
    match = re.search(pattern, kaggle_url)
    if not match:
        raise ValueError(f"Invalid Kaggle dataset URL: {kaggle_url}")
    return match.group(1)


def ensure_kaggle_cli() -> None:
    if shutil.which("kaggle") is None:
        raise RuntimeError(
            "Kaggle CLI not found. Install with `pip install kaggle` and make sure `kaggle` is on PATH."
        )


def load_sources(config_path: str) -> List[Dict]:
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("sources", [])


def download_source(source: Dict, out_dir: str) -> None:
    name = source.get("name", "Unnamed source")
    kaggle_url = source.get("kaggle_url", "").strip()

    if not source.get("enabled", True):
        print(f"[SKIP] {name} (disabled)")
        return

    if not kaggle_url:
        print(f"[SKIP] {name} (missing kaggle_url)")
        return

    dataset_slug = parse_kaggle_dataset_slug(kaggle_url)
    safe_name = re.sub(r"[^a-zA-Z0-9_-]+", "_", name.lower()).strip("_")
    target_dir = os.path.join(out_dir, safe_name)
    os.makedirs(target_dir, exist_ok=True)

    print(f"[DOWNLOAD] {name}")
    print(f"  -> dataset: {dataset_slug}")
    print(f"  -> output:  {target_dir}")

    cmd = [
        "kaggle",
        "datasets",
        "download",
        "-d",
        dataset_slug,
        "-p",
        target_dir,
        "--unzip",
    ]
    subprocess.run(cmd, check=True)

    expected_csv = source.get("expected_csv")
    if expected_csv:
        expected_path = os.path.join(target_dir, expected_csv)
        if os.path.exists(expected_path):
            print(f"  -> found expected file: {expected_csv}")
        else:
            print(f"  -> warning: expected file not found: {expected_csv}")


def main() -> int:
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(repo_root, "data", "university_sources.json")
    out_dir = os.path.join(repo_root, "data", "raw_rankings")

    try:
        ensure_kaggle_cli()
    except RuntimeError as e:
        print(f"[ERROR] {e}")
        return 1

    if not os.path.exists(config_path):
        print(f"[ERROR] Missing config file: {config_path}")
        return 1

    try:
        sources = load_sources(config_path)
        if not sources:
            print("[ERROR] No sources found in university_sources.json")
            return 1

        for src in sources:
            try:
                download_source(src, out_dir)
            except Exception as e:
                print(f"[ERROR] Failed to process source '{src.get('name', 'Unknown')}': {e}")

        print("\nDone. Raw ranking files are in backend/data/raw_rankings/")
        print("Next: build a merge/normalize step to generate backend/data/universities.csv")
        return 0
    except Exception as e:
        print(f"[ERROR] {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
