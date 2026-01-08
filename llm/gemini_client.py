# llm/gemini_client.py

import os
import json
from google import genai
from llm.utils import safe_json_loads
from dotenv import load_dotenv
load_dotenv()

#GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = "gemini-2.5-flash-lite"

#genai.configure(api_key=GEMINI_API_KEY)
#model = genai.GenerativeModel(MODEL_NAME)

client = genai.Client()


def gemini_complete(reviews=None, existing_topics=None, proposed_topic=None, review=None, task="categorize"):
    """
    Two modes:
    1. Categorization fallback
    2. Canonical topic rewrite
    """

    if task == "categorize":
        prompt = f"""
        Categorize the following app reviews.

        Rules:
        - Prefer existing topics.
        - Create new topics only if strictly necessary.
        - Topics must be short English phrases.
        - Medium granularity.
        - Avoid duplicates aggressively.

        Existing topics:
        {json.dumps(existing_topics, indent=2)}

        Reviews:
        {json.dumps(reviews, indent=2)}

        Return STRICT JSON only:
        [
        {{
            "review": "<review text>",
            "topic": "<topic>",
            "is_new": true/false
        }}
        ]
        """
    else:
        prompt = f"""
        Rewrite the proposed topic into a canonical topic name.

        Rules:
        - Short English phrase
        - Medium granularity
        - Grounded strictly in the review
        - No duplication with existing concepts

        Proposed topic:
        "{proposed_topic}"

        Review:
        "{review}"

        Return STRICT JSON only:
        {{
        "label": "<final topic label>",
        "description": "<short description>"
        }}
        """

    response = client.models.generate_content(model = MODEL_NAME, contents = prompt)
    text = response.text.strip()
    return safe_json_loads(text)
