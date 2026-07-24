"""
main.py — Entry point for the FreshTake content pipeline.

Run with:
    python -m src.main --mode linkedin
    python -m src.main --mode newsletter

Pipeline: document -> monitor(news) -> brief -> publish -> iterate
"""

import argparse

from src.knowledge_base import KnowledgeBase
from src.news_fetcher import fetch_daily_news
from src.content_pipeline import generate_post


def run(mode: str) -> None:
    # 1. Document stage: load the primary (personal) and secondary (topics) KBs
    kb = KnowledgeBase(
        primary_dir="knowledge_base/primary",
        secondary_dir="knowledge_base/secondary",
    )
    kb.load()

    # 2. Monitor stage: pull fresh news relevant to the KB's general topics
    news_items = fetch_daily_news(topics=kb.get_topics(), max_items=3)

    # 3 & 4. Brief + Publish stages: build the prompt and call the LLM
    post = generate_post(
        mode=mode,
        kb=kb,
        news_items=news_items,
    )

    print("\n=== GENERATED CONTENT ===\n")
    print(post.text)
    if post.diagram_spec:
        print("\n[Diagram spec attached — see post.diagram_spec]")

    # 5. Iterate stage: save output for human review / next-round refinement
    kb.save_output(post, mode=mode)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FreshTake content pipeline")
    parser.add_argument(
        "--mode",
        choices=["linkedin", "newsletter"],
        default="linkedin",
        help="Which content format to generate",
    )
    args = parser.parse_args()
    run(args.mode)
