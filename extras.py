import os
import httpx
from urllib.parse import urlparse

def lookup(subject):
    key = os.getenv("SERPAPI_KEY")
    if not key or not subject:
        return {"title": subject, "description": None}

    trusted_domains = (
        "edu",
        "gov",
        "britannica.com",
        "kew.org",
        "nationalgeographic.com",
        "nwf.org",
    )

    try:
        response = httpx.get(
            "https://serpapi.com/search.json",
            params={
                "q": f"{subject} nature ecology facts",
                "api_key": key,
                "engine": "google",
            },
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
    except Exception as error:
        print("SerpApi error:", error)
        return {"title": subject, "description": None}

    info = data.get("knowledge_graph", {})
    if info.get("description"):
        return {
            "title": info.get("title", subject),
            "description": info["description"],
        }

    for result in data.get("organic_results") or []:
        snippet = result.get("snippet", "").strip()
        hostname = urlparse(result.get("link", "")).hostname or ""
        hostname = hostname.lower().removeprefix("www.")

        is_trusted = any(
            hostname == domain or hostname.endswith("." + domain)
            for domain in trusted_domains
        )
        looks_useful = len(snippet) >= 50 and "facebook" not in snippet.lower()

        if is_trusted and looks_useful:
            return {
                "title": result.get("title", subject),
                "description": snippet,
            }

    return {"title": subject, "description": None}