"""
content_pipeline.py — Orchestrates brief -> publish for one content mode.

Keeps the "expensive/complex" diagram step optional and separate, so the
text-only MVP always works even if diagram generation is skipped or fails.
"""

import json
from dataclasses import dataclass

from src.llm_integration import complete
from src.prompt_templates import (
    LINKEDIN_TEMPLATE,
    NEWSLETTER_TEMPLATE,
    DIAGRAM_DECISION_TEMPLATE,
)


@dataclass
class GeneratedPost:
    text: str
    diagram_spec: dict | None
    sources_used: list[str]


def generate_post(mode: str, kb, news_items, topic: str | None = None, angle: str | None = None) -> GeneratedPost:
    template = LINKEDIN_TEMPLATE if mode == "linkedin" else NEWSLETTER_TEMPLATE

    news_context = _chunk_and_select(news_items) or (
        "No fresh news items this run — write from KB context alone."
    )

    prompt = template.format(
        primary_context=kb.primary_context(),
        secondary_context=kb.secondary_context(topic=topic, angle=angle),
        news_context=news_context,
    )

    text = complete(prompt)

    # Optional diagram step — only for LinkedIn, only if it's worth the cost.
    diagram_spec = None
    if mode == "linkedin":
        diagram_spec = _maybe_plan_diagram(text)

    sources_used = [item.title for item in news_items]
    return GeneratedPost(text=text, diagram_spec=diagram_spec, sources_used=sources_used)


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


def _maybe_plan_diagram(post_text: str) -> dict | None:
    """Ask the LLM whether this post warrants a diagram, and what kind.

    Cheap decision step (short prompt, small output) before spending on
    actual diagram/image generation — keeps the visual feature from
    running (and costing) on every single post.
    """
    raw = complete(DIAGRAM_DECISION_TEMPLATE.format(post_text=post_text), temperature=0.0)
    try:
        decision = json.loads(raw)
    except json.JSONDecodeError:
        return None

    if not decision.get("needs_diagram"):
        return None
    return decision