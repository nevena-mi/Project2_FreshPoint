"""
knowledge_base.py — Loads and structures the two markdown knowledge bases.

Primary KB   : background.md, branding.md, tone_style.md, voice_examples.md
               — your voice. Always injected directly into the prompt in
               full; no retrieval needed since it's small and curated.
Secondary KB : topics.md + ingested/ (books, articles, PDFs you selected)
               — grounding material. As this grows, it is now retrieved
               by relevance to each post's specific angle (via
               embeddings.py), not dumped in wholesale.

See rag_decision.md for the full RAG vs non-RAG defense — the short
version: primary stays non-RAG (small, direct), secondary now uses real
embedding-based retrieval because its size can grow well beyond what
fits in one prompt.
"""

from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import json

from src.chunker import chunk_secondary_corpus, export_chunks_jsonl
from src.embeddings import retrieve_top_chunks

# Fallback cap (used only when no angle is given) on how many words of
# secondary context go into one prompt. With retrieval doing the real
# relevance work now, this is a safety net, not the primary mechanism.
MAX_SECONDARY_CONTEXT_WORDS = 3000

# How many of your most recent posted posts to keep as voice examples.
# Keeps voice_examples.md small and always injected directly (no retrieval
# needed) rather than growing unbounded.
MAX_VOICE_EXAMPLES = 5


@dataclass
class KnowledgeBase:
    primary_dir: str
    secondary_dir: str
    primary_docs: dict = field(default_factory=dict)
    secondary_docs: dict = field(default_factory=dict)
    secondary_chunks: list = field(default_factory=list)

    def load(self) -> None:
        self.primary_docs = self._load_dir(self.primary_dir)
        self.secondary_docs = self._load_dir(self.secondary_dir)
        self.secondary_chunks = self._load_secondary_chunks()

    @staticmethod
    def _load_dir(dir_path: str) -> dict:
        docs = {}
        for path in Path(dir_path).rglob("*.md"):
            docs[path.stem] = path.read_text(encoding="utf-8")
        return docs

    def _load_secondary_chunks(self) -> list:
        """Chunk secondary markdown into deterministic, embedding-ready units."""
        return chunk_secondary_corpus(Path(self.secondary_dir))

    def add_favorite(self, entry: str) -> None:
        """Append a favorite topic or article to knowledge_base/primary/favorites.md
        so it's picked up as personal-voice context on the next load()."""
        fav_path = Path(self.primary_dir) / "favorites.md"
        fav_path.parent.mkdir(parents=True, exist_ok=True)
        if not fav_path.exists():
            fav_path.write_text("# Favorite Topics & Articles\n\n", encoding="utf-8")
        with fav_path.open("a", encoding="utf-8") as f:
            f.write(f"- {entry}\n")

    def get_topics(self) -> list[str]:
        """Extract the topic list from secondary/topics.md.

        Expects simple markdown bullets, e.g.:
            - Leadership
            - AI
            - Product
            - Coaching
        """
        raw = self.secondary_docs.get("topics", "")
        topics = [
            line.lstrip("-* ").strip()
            for line in raw.splitlines()
            if line.strip().startswith(("-", "*"))
        ]
        return topics or ["AI", "Product", "Leadership", "Coaching"]

    def primary_context(self) -> str:
        """Concatenate all primary docs for prompt injection."""
        return "\n\n".join(f"## {name}\n{text}" for name, text in self.primary_docs.items())

    def secondary_context(self, angle: str | None = None, top_k: int = 6) -> str:
        """Return secondary KB text for prompt injection, ranked by
        relevance to the post's specific angle.

        Topic tags on ingested files (e.g. 'leadership__article.md') are
        kept purely as organizational metadata now — they no longer gate
        what's included. Every chunk (from every source, any topic) is a
        candidate; the angle's embedding similarity decides what's
        actually relevant. This is what keeps output focused as your
        source library grows, regardless of which topic bucket a given
        source happens to be filed under.

        If no angle is given, falls back to a simple word-count cap in
        document order (a safety net, not the main mechanism) — this
        should be rare in normal use now that angle drives generation.
        """
        if not self.secondary_chunks:
            # Fallback for callers that have not loaded the KB yet.
            return "\n\n".join(f"## {name}\n{text}" for name, text in self.secondary_docs.items())

        if angle and angle.strip():
            top_chunks = retrieve_top_chunks(self.secondary_chunks, angle, top_k=top_k)
            return "\n\n".join(chunk.text for chunk in top_chunks)

        # No angle given — fall back to word-count-capped, document-order chunks.
        ordered_chunks = sorted(
            self.secondary_chunks,
            key=lambda chunk: (chunk.source_path, chunk.section_index, chunk.chunk_index),
        )
        capped_chunks = []
        running_words = 0
        for chunk in ordered_chunks:
            if running_words + chunk.word_count > MAX_SECONDARY_CONTEXT_WORDS:
                break
            capped_chunks.append(chunk)
            running_words += chunk.word_count

        return "\n\n".join(chunk.text for chunk in capped_chunks)

    def add_voice_example(self, post_text: str) -> None:
        """Append a posted/finalized post to knowledge_base/primary/voice_examples.md
        so future generations draw on your real, actually-published writing.

        Keeps only the most recent MAX_VOICE_EXAMPLES posts — old ones are
        trimmed off the top so this file (and the prompt) stays small.
        """
        examples_path = Path(self.primary_dir) / "voice_examples.md"
        examples_path.parent.mkdir(parents=True, exist_ok=True)

        existing = examples_path.read_text(encoding="utf-8") if examples_path.exists() else ""
        entries = [e.strip() for e in existing.split("\n---\n") if e.strip()]
        entries.append(post_text.strip())
        entries = entries[-MAX_VOICE_EXAMPLES:]

        header = "# Voice Examples (from your posted content)\n\n"
        body = "\n---\n".join(entries)
        examples_path.write_text(header + body + "\n", encoding="utf-8")

    def export_secondary_chunks(self, out_path: str | Path = "output/secondary_chunks.jsonl") -> str:
        """Write the chunked secondary KB to JSONL for inspection or later embedding."""
        if not self.secondary_chunks:
            self.secondary_chunks = self._load_secondary_chunks()
        export_chunks_jsonl(self.secondary_chunks, Path(out_path))
        return str(out_path)

    def save_output(self, post, mode: str) -> None:
        """Persist generated content for the iterate stage / human review."""
        out_dir = Path("output")
        out_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        record = {
            "mode": mode,
            "timestamp": timestamp,
            "text": post.text,
            "sources_used": post.sources_used,
            "status": "draft",
            "final_text": None,
            "rating": None,
        }
        out_path = out_dir / f"{mode}_{timestamp}.json"
        out_path.write_text(json.dumps(record, indent=2), encoding="utf-8")