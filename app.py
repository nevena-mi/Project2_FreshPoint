"""
app.py — Streamlit UI for FreshPoint.

Run with:
    streamlit run app.py

Three top-level tabs:
  - Generate & Review: contains three sub-tabs — General Post, Post from
    News, Newsletter — each with exactly one action/button, no shared
    mode-toggle across them.
  - Add Sources:        PDF / article URL / YouTube ingestion
  - Feedback:           review posts marked final, rate them, mark final version
"""

import streamlit as st
from pathlib import Path
from datetime import datetime

from src.knowledge_base import KnowledgeBase
from src.news_fetcher import fetch_news_for_query
from src.content_pipeline import generate_post
from src.feedback import list_posts, mark_as_final, rate_post, mark_voice_example_added
from src.document_processor import ingest_pdf, ingest_youtube, ingest_url_article

st.set_page_config(page_title="FreshPoint", layout="centered")
st.title("FreshPoint")

# Load once so every tab that needs a topic list uses the same one.
_kb_for_topics = KnowledgeBase(primary_dir="knowledge_base/primary", secondary_dir="knowledge_base/secondary")
_kb_for_topics.load()
TOPICS = _kb_for_topics.get_topics()


def _post_label(post: dict) -> str:
    """Human-readable 'date — short title' label so posts are actually
    findable in a dropdown, instead of raw mode + timestamp."""
    raw_ts = post.get("timestamp", "")
    try:
        date_str = datetime.strptime(raw_ts, "%Y%m%d_%H%M%S").strftime("%Y-%m-%d %H:%M")
    except ValueError:
        date_str = raw_ts or "unknown date"

    text = (post.get("final_text") or post.get("text") or "").strip()
    first_line = text.splitlines()[0] if text else ""
    first_line = first_line.replace("**", "").replace("*", "").strip()
    title = first_line[:60] + "…" if len(first_line) > 60 else first_line

    return f"{date_str} — {title}" if title else f"{date_str} — ({post.get('mode', 'post')})"


def _draft_review_block(state_prefix: str) -> None:
    """Shared 'review + mark as final' block, used by all three generate
    sub-tabs. state_prefix keeps each sub-tab's draft in its own
    session_state slot, so generating in one doesn't clobber another."""
    path_key = f"{state_prefix}_draft_path"
    text_key = f"{state_prefix}_draft_edit"
    sources_key = f"{state_prefix}_draft_sources"

    if not st.session_state.get(path_key):
        return

    st.subheader("Review draft")

    sources = st.session_state.get(sources_key)
    if sources:
        st.caption("News sources used: " + ", ".join(sources))

    st.text_area(
        "Post text (edit before marking as final)",
        height=250,
        key=text_key,
    )
    if st.button("Mark as final / published", key=f"{state_prefix}_mark_final"):
        mark_as_final(st.session_state[path_key], st.session_state[text_key])
        st.success(
            "Marked as final — rate it Good/Medium/Poor on the Feedback "
            "tab once you know how it did; only Good posts get added to "
            "your voice examples."
        )
        del st.session_state[path_key]
        del st.session_state[text_key]
        if sources_key in st.session_state:
            del st.session_state[sources_key]


tab_generate, tab_sources, tab_feedback = st.tabs(
    ["Generate & Review", "Add Sources", "Feedback"]
)

