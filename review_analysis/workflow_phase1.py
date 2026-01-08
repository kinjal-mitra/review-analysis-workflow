# review_analysis/workflow.py

from typing import TypedDict, Optional, List
from datetime import datetime, timedelta
import pandas as pd

from langgraph.graph import StateGraph, END

from review_analysis.dataset import (
    extract_play_store_id,
    fetch_reviews,
)
from review_analysis.config import (
    INTERIM_DATA_DIR,
    PROCESSED_DATA_DIR,
    client,
)

# ============================================================
# LangGraph State Definition
# ============================================================
class ReviewState(TypedDict):
    # Inputs
    app_url: str
    target_date: str
    lookback_days: int

    # Derived
    product_id: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]

    # Data
    reviews_df: Optional[pd.DataFrame]

    # Outputs
    interim_output_path: Optional[str]
    daily_output_paths: Optional[List[str]]


# ============================================================
# Node 1: Extract Product ID
# ============================================================
def extract_product_id_node(state: ReviewState) -> ReviewState:
    product_id = extract_play_store_id(state["app_url"])
    if not product_id:
        raise ValueError("Failed to extract Play Store product ID")

    state["product_id"] = product_id
    return state


# ============================================================
# Node 2: Compute Date Window
# ============================================================
def compute_date_window_node(state: ReviewState) -> ReviewState:
    target = datetime.strptime(state["target_date"], "%Y-%m-%d")
    lookback = state["lookback_days"]

    start = target - timedelta(days=lookback - 1)

    state["start_date"] = start.strftime("%Y-%m-%d")
    state["end_date"] = target.strftime("%Y-%m-%d")
    return state


# ============================================================
# Node 3: Fetch Reviews from SerpAPI
# ============================================================
def fetch_reviews_node(state: ReviewState) -> ReviewState:
    df = fetch_reviews(
        client=client,
        product_id=state["product_id"],
        START_DATE=state["start_date"],
        END_DATE=state["end_date"],
    )

    if df.empty:
        raise ValueError("No reviews fetched for the given date range")

    state["reviews_df"] = df
    return state


# ============================================================
# Node 4: Persist Interim JSON (Single File)
# ============================================================
def persist_interim_node(state: ReviewState) -> ReviewState:
    df = state["reviews_df"].copy()

    # Normalize Date format
    df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")

    INTERIM_DATA_DIR.mkdir(parents=True, exist_ok=True)

    filename = f"reviews_{state['product_id']}_T={state['end_date']}.json"
    output_path = INTERIM_DATA_DIR / filename

    df.to_json(
        output_path,
        orient="records",
        indent=4
    )

    state["interim_output_path"] = str(output_path)
    state["reviews_df"] = df  # keep normalized version
    return state


# ============================================================
# Node 5: Split Reviews by Day → data/processed
# ============================================================
def split_daily_node(state: ReviewState) -> ReviewState:
    df = state["reviews_df"]

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    daily_paths: List[str] = []

    for date, group in df.groupby("Date"):
        filename = f"reviews_{state['product_id']}_{date}.json"
        output_path = PROCESSED_DATA_DIR / filename

        group.to_json(
            output_path,
            orient="records",
            indent=4
        )

        daily_paths.append(str(output_path))

    state["daily_output_paths"] = daily_paths
    return state


# ============================================================
# Build LangGraph
# ============================================================
def build_review_workflow():
    graph = StateGraph(ReviewState)

    graph.add_node("extract_product_id", extract_product_id_node)
    graph.add_node("compute_date_window", compute_date_window_node)
    graph.add_node("fetch_reviews", fetch_reviews_node)
    graph.add_node("persist_interim", persist_interim_node)
    graph.add_node("split_daily", split_daily_node)

    graph.set_entry_point("extract_product_id")

    graph.add_edge("extract_product_id", "compute_date_window")
    graph.add_edge("compute_date_window", "fetch_reviews")
    graph.add_edge("fetch_reviews", "persist_interim")
    graph.add_edge("persist_interim", "split_daily")
    graph.add_edge("split_daily", END)

    return graph.compile()
