# review_analysis/workflow_end_to_end.py

from typing import TypedDict
from langgraph.graph import StateGraph, END

from runner_phase1 import run as run_phase1
from runner_phase2 import run_phase3_all_days
from runner_phase3 import run_phase4


# ======================================================
# Graph State
# ======================================================
class EndToEndState(TypedDict):
    app_url: str
    target_date: str
    lookback_days: int
    product_id: str


# ======================================================
# Phase Nodes
# ======================================================
def phase1_node(state: EndToEndState) -> EndToEndState:
    run_phase1(
        app_url=state["app_url"],
        target_date=state["target_date"],
        lookback_days=state["lookback_days"],
    )
    return state


def phase3_node(state: EndToEndState) -> EndToEndState:
    run_phase3_all_days()
    return state


def phase4_node(state: EndToEndState) -> EndToEndState:
    run_phase4(
        product_id=state["product_id"],
        input_dir="output",
        output_dir="output",
    )
    return state


# ======================================================
# Build LangGraph
# ======================================================
def build_end_to_end_workflow():
    graph = StateGraph(EndToEndState)

    graph.add_node("phase1", phase1_node)
    graph.add_node("phase3", phase3_node)
    graph.add_node("phase4", phase4_node)

    graph.set_entry_point("phase1")
    graph.add_edge("phase1", "phase3")
    graph.add_edge("phase3", "phase4")
    graph.add_edge("phase4", END)

    return graph.compile()