with tab_generate:
    sub_general, sub_news, sub_newsletter = st.tabs(
        ["General Post", "Post from News", "Newsletter"]
    )

    with sub_general:
        st.write("Generate a LinkedIn post from your background and sources — no news fetch.")
        angle_general = st.text_input(
            "What's this post actually about?",
            placeholder="e.g. why hiring for technical skill alone misses the point",
            help="This drives which passages get pulled from your sources — be specific.",
            key="angle_general",
        )

        if st.button("Generate post", key="btn_generate_general"):
            with st.spinner("Loading knowledge base..."):
                kb = KnowledgeBase(primary_dir="knowledge_base/primary", secondary_dir="knowledge_base/secondary")
                kb.load()
                post = generate_post(mode="linkedin", kb=kb, news_items=[], angle=angle_general)
                saved_path = kb.save_output(post, mode="linkedin")

            st.session_state["general_draft_path"] = saved_path
            st.session_state["general_draft_edit"] = post.text
            st.success("Generated — review below before marking it final.")

        _draft_review_block("general")

    with sub_news:
        st.write("Generate a LinkedIn post anchored on a real, fresh news article.")
        angle_news = st.text_input(
            "What's this post actually about?",
            placeholder="e.g. why hiring for technical skill alone misses the point",
            help="This drives which passages get pulled from your sources — be specific.",
            key="angle_news",
        )

        if st.button("Generate post from news", key="btn_generate_news"):
            with st.spinner("Loading knowledge base and fetching news..."):
                kb = KnowledgeBase(primary_dir="knowledge_base/primary", secondary_dir="knowledge_base/secondary")
                kb.load()
                news_items = fetch_news_for_query(angle_news, max_items=5)

            if not news_items:
                st.error(
                    "No news articles found right now — check NEWS_API_KEY and "
                    "your NewsAPI quota, or try again shortly. Can't generate a "
                    "news-based post with nothing to react to."
                )
            else:
                post = generate_post(mode="linkedin", kb=kb, news_items=news_items, angle=angle_news, news_only=True)
                saved_path = kb.save_output(post, mode="linkedin")
                st.session_state["news_draft_path"] = saved_path
                st.session_state["news_draft_edit"] = post.text
                st.session_state["news_draft_sources"] = post.sources_used
                st.success("Generated from the news — review below before marking it final.")

        _draft_review_block("news")

    with sub_newsletter:
        st.write("Generate your monthly newsletter from your background and sources — no news fetch.")
        angle_newsletter = st.text_input(
            "What's this newsletter actually about?",
            placeholder="e.g. what I've learned so far transitioning into AI consulting",
            help="This drives which passages get pulled from your sources — be specific.",
            key="angle_newsletter",
        )

        if st.button("Generate newsletter", key="btn_generate_newsletter"):
            with st.spinner("Loading knowledge base..."):
                kb = KnowledgeBase(primary_dir="knowledge_base/primary", secondary_dir="knowledge_base/secondary")
                kb.load()
                post = generate_post(mode="newsletter", kb=kb, news_items=[], angle=angle_newsletter)
                saved_path = kb.save_output(post, mode="newsletter")

            st.session_state["newsletter_draft_path"] = saved_path
            st.session_state["newsletter_draft_edit"] = post.text
            st.success("Generated — review below before marking it final.")

        _draft_review_block("newsletter")

with tab_sources:
    st.write("Add a PDF, article URL, or YouTube video as extra secondary-KB context.")
    source_topic = st.selectbox("This source is about", TOPICS, key="source_topic")

    pdf_file = st.file_uploader("PDF", type=["pdf"])
    if pdf_file and st.button("Ingest PDF"):
        saved_path = ingest_pdf(pdf_file.read(), pdf_file.name, source_topic)
        st.success(f"Ingested — saved to {saved_path}")

    article_url = st.text_input("Article URL")
    if article_url and st.button("Ingest article"):
        saved_path = ingest_url_article(article_url, source_topic)
        st.success(f"Article ingested — saved to {saved_path}")

    yt_url = st.text_input("YouTube URL")
    if yt_url and st.button("Ingest YouTube video"):
        saved_path = ingest_youtube(yt_url, source_topic)
        st.success(f"Transcript ingested — saved to {saved_path}")

with tab_feedback:
    # Only posts already marked final show up here — a post has to be
    # confirmed as posted before it's rateable.
    posts = list_posts(status="final")
    if not posts:
        st.write(
            "No posts marked as final yet — generate a post and confirm it "
            "as final on one of the Generate & Review sub-tabs first."
        )
    else:
        labels = [_post_label(p) for p in posts]
        selected = st.selectbox("Pick a post", range(len(posts)), format_func=lambda i: labels[i])
        post = posts[selected]

        edited_text = st.text_area(
            "Post text (final, published version)",
            post.get("final_text") or post["text"],
            height=250,
        )

        status_bits = []
        if post.get("rating"):
            status_bits.append(f"Current rating: {post['rating'].capitalize()}")
        if post.get("added_to_voice_examples"):
            status_bits.append("already added to voice examples")
        if status_bits:
            st.caption(" · ".join(status_bits))

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Update final text"):
                mark_as_final(post["_path"], edited_text)
                st.success("Final text updated.")

        with col2:
            rating_label = st.radio(
                "Performance rating", ["Good", "Medium", "Poor"], horizontal=True, index=None
            )
            if rating_label and st.button("Save rating"):
                rating = rating_label.lower()
                rate_post(post["_path"], rating)

                if rating == "good" and not post.get("added_to_voice_examples"):
                    voice_kb = KnowledgeBase(
                        primary_dir="knowledge_base/primary",
                        secondary_dir="knowledge_base/secondary",
                    )
                    voice_kb.add_voice_example(edited_text)
                    mark_voice_example_added(post["_path"])
                    st.success("Rated Good — added to your voice examples for future posts.")
                elif rating == "good":
                    st.success("Rated Good — already in your voice examples from an earlier rating.")
                else:
                    st.success(f"Rated {rating_label}.")

        if post.get("sources_used"):
            st.caption("News sources used: " + ", ".join(post["sources_used"]))
