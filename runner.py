# runner_end_to_end.py

from review_analysis.workflow import build_end_to_end_workflow
from review_analysis.dataset import extract_play_store_id


def run_end_to_end(
    app_url: str,
    target_date: str,
    lookback_days: int = 3,
):
    product_id = extract_play_store_id(app_url)
    if not product_id:
        raise ValueError("Invalid Play Store URL")

    graph = build_end_to_end_workflow()

    graph.invoke(
        {
            "app_url": app_url,
            "target_date": target_date,
            "lookback_days": lookback_days,
            "product_id": product_id,
        }
    )

    print("\n END-TO-END PIPELINE COMPLETED")
    print("────────────────────────────────")
    print(f" Product ID: {product_id}")
    print(f" Days processed: {lookback_days}")
    print(" Output: Topic trend table generated in output/")


if __name__ == "__main__":
    run_end_to_end(
        app_url="https://play.google.com/store/apps/details?id=in.swiggy.android",
        target_date="2026-01-07",
        lookback_days=10,
    )
