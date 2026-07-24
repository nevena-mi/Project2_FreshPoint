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


@dataclass
class KnowledgeBase:
    primary_dir: str
    secondary_dir: str
    primary_docs: dict = field(default_factory=dict)
    secondary_docs: dict = field(default_factory=dict)

    def load(self) -> None:
        self.primary_docs = self._load_dir(self.primary_dir)
        self.secondary_docs = self._load_dir(self.secondary_dir)

    @staticmethod
    def _load_dir(dir_path: str) -> dict:
        docs = {}
        for path in Path(dir_path).glob("*.md"):
            docs[path.stem] = path.read_text(encoding="utf-8")
        return docs

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
        """Concatenate all secondary docs for prompt injection."""
        return "\n\n".join(f"## {name}\n{text}" for name, text in self.secondary_docs.items())

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
        }
        out_path = out_dir / f"{mode}_{timestamp}.json"
        out_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
