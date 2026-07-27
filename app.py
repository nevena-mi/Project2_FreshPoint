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
    ["Generate", "Add Sources", "Review & Feedback"]
)

with tab_generate:
    mode = st.radio("Content type", ["linkedin", "newsletter"], horizontal=True)
    topic = st.selectbox("Topic", TOPICS)
    angle = st.text_input(
        "What's this post actually about?",
        placeholder="e.g. why hiring for technical skill alone misses the point",
        help="This drives which passages get pulled from your sources — be specific.",
    )

    if st.button("Generate post"):
        with st.spinner("Loading knowledge base and fetching news..."):
            kb = KnowledgeBase(
                primary_dir="knowledge_base/primary",
                secondary_dir="knowledge_base/secondary",
            )
            kb.load()
            news_items = fetch_daily_news(topics=[topic], max_items=3)
            post = generate_post(mode=mode, kb=kb, news_items=news_items, topic=topic, angle=angle)
            kb.save_output(post, mode=mode)

        st.success("Generated.")
        st.text_area("Result", post.text, height=250)
        if post.diagram_spec and post.diagram_spec.get("svg_path"):
            st.caption(f"Diagram type: {post.diagram_spec.get('diagram_type')}")
            st.image(post.diagram_spec["svg_path"])
        elif post.diagram_spec:
            st.info("A diagram was recommended but could not be generated for this type.")

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
    posts = list_posts()
    if not posts:
        st.write("No posts generated yet — use the Generate tab first.")
    else:
        labels = [f"{p['mode']} — {p['timestamp']} — {p.get('status', 'draft')}" for p in posts]
        selected = st.selectbox("Pick a post", range(len(posts)), format_func=lambda i: labels[i])
        post = posts[selected]

        edited_text = st.text_area(
            "Post text (edit before marking as final if needed)",
            post.get("final_text") or post["text"],
            height=250,
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Mark as final / published"):
                mark_as_final(post["_path"], edited_text)
                voice_kb = KnowledgeBase(
                    primary_dir="knowledge_base/primary",
                    secondary_dir="knowledge_base/secondary",
                )
                voice_kb.add_voice_example(edited_text)
                st.success("Marked as final — added to your voice examples for future posts.")

        with col2:
            rating = st.radio("Performance rating", ["green", "orange", "red"], horizontal=True, index=None)
            if rating and st.button("Save rating"):
                rate_post(post["_path"], rating)
                st.success(f"Rated {rating}.")

        if post.get("sources_used"):
            st.caption("News sources used: " + ", ".join(post["sources_used"]))