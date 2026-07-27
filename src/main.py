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


def run(mode: str, topic: str | None = None) -> None:
    # 1. Document stage: load the primary (personal) and secondary (topics) KBs
    kb = KnowledgeBase(
        primary_dir="knowledge_base/primary",
        secondary_dir="knowledge_base/secondary",
    )
    kb.load()

    # If no topic was given on the command line, default to the first known
    # topic rather than searching/including all of them at once.
    if topic is None:
        topics = kb.get_topics()
        topic = topics[0] if topics else None

    # 2. Monitor stage: pull fresh news relevant to this specific topic
    news_items = fetch_daily_news(topics=[topic] if topic else [], max_items=3)

    # 3 & 4. Brief + Publish stages: build the prompt and call the LLM
    post = generate_post(
        mode=mode,
        kb=kb,
        news_items=news_items,
        topic=topic,
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
    parser.add_argument(
        "--topic",
        default=None,
        help="Which topic to write about (e.g. Leadership, AI, Product, Coaching). "
             "Defaults to the first topic in knowledge_base/secondary/topics.md.",
    )
    args = parser.parse_args()
    run(args.mode, args.topic)