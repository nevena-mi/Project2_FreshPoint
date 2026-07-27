"""
chunker.py — Structure-aware chunking for the secondary knowledge base.

This module prepares markdown under knowledge_base/secondary/ for embedding:
- preserve heading context
- keep paragraphs together where possible
- fall back to sentence-level splitting only when necessary
- produce deterministic, JSON-serializable chunks with metadata

It is intentionally standalone for now. No other pipeline files are changed.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import argparse
import json
import re
from typing import Iterable, Iterator


DEFAULT_SECONDARY_DIR = Path("knowledge_base/secondary")
TARGET_CHUNK_WORDS = 280
MAX_CHUNK_WORDS = 420
MIN_CHUNK_WORDS = 140
OVERLAP_SENTENCES = 1

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
PAGE_NUMBER_RE = re.compile(r"^\s*\d+\s*$")
WHITESPACE_RE = re.compile(r"[ \t]+")
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9(])")
TOPIC_PREFIX_RE = re.compile(r"^([a-z0-9\-]+)__")


def _topic_from_filename(stem: str) -> str | None:
    """Ingested files are saved as '{topic_slug}__{name}.md' by
    document_processor.py. Files without that prefix (e.g. topics.md,
    hand-written secondary KB files) have no topic tag."""
    match = TOPIC_PREFIX_RE.match(stem)
    return match.group(1) if match else None


@dataclass(frozen=True)
class Chunk:
    """Embedding-ready chunk with source metadata."""

    source_path: str
    doc_id: str
    chunk_index: int
    text: str
    heading_path: list[str]
    section_index: int
    word_count: int
    char_count: int
    topic: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class _Section:
    heading_path: list[str]
    body: str
    section_index: int


def iter_secondary_markdown(root: Path = DEFAULT_SECONDARY_DIR) -> Iterator[Path]:
    """Yield markdown files from the secondary KB in deterministic order."""

    for path in sorted(root.rglob("*.md")):
        if path.is_file():
            yield path


def load_markdown(path: Path) -> str:
    """Read a markdown file using UTF-8."""

    return path.read_text(encoding="utf-8")


def normalize_text(text: str) -> str:
    """Light cleanup only: normalize whitespace and remove obvious noise lines."""

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    cleaned_lines: list[str] = []
    for raw_line in text.split("\n"):
        line = WHITESPACE_RE.sub(" ", raw_line).strip()
        if not line:
            cleaned_lines.append("")
            continue
        if PAGE_NUMBER_RE.match(line):
            continue
        cleaned_lines.append(line)

    normalized = "\n".join(cleaned_lines)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def split_into_sections(text: str) -> list[_Section]:
    """
    Split markdown into heading-scoped sections.

    Each section keeps the nearest heading stack so the chunker can preserve
    semantic context in the final chunk text.
    """

    lines = text.split("\n")
    heading_stack: list[tuple[int, str]] = []
    current_body: list[str] = []
    sections: list[_Section] = []
    section_index = 0

    def flush_section() -> None:
        nonlocal current_body, section_index
        body = "\n".join(current_body).strip()
        if body:
            sections.append(
                _Section(
                    heading_path=[title for _, title in heading_stack],
                    body=body,
                    section_index=section_index,
                )
            )
            section_index += 1
        current_body = []

    for line in lines:
        heading_match = HEADING_RE.match(line)
        if heading_match:
            flush_section()
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            heading_stack = [(lvl, ttl) for lvl, ttl in heading_stack if lvl < level]
            heading_stack.append((level, title))
            continue
        current_body.append(line)

    flush_section()
    if not sections and text.strip():
        sections.append(
            _Section(
                heading_path=[],
                body=text.strip(),
                section_index=0,
            )
        )
    return sections


def split_paragraphs(text: str) -> list[str]:
    """Split a section into paragraph-like blocks."""

    blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
    return blocks


def sentence_split(text: str) -> list[str]:
    """Deterministic sentence split with a conservative fallback."""

    text = text.strip()
    if not text:
        return []
    parts = SENTENCE_RE.split(text)
    return [part.strip() for part in parts if part.strip()]


def word_count(text: str) -> int:
    return len(text.split())


def build_chunk_text(heading_path: list[str], body: str) -> str:
    header_lines = [f"# {heading_path[0]}"] if heading_path else []
    if len(heading_path) > 1:
        header_lines.extend(f"{'#' * (idx + 2)} {title}" for idx, title in enumerate(heading_path[1:]))
    return "\n\n".join(header_lines + [body]).strip() if header_lines else body.strip()


def chunk_markdown_document(path: Path, target_words: int = TARGET_CHUNK_WORDS, max_words: int = MAX_CHUNK_WORDS) -> list[Chunk]:
    """Chunk one markdown document into embedding-ready records."""

    text = normalize_text(load_markdown(path))
    sections = split_into_sections(text)
    doc_id = path.stem
    topic = _topic_from_filename(doc_id)
    chunks: list[Chunk] = []
    chunk_index = 0

    for section in sections:
        section_chunks = _chunk_section(
            section=section,
            path=path,
            doc_id=doc_id,
            chunk_index_start=chunk_index,
            target_words=target_words,
            max_words=max_words,
            topic=topic,
        )
        chunks.extend(section_chunks)
        chunk_index += len(section_chunks)

    return chunks


def chunk_secondary_corpus(root: Path = DEFAULT_SECONDARY_DIR) -> list[Chunk]:
    """Chunk every markdown file under the secondary KB."""

    all_chunks: list[Chunk] = []
    for path in iter_secondary_markdown(root):
        all_chunks.extend(chunk_markdown_document(path))
    return all_chunks


def export_chunks_jsonl(chunks: Iterable[Chunk], out_path: Path) -> Path:
    """Write chunks as JSON Lines for downstream embedding jobs."""

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        for chunk in chunks:
            handle.write(json.dumps(chunk.to_dict(), ensure_ascii=False))
            handle.write("\n")
    return out_path


def _chunk_section(
    section: _Section,
    path: Path,
    doc_id: str,
    chunk_index_start: int,
    target_words: int,
    max_words: int,
    topic: str | None = None,
) -> list[Chunk]:
    blocks = split_paragraphs(section.body)
    if not blocks:
        return []

    heading_overhead = sum(word_count(title) for title in section.heading_path)
    # Reserve a small buffer for the inserted heading lines so the final chunk
    # stays under the intended cap after metadata/context is reattached.
    body_target = max(100, target_words - heading_overhead - 10)
    body_max = max(120, max_words - heading_overhead - 10)

    prepared_blocks: list[str] = []
    for block in blocks:
        prepared_blocks.extend(_split_large_block(block, max_words=body_max))

    merged = _pack_blocks(prepared_blocks, target_words=body_target, max_words=body_max)
    if len(merged) > 1 and word_count(" ".join(merged)) < MIN_CHUNK_WORDS:
        merged = ["\n\n".join(merged)]

    chunks: list[Chunk] = []
    for offset, body in enumerate(merged):
        text = build_chunk_text(section.heading_path, body)
        chunks.append(
            Chunk(
                source_path=str(path),
                doc_id=doc_id,
                chunk_index=chunk_index_start + offset,
                text=text,
                heading_path=section.heading_path,
                section_index=section.section_index,
                word_count=word_count(text),
                char_count=len(text),
                topic=topic,
            )
        )
    return chunks


def _split_large_block(block: str, max_words: int) -> list[str]:
    """Split a large paragraph into smaller sentence-based pieces."""

    if word_count(block) <= max_words:
        return [block.strip()]

    sentences = sentence_split(block)
    if len(sentences) <= 1:
        return _hard_wrap_words(block, max_words=max_words)

    pieces: list[str] = []
    current: list[str] = []
    current_words = 0
    for sentence in sentences:
        sentence_words = word_count(sentence)
        if current and current_words + sentence_words > max_words:
            pieces.append(" ".join(current).strip())
            current = []
            current_words = 0
        current.append(sentence)
        current_words += sentence_words

    if current:
        pieces.append(" ".join(current).strip())
    return pieces


def _hard_wrap_words(text: str, max_words: int) -> list[str]:
    """Last-resort fallback when a paragraph has no usable sentence boundaries."""

    words = text.split()
    if not words:
        return []
    pieces: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + max_words, len(words))
        pieces.append(" ".join(words[start:end]).strip())
        if end == len(words):
            break
        start = end
    return pieces


def _pack_blocks(blocks: list[str], target_words: int, max_words: int) -> list[str]:
    """
    Pack blocks into chunk-sized groups while respecting semantic boundaries.

    The function prefers to keep paragraphs together and only merges adjacent
    pieces until the target is reached. If a block alone exceeds the cap, it
    will have been pre-split by _split_large_block().
    """

    chunks: list[str] = []
    current: list[str] = []
    current_words = 0

    def flush() -> None:
        nonlocal current, current_words
        if current:
            chunks.append("\n\n".join(current).strip())
        current = []
        current_words = 0

    for block in blocks:
        block_words = word_count(block)
        if not block:
            continue
        if current and current_words + block_words > max_words:
            flush()
        current.append(block.strip())
        current_words += block_words
        if current_words >= target_words:
            flush()

    flush()
    return [chunk for chunk in chunks if chunk.strip()]


def _overlap_sentence_tail(previous_text: str, overlap_sentences: int = OVERLAP_SENTENCES) -> str:
    sentences = sentence_split(previous_text)
    if not sentences:
        return ""
    return " ".join(sentences[-overlap_sentences:]).strip()


def export_chunks_with_overlap(chunks: list[Chunk]) -> list[dict]:
    """
    Optional helper for downstream embedding jobs.

    It adds a deterministic context overlap between adjacent chunks from the
    same source document, while keeping the original chunk metadata intact.
    """

    enriched: list[dict] = []
    previous_by_doc: dict[str, Chunk] = {}
    for chunk in chunks:
        previous = previous_by_doc.get(chunk.doc_id)
        text = chunk.text
        if previous is not None and previous.source_path == chunk.source_path:
            overlap = _overlap_sentence_tail(previous.text)
            if overlap and overlap not in text:
                text = f"{overlap}\n\n{text}"
        enriched.append(
            {
                **chunk.to_dict(),
                "embedding_text": text,
            }
        )
        previous_by_doc[chunk.doc_id] = chunk
    return enriched


def main() -> None:
    parser = argparse.ArgumentParser(description="Chunk secondary KB markdown for embedding.")
    parser.add_argument(
        "--root",
        default=str(DEFAULT_SECONDARY_DIR),
        help="Secondary KB root directory",
    )
    parser.add_argument(
        "--out",
        default="output/secondary_chunks.jsonl",
        help="Write chunks to JSONL instead of stdout",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print a short chunking summary",
    )
    args = parser.parse_args()

    root = Path(args.root)
    chunks = chunk_secondary_corpus(root)

    if args.out:
        export_chunks_jsonl(chunks, Path(args.out))

    if args.stats:
        by_doc: dict[str, int] = {}
        for chunk in chunks:
            by_doc[chunk.doc_id] = by_doc.get(chunk.doc_id, 0) + 1
        summary = {
            "root": str(root),
            "documents": len(by_doc),
            "chunks": len(chunks),
            "per_document": by_doc,
        }
        print(json.dumps(summary, indent=2))
    else:
        print(json.dumps([chunk.to_dict() for chunk in chunks], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()