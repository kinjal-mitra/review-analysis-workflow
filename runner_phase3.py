# runner_phase4.py

from review_analysis.workflow_phase3 import build_phase4_workflow


def run_phase4(
    product_id: str,
    input_dir: str = "output",
    output_dir: str = "output",
):
    graph = build_phase4_workflow()

    graph.invoke(
        {
            "product_id": product_id,
            "input_dir": input_dir,
            "output_dir": output_dir,
        }
    )

    print("\n✅ PHASE-4 TREND AGGREGATION COMPLETE")


if __name__ == "__main__":
    run_phase4(
        product_id="in.swiggy.android",
        input_dir="output",
        output_dir="output",
    )
