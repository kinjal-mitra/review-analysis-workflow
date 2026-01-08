
# Review Analysis Workflow (Agentic AI)

An end-to-end **agentic AI system** for analyzing Google Play Store reviews and generating **topic-wise trend reports** over time.  
The system ingests reviews daily, discovers and maintains topics using multiple LLM agents, and produces a **Topic × Date trend table** for product teams.

---

## 🚀 Key Capabilities

- **End-to-end pipeline**: Review ingestion → topic discovery → trend aggregation
- **Agentic AI (LangGraph-based)** orchestration
- **High-recall topic discovery** with strict deduplication
- **Cross-day topic continuity**
- **Daily batch processing**
- **LLM-only topic reasoning** 
- **Rate-limit safe execution**
- **Production-ready outputs** 

---

## 🧠 Architecture Overview

### Logical Phases

| Phase | Description | Key Output |
|-----|------------|-----------|
| Phase 1.1 | Fetch reviews from Google Play Store (SerpAPI) | Interim JSON |
| Phase 1.2 | Split reviews into daily files | Daily JSON files |
| Phase 2 | Agentic topic discovery & categorization | Topics + daily counts |
| Phase 3 | Topic × Date trend aggregation | CSV trend table |

The entire system is orchestrated using **LangGraph** with explicit state transitions.

---

## 📂 Repository Structure

```
review-analysis-workflow/
├── data/
│   ├── interim/        # Raw multi-day review dump
│   ├── processed/      # Per-day review JSON files
├── llm/
│   ├── groq_client.py
│   ├── mistral_client.py
│   ├── claude_client.py
│   └── utils.py
├── review_analysis/
│   ├── workflow_phase1.py   # Fetch + daily split
│   ├── workflow_phase2.py   # Agentic topic discovery
│   ├── workflow_phase3.py   # Trend aggregation
│   ├── workflow.py
│   └── dataset.py
├── output/
│   ├── <product_id>/
│   │   ├── topics.json
│   │   ├── topic_counts_YYYY-MM-DD.json
│   │   └── topic_assignments_YYYY-MM-DD.json
│   └── <product_id>_Topic_Trend_Table.csv
├── runner_phase1.py
├── runner_phase2.py
├── runner_phase3.py
├── runner.py
└── README.md
```

---

## 🤖 LLM Strategy

| Role | LLM |
|----|----|
| Primary categorization | Groq (LLaMA 3.3 70B) |
| Fallback categorization & rewrite | Mistral (mistral-small-latest) |
| Topic approval & hallucination guard | Claude Sonnet |
| Topic deduplication | Strict rejection strategy |
| Topic naming | Canonical rewrite via LLM |

---

## 🧩 Topic Handling Principles

- Medium granularity topics
- Short English phrase naming
- Positive feedback included as topics
- Very low similarity tolerance
- Topics persisted per product
- Reused across batches and days
- New topics validated before acceptance

---

## 📊 Output Format

### Final Trend Table

**Rows**: Topics  
**Columns**: Dates (T-30 → T or available range)  
**Cells**: Frequency of topic occurrence

Example:

```
Topic                          2026-01-05  2026-01-06  2026-01-07
Delivery Partner Rude          5           8           12
Late Delivery                  3           7           10
Positive Sentiment             12          15          18
```

Saved as:

```
output/<product_id>_Topic_Trend_Table.csv
```

---

## ▶️ How to Run (3-Day Demo)

### 1️⃣ Set Environment Variables

```
SERPAPI_KEY=...
GROQ_API_KEY=...
MISTRAL_API_KEY=...
CLAUDE_API_KEY=...
```

### 2️⃣ Run End-to-End Pipeline

```bash
python runner.py
```

Default behavior:
- Processes **last 3 days**
- Generates topic trends automatically

---

## 🔮 Extensibility

- Extend from 3 days → 30 days or more
- Add dashboards / visualizations
- Add alerting on trend spikes
- Integrate human-in-the-loop review
- Schedule via cron / Airflow

---

## 📜 License

MIT License

---
