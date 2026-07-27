"""
content_pipeline.py — Orchestrates brief -> publish for one content mode.

Diagram generation has been removed for now (unused code, cut to keep the
pipeline focused) — GeneratedPost no longer carries a diagram_spec field.
"""

from dataclasses import dataclass

from src.llm_integration import complete
from src.prompt_templates import LINKEDIN_TEMPLATE, NEWSLETTER_TEMPLATE


@dataclass
class GeneratedPost:
    text: str
    sources_used: list[str]


def generate_post(mode: str, kb, news_items, angle: str | None = None, news_only: bool = False) -> GeneratedPost:
    """
    news_only=True is the "Generate post based on the news" path: the post
    must be built around a fetched news item, not just optionally touch one.
    Raises if news_only is requested with no news_items — a news-based post
    can't be generated from nothing, and silently falling back to KB-only
    content would defeat the point of the button. The caller (app.py) is
    expected to check for news before calling this, but this is the actual
    guarantee.
    """
    if news_only and not news_items:
        raise ValueError("No news items available — can't generate a news-based post.")

    template = LINKEDIN_TEMPLATE if mode == "linkedin" else NEWSLETTER_TEMPLATE

    news_context = _chunk_and_select(news_items) or (
        "No fresh news items this run — write from KB context alone."
    )

    if news_only:
        news_requirement = (
            "This post MUST be built around one specific fresh news item above "
            "— pick the single most relevant one and make it the anchor of the "
            "whole post, not a passing reference."
            if mode == "linkedin"
            else "This newsletter MUST be built primarily around the fresh news "
            "items above — treat KB context as supporting flavor, not the main content."
        )
    else:
        news_requirement = (
            "References at most one news item above, only if it's genuinely "
            "relevant to the angle; it's fine to skip news entirely if none of it fits."
            if mode == "linkedin"
            else "2-3 short sections, each built around one theme or news item above."
        )

    prompt = template.format(
        primary_context=kb.primary_context(),
        secondary_context=kb.secondary_context(angle=angle),
        news_context=news_context,
        news_requirement=news_requirement,
    )
    print(prompt)
    text = complete(prompt)

    sources_used = [item.title for item in news_items]
    return GeneratedPost(text=text, sources_used=sources_used)


MAX_SNIPPET_CHARS = 240


def _chunk_and_select(news_items) -> str:
    """Trim each fetched article down to its most relevant snippet.

    This is the 'chunking' step from the pipeline sketch: not vector-DB
    chunking (we don't have a large stored corpus to search), just keeping
    each raw article's contribution to the prompt short and relevant so we
    don't burn context window / cost on full article text. If summaries are
    already short (as NewsAPI's usually are), this is close to a no-op —
    it becomes worth more once you fetch longer or more numerous sources.
    """
    lines = []
    for item in news_items:
        snippet = item.summary.strip()
        if len(snippet) > MAX_SNIPPET_CHARS:
            snippet = snippet[:MAX_SNIPPET_CHARS].rsplit(" ", 1)[0] + "..."
        lines.append(f"- {item.title} ({item.source}): {snippet}")
    return "\n".join(lines)