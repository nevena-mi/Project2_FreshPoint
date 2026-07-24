"""
document_processor.py — Ingest non-markdown sources (PDF, audio, YouTube)
into the secondary knowledge base as plain text/markdown.

Each ingested source is saved as a new .md file under
knowledge_base/secondary/ingested/, so it flows into the existing
KnowledgeBase.secondary_context() without any changes needed there.

Audio transcription uses the OpenAI Whisper API (same OPENAI_API_KEY,
no extra key needed). PDF uses pypdf. YouTube uses youtube-transcript-api
(works only for videos that already have captions/transcripts available).
"""

import re
from pathlib import Path

from pypdf import PdfReader
from youtube_transcript_api import YouTubeTranscriptApi

from src.llm_integration import client  # reuse the same OpenAI client

INGESTED_DIR = Path("knowledge_base/secondary/ingested")


def ingest_pdf(file_path: str) -> str:
    """Extract text from a PDF and save it as a secondary KB markdown file.
    Returns the path to the saved .md file."""
    reader = PdfReader(file_path)
    text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
    return _save_ingested(Path(file_path).stem, text)


def ingest_audio(file_path: str) -> str:
    """Transcribe an audio file via OpenAI Whisper and save as markdown."""
    with open(file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
        )
    return _save_ingested(Path(file_path).stem, transcript.text)


def ingest_youtube(url: str) -> str:
    """Pull the transcript of a YouTube video (if captions exist) and save
    as markdown. Raises if the video has no transcript available."""
    video_id = _extract_youtube_id(url)
    transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
    text = " ".join(chunk["text"] for chunk in transcript_list)
    return _save_ingested(video_id, text)


def _extract_youtube_id(url: str) -> str:
    match = re.search(r"(?:v=|youtu\.be/)([\w-]{11})", url)
    if not match:
        raise ValueError(f"Could not extract a video ID from URL: {url}")
    return match.group(1)


def _save_ingested(name: str, text: str) -> str:
    INGESTED_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^\w\-]", "_", name)
    out_path = INGESTED_DIR / f"{safe_name}.md"
    out_path.write_text(f"# {name}\n\n{text}", encoding="utf-8")
    return str(out_path)
