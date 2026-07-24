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
from src.document_processor import ingest_pdf, ingest_audio, ingest_youtube

st.set_page_config(page_title="FreshPoint", layout="centered")
st.title("FreshPoint")

tab_generate, tab_sources, tab_favorites, tab_review = st.tabs(
    ["Generate", "Add Sources", "Favorites", "Review & Feedback"]
)

with tab_generate:
    mode = st.radio("Content type", ["linkedin", "newsletter"], horizontal=True)

    if st.button("Generate post"):
        with st.spinner("Loading knowledge base and fetching news..."):
            kb = KnowledgeBase(
                primary_dir="knowledge_base/primary",
                secondary_dir="knowledge_base/secondary",
            )
            kb.load()
            news_items = fetch_daily_news(topics=kb.get_topics(), max_items=3)
            post = generate_post(mode=mode, kb=kb, news_items=news_items)
            kb.save_output(post, mode=mode)

        st.success("Generated.")
        st.text_area("Result", post.text, height=250)
        if post.diagram_spec:
            st.info(f"Suggested diagram: {post.diagram_spec}")

with tab_sources:
    st.write("Add a PDF, audio file, or YouTube video as extra secondary-KB context.")

    pdf_file = st.file_uploader("PDF", type=["pdf"])
    if pdf_file and st.button("Ingest PDF"):
        tmp_path = Path("output") / pdf_file.name
        tmp_path.parent.mkdir(exist_ok=True)
        tmp_path.write_bytes(pdf_file.read())
        saved_path = ingest_pdf(str(tmp_path))
        st.success(f"Ingested — saved to {saved_path}")

    audio_file = st.file_uploader("Audio", type=["mp3", "wav", "m4a"])
    if audio_file and st.button("Ingest audio"):
        tmp_path = Path("output") / audio_file.name
        tmp_path.parent.mkdir(exist_ok=True)
        tmp_path.write_bytes(audio_file.read())
        saved_path = ingest_audio(str(tmp_path))
        st.success(f"Transcribed and ingested — saved to {saved_path}")

    yt_url = st.text_input("YouTube URL")
    if yt_url and st.button("Ingest YouTube video"):
        saved_path = ingest_youtube(yt_url)
        st.success(f"Transcript ingested — saved to {saved_path}")

with tab_favorites:
    st.write("Add topics you like or articles you consider a good example of your voice.")
    fav_entry = st.text_input("New favorite (topic or article title + link)")
    if fav_entry and st.button("Save favorite"):
        kb = KnowledgeBase(primary_dir="knowledge_base/primary", secondary_dir="knowledge_base/secondary")
        kb.add_favorite(fav_entry)
        st.success("Saved.")

    fav_path = Path("knowledge_base/primary/favorites.md")
    if fav_path.exists():
        st.text_area("Current favorites.md", fav_path.read_text(encoding="utf-8"), height=200)


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
                st.success("Marked as final.")

        with col2:
            rating = st.radio("Performance rating", ["green", "orange", "red"], horizontal=True, index=None)
            if rating and st.button("Save rating"):
                rate_post(post["_path"], rating)
                st.success(f"Rated {rating}.")

        if post.get("sources_used"):
            st.caption("News sources used: " + ", ".join(post["sources_used"]))
