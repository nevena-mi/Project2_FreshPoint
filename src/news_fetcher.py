"""
news_fetcher.py — Pulls recent articles for the KB's topics.

This is the "freshness" piece: instead of retrieval over a stored corpus
(RAG), we fetch a handful of recent articles live and inject them directly
into the prompt. Swap NEWS_API_URL / provider as needed (e.g. NewsAPI,
cube.io, or a simple RSS feed reader).
"""

import os
from dataclasses import dataclass

import requests

NEWS_API_URL = "https://newsapi.org/v2/everything"


@dataclass
class NewsItem:
    title: str
    summary: str
    url: str
    source: str


def fetch_news_for_query(query: str, max_items: int = 10) -> list[NewsItem]:
    """Fetch recent, relevant articles for a single search query.

    Results are ranked by relevancy so the caller can pick the best match
    for the user's angle instead of auto-selecting by recency.

    Returns up to max_items candidates for a human to choose from in the UI
    (see app.py tab_sources), rather than auto-selecting one. Falls back to
    an empty list if the API key is missing or the request fails, per
    agents.md Definition of Done re: error handling.
    """
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key or not query:
        return []

    params = {
        "q": query,
        "language": "en",
        "sortBy": "relevancy",
        "pageSize": max_items,
        "apiKey": api_key,
    }

    try:
        response = requests.get(NEWS_API_URL, params=params, timeout=10)
        response.raise_for_status()
        articles = response.json().get("articles", [])
    except requests.RequestException:
        return []

    return [
        NewsItem(
            title=a.get("title", ""),
            summary=a.get("description", "") or "",
            url=a.get("url", ""),
            source=(a.get("source") or {}).get("name", ""),
        )
        for a in articles
    ]


def fetch_news_for_topic(topic: str, max_items: int = 10) -> list[NewsItem]:
    """Compatibility wrapper for topic-driven calls."""
    return fetch_news_for_query(topic, max_items=max_items)


def fetch_daily_news(topics: list[str], max_items: int = 3) -> list[NewsItem]:
    """Back-compat wrapper: fetch across multiple topics via separate
    per-topic queries (not one OR-joined query), then merge and cap.

    Prefer calling fetch_news_for_topic(topic) directly once a topic has
    already been chosen in the UI. This wrapper exists only for any call
    site that still expects a multi-topic list.
    """
    results: list[NewsItem] = []
    seen_urls: set[str] = set()
    per_topic_cap = max(1, max_items // max(1, len(topics[:4])))

    for topic in topics[:4]:
        for item in fetch_news_for_query(topic, max_items=per_topic_cap):
            if item.url and item.url in seen_urls:
                continue
            seen_urls.add(item.url)
            results.append(item)

    return results[:max_items]
