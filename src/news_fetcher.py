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


def fetch_daily_news(topics: list[str], max_items: int = 3) -> list[NewsItem]:
    """Fetch a small number of recent articles across the given topics.

    Kept deliberately simple: one query per pipeline run, top N results.
    Falls back to an empty list (post generation still works without news)
    if the API key is missing or the request fails — see agents.md
    Definition of Done re: error handling.
    """
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        return []

    query = " OR ".join(topics[:4])
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
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
