import json
import os
from typing import Dict, List, Optional

try:
    import google.generativeai as genai  # type: ignore
    _GENAI_IMPORT_ERROR = None
except Exception as import_error:  # pragma: no cover - depends on runtime python version
    genai = None
    _GENAI_IMPORT_ERROR = import_error


def gemini_enabled() -> bool:
    return bool(os.getenv("GEMINI_API_KEY")) and genai is not None


def _init_client():
    if genai is None:
        return None
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    genai.configure(api_key=api_key)
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        return model
    except Exception:
        return None


def suggest_actions_with_llm(
    query: str,
    actions: List[Dict],
    user_roles: List[str],
) -> Optional[Dict]:
    """
    Use Gemini to map a free-form question to one or more action IDs.
    Returns dict with keys answer, suggestion_ids, quick_replies, fallback.
    """
    model = _init_client()
    if not model:
        return None

    catalog = []
    for action in actions:
        catalog.append({
            "id": action["id"],
            "label": action["label"],
            "description": action["description"],
            "keywords": action.get("keywords", []),
            "url": action["url"],
        })

    schema_description = {
        "answer": "short natural language reply",
        "suggestion_ids": ["action_id_1", "action_id_2"],
        "quick_replies": ["text", "text"],
        "fallback": False
    }

    system_prompt = f"""
You are Nova, the Hoosier Hub assistant. Users can be students, staff, or admins.
Reply ONLY with JSON matching this schema (no markdown, no explanations):
{json.dumps(schema_description)}

Available actions (with ids):
{json.dumps(catalog)}

User roles: {user_roles}

Rules:
- Never invent action IDs. Use only the ids listed above.
- For clear matches, include up to 3 ids in suggestion_ids (ordered by relevance).
- If intent unclear, set suggestion_ids to [] and fallback true.
- answer must be <= 1 sentence, friendly and confident.
- quick_replies should be 2-4 short follow-ups (reuse defaults if unsure).
"""

    try:
        response = model.generate_content(
            [
                {"role": "user", "parts": [system_prompt]},
                {"role": "user", "parts": [f"User query: {query}"]},
            ]
        )
        if not response or not response.text:
            return None
        data = json.loads(response.text)
        return data
    except Exception:
        return None


