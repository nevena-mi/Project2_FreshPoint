"""
app.py — Streamlit UI for FreshPoint.

Run with:
    streamlit run app.py

Two tabs:
  - Generate: trigger the pipeline for LinkedIn or newsletter mode
  - Review:   see past posts, mark one as the final/published version
              (with edits), and rate it green/orange/red
"""

import streamlit as st
from pathlib import Path

from src.knowledge_base import KnowledgeBase
from src.news_fetcher import fetch_daily_news
from src.content_pipeline import generate_post
from src.feedback import list_posts, mark_as_final, rate_post
from src.document_processor import ingest_pdf, ingest_youtube, ingest_url_article

st.set_page_config(page_title="FreshPoint", layout="centered")
st.title("FreshPoint")

# Load once so both the Generate and Add Sources tabs can offer the same
# topic list in their dropdowns.
_kb_for_topics = KnowledgeBase(primary_dir="knowledge_base/primary", secondary_dir="knowledge_base/secondary")
_kb_for_topics.load()
TOPICS = _kb_for_topics.get_topics()

tab_generate, tab_sources, tab_review = st.tabs(
    ["Generate & Review", "Add Sources", "Feedback"]
)

with tab_generate:
    mode = st.radio("Content type", ["linkedin", "newsletter"], horizontal=True)
    angle = st.text_input(
        "What's this post actually about?",
        placeholder="e.g. why hiring for technical skill alone misses the point",
        help="This drives which passages get pulled from your sources — be specific.",
    )

    col_generate, col_generate_news = st.columns(2)
    with col_generate:
        generate_clicked = st.button("Generate post")
    with col_generate_news:
        generate_news_clicked = st.button("Generate post based on the news")

    if generate_clicked:
        with st.spinner("Loading knowledge base..."):
            kb = KnowledgeBase(
                primary_dir="knowledge_base/primary",
                secondary_dir="knowledge_base/secondary",
            )
            kb.load()
            # KB-only path — no news fetch here. That's what the "based on
            # the news" button is for now, so this one doesn't spend NewsAPI
            # quota on a post that isn't asking for news.
            post = generate_post(mode=mode, kb=kb, news_items=[], angle=angle)
            saved_path = kb.save_output(post, mode=mode)

        # Stash in session_state — the button click below triggers a rerun,
        # so a plain local variable wouldn't survive to that point. Written
        # directly into "generate_draft_edit", the SAME key the text_area
        # below uses, not a separate "draft_text" key — a keyed widget
        # ignores any value= argument once it exists, it only ever reflects
        # session_state[key], so this has to be the single source of truth.
        st.session_state["draft_path"] = saved_path
        st.session_state["generate_draft_edit"] = post.text
        st.success("Generated — review below before marking it final.")

    if generate_news_clicked:
        with st.spinner("Loading knowledge base and fetching news..."):
            kb = KnowledgeBase(
                primary_dir="knowledge_base/primary",
                secondary_dir="knowledge_base/secondary",
            )
            kb.load()
            news_items = fetch_daily_news(topics=TOPICS, max_items=3)

        if not news_items:
            st.error(
                "No news articles found right now — check NEWS_API_KEY and "
                "your NewsAPI quota, or try again shortly. Can't generate a "
                "news-based post with nothing to react to."
            )
        else:
            post = generate_post(mode=mode, kb=kb, news_items=news_items, angle=angle, news_only=True)
            saved_path = kb.save_output(post, mode=mode)
            st.session_state["draft_path"] = saved_path
            st.session_state["generate_draft_edit"] = post.text
            st.success("Generated from the news — review below before marking it final.")

    if st.session_state.get("draft_path"):
        st.subheader("Review draft")
        edited_draft = st.text_area(
            "Post text (edit before marking as final)",
            height=250,
            key="generate_draft_edit",
        )
        if st.button("Mark as final / published", key="generate_mark_final"):
            mark_as_final(st.session_state["draft_path"], edited_draft)
            voice_kb = KnowledgeBase(
                primary_dir="knowledge_base/primary",
                secondary_dir="knowledge_base/secondary",
            )
            voice_kb.add_voice_example(edited_draft)
            st.success("Marked as final — added to your voice examples for future posts.")
            del st.session_state["draft_path"]
            del st.session_state["generate_draft_edit"]

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

with tab_review:
    # Only posts already marked final show up here — a post has to be
    # confirmed as posted (in the Generate tab) before it's rateable.
    posts = list_posts(status="final")
    if not posts:
        st.write(
            "No posts marked as final yet — generate a post and confirm it "
            "as final on the Generate tab first."
        )
    else:
        labels = [f"{p['mode']} — {p['timestamp']}" for p in posts]
        selected = st.selectbox("Pick a post", range(len(posts)), format_func=lambda i: labels[i])
        post = posts[selected]

        edited_text = st.text_area(
            "Post text (final, published version)",
            post.get("final_text") or post["text"],
            height=250,
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Update final text"):
                mark_as_final(post["_path"], edited_text)
                st.success("Final text updated.")

        with col2:
            rating = st.radio("Performance rating", ["green", "orange", "red"], horizontal=True, index=None)
            if rating and st.button("Save rating"):
                rate_post(post["_path"], rating)
                st.success(f"Rated {rating}.")

        if post.get("sources_used"):
            st.caption("News sources used: " + ", ".join(post["sources_used"]))