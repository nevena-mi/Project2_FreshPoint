"""
document_processor.py — Ingest non-markdown sources (PDF, web article URLs,
and YouTube) into the secondary knowledge base as plain text/markdown.

Each ingested source is saved as a new .md file under
knowledge_base/secondary/ingested/, so it flows into the existing
KnowledgeBase.secondary_context() without any changes needed there.

PDF uses pypdf. YouTube uses youtube-transcript-api (works only for
videos that already have captions/transcripts available). Article URLs
use requests + BeautifulSoup to pull the main text out of a webpage.

Uploaded PDFs are written to the OS temp folder while being processed,
not to output/ — output/ is reserved for generated posts only.
"""

import os
import re
import tempfile
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
from youtube_transcript_api import YouTubeTranscriptApi

INGESTED_DIR = Path("knowledge_base/secondary/ingested")


def ingest_pdf(file_bytes: bytes, original_name: str) -> str:
    """Extract text from PDF bytes and save it as a secondary KB markdown file.
    Writes to a temp file only for the duration of extraction, then deletes it.
    Returns the path to the saved .md file."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        reader = PdfReader(tmp_path)
        text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
    finally:
        os.remove(tmp_path)

    return _save_ingested(Path(original_name).stem, text)


def ingest_youtube(url: str) -> str:
    """Pull the transcript of a YouTube video (if captions exist) and save
    as markdown. Raises if the video has no transcript available."""
    video_id = _extract_youtube_id(url)
    ytt_api = YouTubeTranscriptApi()
    transcript_list = ytt_api.fetch(video_id)
    text = " ".join(chunk.text for chunk in transcript_list)
    title = _get_youtube_title(url) or video_id
    return _save_ingested(title, text)


def ingest_url_article(url: str) -> str:
    """Fetch a webpage and extract its main readable text (via <p> tags),
    then save as markdown. Works for most standard article pages; won't
    reliably extract content from JS-rendered sites."""
    response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else url

    paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]
    text = "\n\n".join(p for p in paragraphs if len(p) > 40)  # skip nav/footer noise

    if not text:
        raise ValueError(f"Could not extract readable article text from: {url}")

    return _save_ingested(title, f"Source: {url}\n\n{text}")


def _get_youtube_title(url: str) -> str | None:
    """Fetch the video's title via YouTube's public oEmbed endpoint —
    no API key required. Returns None if the lookup fails, in which case
    ingest_youtube() falls back to using the video ID as the name."""
    try:
        response = requests.get(
            "https://www.youtube.com/oembed",
            params={"url": url, "format": "json"},
            timeout=10,
        )
        response.raise_for_status()
        return response.json().get("title")
    except requests.RequestException:
        return None


def _extract_youtube_id(url: str) -> str:
    match = re.search(r"(?:v=|youtu\.be/)([\w-]{11})", url)
    if not match:
        raise ValueError(f"Could not extract a video ID from URL: {url}")
    return match.group(1)


def _save_ingested(name: str, text: str) -> str:
    INGESTED_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^\w\-]", "_", name)[:60]
    out_path = INGESTED_DIR / f"{safe_name}.md"
    out_path.write_text(f"# {name}\n\n{text}", encoding="utf-8")
    return str(out_path)