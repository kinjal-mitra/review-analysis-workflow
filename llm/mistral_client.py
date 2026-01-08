# llm/mistral_client.py

from mistralai import Mistral
import os
import json
from llm.utils import safe_json_loads


MODEL_NAME = "mistral-small-latest"


def mistral_complete(
    reviews=None,
    existing_topics=None,
    task="categorize",
    proposed_topic=None,
    review=None,
):
    """
    Mistral LLM wrapper for Phase-3.

    Supported tasks:
    - categorize: batch review → topic assignment
    - rewrite: canonical topic rewrite
    """

    with Mistral(
        api_key=os.getenv("MISTRAL_API_KEY", ""),
    ) as mistral:

        # --------------------------------------------------
        # Categorization task
        # --------------------------------------------------
        if task == "categorize":
            prompt = f"""
You are categorizing app reviews into topics.

Rules:
- Reuse existing topics if semantically similar.
- Propose a new topic ONLY if no existing topic fits.
- Topics must be short English phrases.
- Medium granularity.
- Very low tolerance for duplication.

Existing topics:
{json.dumps(existing_topics or [], indent=2)}

Reviews:
{json.dumps(reviews or [], indent=2)}

Return STRICT JSON only in this format:
[
  {{
    "review": "<review text>",
    "topic": "<topic name>",
    "is_new": true/false
  }}
]
"""

        # --------------------------------------------------
        # Canonical rewrite task
        # --------------------------------------------------
        elif task == "rewrite":
            prompt = f"""
Rewrite the proposed topic into a canonical topic.

Rules:
- Short English phrase
- Medium granularity
- Grounded strictly in the review
- Avoid duplication

Proposed topic:
"{proposed_topic}"

Review:
"{review}"

Return STRICT JSON only:
{{
  "label": "<canonical topic label>",
  "description": "<short description>"
}}
"""

        else:
            raise ValueError(f"Unsupported task: {task}")

        # --------------------------------------------------
        # Call Mistral
        # --------------------------------------------------
        res = mistral.chat.complete(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            stream=False,
        )

        # --------------------------------------------------
        # Extract & safely parse JSON
        # --------------------------------------------------
        content = res.choices[0].message.content
        return safe_json_loads(content)
