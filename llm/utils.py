# llm/utils.py

import json
import re


def safe_json_loads(text: str):
    """
    Extracts and parses JSON from LLM output.
    Raises ValueError if parsing fails.
    """
    if not text or not text.strip():
        raise ValueError("Empty LLM response")

    text = text.strip()

    # Case 1: Raw JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Case 2: Markdown fenced JSON
    match = re.search(r"```json(.*?)```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Case 3: First JSON-like block
    match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    raise ValueError("LLM response is not valid JSON")
