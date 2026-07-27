"""
main.py — CLI entry point for FreshPoint, for quick prompt testing.

Run with:
    python -m src.main --mode linkedin
    python -m src.main --mode newsletter
    python -m src.main --mode linkedin --angle "why hiring for skill alone misses the point"
    python -m src.main --mode linkedin --news-only

Mirrors the same three actions as the app: a normal generation (no news
fetch), a news-anchored generation (--news-only, fetches and requires a
real article), and newsletter mode. Kept in sync with app.py's behavior —
if the app's generation logic changes, update this to match.
"""

import argparse

from src.knowledge_base import KnowledgeBase
from src.news_fetcher import fetch_news_for_query
from src.content_pipeline import generate_post


def run(mode: str, angle: str | None = None, news_only: bool = False) -> None:
    kb = KnowledgeBase(
        primary_dir="knowledge_base/primary",
        secondary_dir="knowledge_base/secondary",
    )
    kb.load()

    # Only fetch news if explicitly asked for (--news-only) — matches the
    # app's "General Post" (no fetch) vs "Post from News" (fetch + require)
    # split, instead of always fetching regardless of intent.
    news_items = []
    if news_only:
        news_items = fetch_news_for_query(angle or "", max_items=5)
        if not news_items:
            print("No news articles found — check NEWS_API_KEY/quota. Can't generate a news-based post.")
            return

    post = generate_post(
        mode=mode,
        kb=kb,
        news_items=news_items,
        angle=angle,
        news_only=news_only,
    )

    print("\n=== GENERATED CONTENT ===\n")
    print(post.text)

    if news_only:
        print("\n=== NEWS SOURCES USED ===")
        for title in post.sources_used:
            print(f"- {title}")

    kb.save_output(post, mode=mode)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FreshPoint content pipeline (CLI, for prompt testing)")
    parser.add_argument(
        "--mode",
        choices=["linkedin", "newsletter"],
        default="linkedin",
        help="Which content format to generate",
    )
    parser.add_argument(
        "--angle",
        default=None,
        help="What this specific post is actually about, e.g. "
             "'why hiring for technical skill alone misses the point'. "
             "Drives which passages get retrieved from your sources.",
    )
    parser.add_argument(
        "--news-only",
        action="store_true",
        help="Fetch real news and require the post to be built around one "
             "specific article, instead of writing from KB context alone.",
    )
    args = parser.parse_args()
    run(args.mode, args.angle, args.news_only)
