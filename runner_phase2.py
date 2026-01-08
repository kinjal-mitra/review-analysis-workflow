# runner_phase3.py

from pathlib import Path
import re
import time

from review_analysis.workflow_phase2 import build_phase3_workflow


PROCESSED_DIR = Path("data/processed")

MAX_MISTRAL_CALLS_PER_DAY = 100
DAY_DELAY_SECONDS = 60


def parse_filename(filename: str):
    """
    reviews_<product_id>_<YYYY-MM-DD>.json
    """
    match = re.match(r"reviews_(.+)_(\d{4}-\d{2}-\d{2})\.json", filename)
    if not match:
        return None, None
    return match.group(1), match.group(2)


def run_phase3_all_days(
    batch_size: int = 10,
    output_dir: str = "output",
):
    graph = build_phase3_workflow()
    product_files = {}

    for file in PROCESSED_DIR.glob("reviews_*.json"):
        product_id, date = parse_filename(file.name)
        if product_id:
            product_files.setdefault(product_id, []).append((date, file))

    if not product_files:
        print("❌ No processed review files found.")
        return

    for product_id, entries in product_files.items():
        print(f"\n🧠 Processing product: {product_id}")
        entries.sort(key=lambda x: x[0])

        for date, file_path in entries:
            print(f"  📅 Processing date: {date}")

            try:
                graph.invoke(
                    {
                        "product_id": product_id,
                        "date": date,
                        "input_file": str(file_path),
                        "batch_size": batch_size,
                        "output_dir": output_dir,
                        "mistral_calls": 0,
                        "max_mistral_calls": MAX_MISTRAL_CALLS_PER_DAY,
                    }
                )
            except Exception as e:
                print(f"  ⚠️ Failed for {date}: {e}")

            print(f"  ⏳ Waiting {DAY_DELAY_SECONDS}s before next day...")
            time.sleep(DAY_DELAY_SECONDS)

        print(f"✅ Completed product: {product_id}")


if __name__ == "__main__":
    run_phase3_all_days(
        batch_size=10,
        output_dir="output",
    )
