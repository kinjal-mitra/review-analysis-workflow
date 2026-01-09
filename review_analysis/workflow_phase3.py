# review_analysis/workflow_phase3.py

from typing import TypedDict, Dict, List
from pathlib import Path
import json
import pandas as pd

from langgraph.graph import StateGraph, END


# ======================================================
# Graph State
# ======================================================
class Phase4State(TypedDict):
    product_id: str
    input_dir: str
    output_dir: str

    topics: List[str]
    dates: List[str]
    topic_dates: Dict[str, Dict[str, int]]
    trend_df: pd.DataFrame


# ======================================================
# Node 1: Load Canonical Topics + Daily Counts
# ======================================================
def load_topic_counts_node(state: Phase4State) -> Phase4State:
    product_dir = Path(state["input_dir"]) / state["product_id"]

    # --------------------------------------------------
    # 1. Load canonical topics (single source of truth)
    # --------------------------------------------------
    topics_file = product_dir / "topics.json"
    if not topics_file.exists():
        raise FileNotFoundError(f"topics.json not found for {state['product_id']}")

    with open(topics_file, "r", encoding="utf-8") as f:
        topics_registry = json.load(f)

    canonical_topics = [v["label"] for v in topics_registry.values()]

    # --------------------------------------------------
    # 2. Discover all available dates
    # --------------------------------------------------
    date_files = sorted(product_dir.glob("topic_counts_*.json"))
    if not date_files:
        raise FileNotFoundError("No topic_counts_*.json files found")

    dates = [f.stem.replace("topic_counts_", "") for f in date_files]

    # --------------------------------------------------
    # 3. Initialize FULL Topic × Date matrix with zeros
    # --------------------------------------------------
    topic_dates = {
        topic: {date: 0 for date in dates}
        for topic in canonical_topics
    }

    # --------------------------------------------------
    # 4. Fill actual counts where present
    # --------------------------------------------------
    for file in date_files:
        date = file.stem.replace("topic_counts_", "")
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        for topic, count in data.get("topics", {}).items():
            if topic in topic_dates:
                topic_dates[topic][date] = count
            # else: ignore deprecated / rewritten topic labels

    state["topics"] = canonical_topics
    state["dates"] = dates
    state["topic_dates"] = topic_dates
    return state


# ======================================================
# Node 2: Build Trend Table (DataFrame)
# ======================================================
def build_trend_table_node(state: Phase4State) -> Phase4State:
    df = pd.DataFrame(
        index=state["topics"],
        columns=state["dates"],
        data=0,
        dtype=int,
    )

    for topic, date_counts in state["topic_dates"].items():
        for date, count in date_counts.items():
            df.loc[topic, date] = count

    state["trend_df"] = df
    return state


# ======================================================
# Node 3: Persist Trend Table (output/)
# ======================================================
def persist_trend_report_node(state: Phase4State) -> Phase4State:
    output_dir = Path(state["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{state['product_id']}_Topic_Trend_Table.csv"
    output_path = output_dir / filename

    state["trend_df"].to_csv(output_path)

    print(f"\n Topic trend table saved to: {output_path}")
    return state


# ======================================================
# Build LangGraph Workflow
# ======================================================
def build_phase4_workflow():
    graph = StateGraph(Phase4State)

    graph.add_node("load_counts", load_topic_counts_node)
    graph.add_node("build_table", build_trend_table_node)
    graph.add_node("persist", persist_trend_report_node)

    graph.set_entry_point("load_counts")
    graph.add_edge("load_counts", "build_table")
    graph.add_edge("build_table", "persist")
    graph.add_edge("persist", END)

    return graph.compile()
