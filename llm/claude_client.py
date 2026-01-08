# llm/claude_client.py

import os
import json
import anthropic
from llm.utils import safe_json_loads
from dotenv import load_dotenv
load_dotenv()

CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL_NAME = "claude-sonnet-4-5-20250929"

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)


def claude_complete(proposed_topic, review, existing_topics):
    """
    Strictly validates whether a proposed topic:
    1. Is grounded in the review
    2. Is NOT semantically similar to existing topics
    """

    prompt = f"""
        You are a strict topic approval agent.

        Rules:
        - Reject if the topic is even slightly similar to any existing topic.
        - Reject if the topic is not explicitly grounded in the review text.
        - Approve only if the topic is clearly new and distinct.

        Existing topics:
        {json.dumps(existing_topics, indent=2)}

        Proposed topic:
        "{proposed_topic}"

        Review:
        "{review}"

        Return STRICT JSON only:
        {{
        "approved": true/false,
        "reason": "<short explanation>"
        }}
        """

    response = client.messages.create(
        model=MODEL_NAME,
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    content = response.content[0].text.strip()
    return safe_json_loads(content)
