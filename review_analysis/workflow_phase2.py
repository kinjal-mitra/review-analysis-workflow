# review_analysis/workflow_phase3.py

from typing import TypedDict, List, Dict
from pathlib import Path
import json
import time

from langgraph.graph import StateGraph, END

from llm.groq_client import groq_complete
from llm.mistral_client import mistral_complete
from llm.claude_client import claude_complete


# ======================================================
# Graph State
# ======================================================
class Phase3State(TypedDict):
    product_id: str
    date: str
    input_file: str
    batch_size: int
    output_dir: str

    mistral_calls: int
    max_mistral_calls: int

    reviews: List[str]
    topics: Dict[str, Dict]
    assignments: List[Dict]
    topic_counts: Dict[str, int]


# ======================================================
# Utility
# ======================================================
def batched(items: List[str], size: int):
    for i in range(0, len(items), size):
        yield items[i:i + size]


# ======================================================
# Node 1: Load Daily Reviews
# ======================================================
def load_daily_reviews_node(state: Phase3State) -> Phase3State:
    with open(state["input_file"], "r", encoding="utf-8") as f:
        data = json.load(f)

    state["reviews"] = [r["Review"] for r in data]
    return state


# ======================================================
# Node 2: Load or Initialize Topic Memory
# ======================================================
def load_or_init_topics_node(state: Phase3State) -> Phase3State:
    base_dir = Path(state["output_dir"]) / state["product_id"]
    base_dir.mkdir(parents=True, exist_ok=True)

    topics_path = base_dir / "topics.json"

    if topics_path.exists():
        with open(topics_path, "r", encoding="utf-8") as f:
            state["topics"] = json.load(f)
    else:
        state["topics"] = {}

    state["assignments"] = []

    # Initialize DAILY counters for ALL canonical topics
    state["topic_counts"] = {
        topic["label"]: 0 for topic in state["topics"].values()
    }

    return state


# ======================================================
# Node 3: Categorize Reviews (Batch-wise)
# ======================================================
def categorize_batches_node(state: Phase3State) -> Phase3State:
    topics = state["topics"]

    for batch in batched(state["reviews"], state["batch_size"]):

        # ---------- Primary: Groq ----------
        try:
            response = groq_complete(
                reviews=batch,
                existing_topics=list(topics.values())
            )

        # ---------- Fallback: Mistral (budgeted) ----------
        except Exception:
            if state["mistral_calls"] >= state["max_mistral_calls"]:
                print("⚠️ Mistral daily budget exhausted. Skipping batch.")
                continue

            try:
                response = mistral_complete(
                    reviews=batch,
                    existing_topics=list(topics.values()),
                    task="categorize"
                )
                state["mistral_calls"] += 1

                # short cooldown to avoid burst limits
                time.sleep(10)

            except Exception:
                print("⚠️ Mistral fallback failed. Skipping batch.")
                continue

        # ---------- Process Responses ----------
        for item in response:
            review = item["review"]
            proposed_topic = item["topic"]
            is_new = item["is_new"]

            if not is_new:
                topic_label = proposed_topic
            else:
                approved = validate_new_topic(
                    proposed_topic,
                    review,
                    topics
                )
                if not approved:
                    continue

                topic_label, description = canonicalize_topic(
                    proposed_topic,
                    review
                )

                topics[topic_label] = {
                    "label": topic_label,
                    "description": description,
                }

                if topic_label not in state["topic_counts"]:
                    state["topic_counts"][topic_label] = 0

            # Record assignment
            state["assignments"].append(
                {
                    "review": review,
                    "topic": topic_label
                }
            )

            # Increment DAILY count
            if topic_label not in state["topic_counts"]:
                state["topic_counts"][topic_label] = 0

            state["topic_counts"][topic_label] += 1

    state["topics"] = topics
    return state


# ======================================================
# Claude Validation (Strict)
# ======================================================
def validate_new_topic(proposed_topic, review, topics) -> bool:
    response = claude_complete(
        proposed_topic=proposed_topic,
        review=review,
        existing_topics=list(topics.values())
    )
    return response.get("approved", False)


# ======================================================
# Mistral Canonicalization
# ======================================================
def canonicalize_topic(proposed_topic, review):
    result = mistral_complete(
        proposed_topic=proposed_topic,
        review=review,
        task="rewrite"
    )
    return result["label"], result["description"]


# ======================================================
# Node 4: Persist Outputs
# ======================================================
def persist_outputs_node(state: Phase3State) -> Phase3State:
    base_dir = Path(state["output_dir"]) / state["product_id"]
    base_dir.mkdir(parents=True, exist_ok=True)

    with open(base_dir / "topics.json", "w", encoding="utf-8") as f:
        json.dump(state["topics"], f, indent=4)

    with open(
        base_dir / f"topic_assignments_{state['date']}.json",
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(state["assignments"], f, indent=4)

    with open(
        base_dir / f"topic_counts_{state['date']}.json",
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            {
                "date": state["date"],
                "topics": state["topic_counts"]
            },
            f,
            indent=4
        )

    return state


# ======================================================
# Build LangGraph Workflow
# ======================================================
def build_phase3_workflow():
    graph = StateGraph(Phase3State)

    graph.add_node("load_reviews", load_daily_reviews_node)
    graph.add_node("load_topics", load_or_init_topics_node)
    graph.add_node("categorize", categorize_batches_node)
    graph.add_node("persist", persist_outputs_node)

    graph.set_entry_point("load_reviews")
    graph.add_edge("load_reviews", "load_topics")
    graph.add_edge("load_topics", "categorize")
    graph.add_edge("categorize", "persist")
    graph.add_edge("persist", END)

    return graph.compile()
