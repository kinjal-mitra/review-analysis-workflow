# runner_phase1.py

from review_analysis.workflow_phase1 import build_review_workflow


def run(
    app_url: str,
    target_date: str,
    lookback_days: int = 3,
):
    """
    Entry point for review ingestion + daily segmentation workflow
    """

    graph = build_review_workflow()

    final_state = graph.invoke(
        {
            "app_url": app_url,
            "target_date": target_date,
            "lookback_days": lookback_days,
        }
    )

    print("\n WORKFLOW PHASE 1 COMPLETED SUCCESSFULLY")
    print("────────────────────────────────")
    print(" Interim file:")
    print(f"   {final_state['interim_output_path']}")
    print("\n Daily processed files:")
    for path in final_state["daily_output_paths"]:
        print(f"   {path}")


if __name__ == "__main__":
    # Example run (replace with CLI later)
    run(
        app_url="https://play.google.com/store/apps/details?id=in.swiggy.android",
        target_date="2026-01-07",
        lookback_days=4,
    )
