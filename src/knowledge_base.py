"""
knowledge_base.py — Loads and structures the two markdown knowledge bases.

Primary KB   : background.md, branding.md, tone_style.md  (personal / brand voice)
Secondary KB : topics.md (leadership, AI, product, coaching sources to watch)

This is intentionally simple (non-RAG): the whole KB fits in a prompt, so we
just load every file into memory rather than building a retrieval index.
See rag_decision.md for the full defense.
"""

from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import json

from src.chunker import chunk_secondary_corpus, export_chunks_jsonl


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

    def secondary_context(self) -> str:
        """Concatenate all secondary chunks for prompt injection."""
        if self.secondary_chunks:
            ordered_chunks = sorted(
                self.secondary_chunks,
                key=lambda chunk: (chunk.source_path, chunk.section_index, chunk.chunk_index),
            )
            return "\n\n".join(chunk.text for chunk in ordered_chunks)

        # Fallback for callers that have not loaded the KB yet.
        return "\n\n".join(f"## {name}\n{text}" for name, text in self.secondary_docs.items())

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
            "diagram_spec": post.diagram_spec,
            "sources_used": post.sources_used,
            "status": "draft",
            "final_text": None,
            "rating": None,
        }
        out_path = out_dir / f"{mode}_{timestamp}.json"
        out_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
