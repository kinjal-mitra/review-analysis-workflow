# llm/groq_client.py

import os
import json
from groq import Groq
from llm.utils import safe_json_loads
from dotenv import load_dotenv
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = "llama-3.3-70b-versatile"

client = Groq(api_key=GROQ_API_KEY)


def groq_complete(reviews, existing_topics):
    """
    Categorize reviews into existing topics or propose new ones.

    Returns:
    [
      {
        "review": "...",
        "topic": "Delivery partner rude",
        "is_new": false
      }
    ]
    """

    prompt = f"""
        You are categorizing app reviews into topics.

        Rules:
        - Use existing topics if semantically similar.
        - Propose a new topic ONLY if no existing topic fits.
        - Topics must be short English phrases.
        - Medium granularity.
        - Very low tolerance for duplication.

        Existing topics:
        {json.dumps(existing_topics, indent=2)}

        Reviews:
        {json.dumps(reviews, indent=2)}

        Return STRICT JSON only in this format:
        [
        {{
            "review": "<review text>",
            "topic": "<topic name>",
            "is_new": true/false
        }}
        ]
        """

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )

    content = response.choices[0].message.content.strip()
    return safe_json_loads(content)
