import os
import re
from typing import List

try:
    import requests  # type: ignore
except Exception:
    requests = None  # type: ignore[assignment]


def _clean_term(text: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9 ]+", " ", text or "")
    return re.sub(r"\s+", " ", cleaned).strip()


def fetch_related_terms(query: str, limit: int = 5) -> List[str]:
    """Fetch related keywords from Google Programmable Search if configured."""
    api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

    if not api_key or not engine_id or not query or requests is None:
        return []

    params = {
        "key": api_key,
        "cx": engine_id,
        "q": query,
        "num": limit,
    }

    try:
        response = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params=params,
            timeout=5,
        )
        response.raise_for_status()
    except requests.RequestException:
        return []

    data = response.json()
    terms: List[str] = []
    seen = set()

    for item in data.get("items", []):
        for field in ("title", "snippet"):
            term = _clean_term(item.get(field, ""))
            if term and term.lower() != query.lower() and term.lower() not in seen:
                seen.add(term.lower())
                terms.append(term)
            if len(terms) >= limit:
                break
        if len(terms) >= limit:
            break

    return terms

