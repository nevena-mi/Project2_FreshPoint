# Chunker Integration Notes

This repository now includes a standalone chunker plus lightweight app
integration. The generation pipeline still does not use RAG or retrieval.

## What the new module does

`src/chunker.py` provides:

- `chunk_markdown_document(path)` for one markdown file
- `chunk_secondary_corpus(root)` for the whole secondary KB
- `export_chunks_jsonl(chunks, out_path)` for embedding jobs
- `export_chunks_with_overlap(chunks)` for an embedding-ready payload with
  deterministic overlap text

The chunking strategy is heading-aware and paragraph-first:

1. split by markdown headings
2. keep paragraph blocks intact when possible
3. split oversized blocks into sentences
4. fall back to a hard word wrap only if a paragraph has no sentence boundaries

## Current integration state

The app now consumes chunked secondary KB content directly as plain text.
There is still no retrieval layer, vector DB, or similarity search.

## If embeddings are added later

If you later want embeddings or retrieval, the following files would need
updates:

- `src/knowledge_base.py`
  - already loads chunk metadata and exposes chunked secondary KB context
- `src/main.py`
  - no change required unless retrieval is introduced
- `app.py`
  - already includes a UI action for chunk export
- `requirements.txt`
  - only if a downstream embedding/vector library is chosen

## Example embedding export script

Use this pattern for a standalone export job:

```python
from pathlib import Path
from src.chunker import chunk_secondary_corpus, export_chunks_with_overlap

chunks = chunk_secondary_corpus(Path("knowledge_base/secondary"))
payload = export_chunks_with_overlap(chunks)

print(f"Prepared {len(payload)} chunks for embedding")
```

To write JSONL for a batch job:

```python
from pathlib import Path
from src.chunker import chunk_secondary_corpus, export_chunks_jsonl

chunks = chunk_secondary_corpus(Path("knowledge_base/secondary"))
export_chunks_jsonl(chunks, Path("output/secondary_chunks.jsonl"))
```

## Notes on chunk sizing

The default target is about 280 words per chunk, with a hard cap at about 420
words. That keeps chunks large enough to preserve context, but small enough for
embedding and retrieval workflows.

## Validation checklist

- every `.md` file in `knowledge_base/secondary/` produces at least one chunk
- no chunk is empty
- chunk metadata includes source path, document id, chunk index, and sizes
- repeated runs produce identical chunk boundaries
