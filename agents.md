# FreshPoint Agent Guide

## Project Purpose
FreshPoint generates branded LinkedIn posts and a monthly newsletter for an AI consultant by combining a personal knowledge base, chunked-and-retrieved secondary sources, and fresh news. `project_structure.md` is the source of truth for scope, and agents should use the relevant Must IDs from that file when scoping work. If a task does not map cleanly to a Must ID, treat it as out of scope unless the user explicitly says otherwise.

## Stack & How To Run
- Python: tested in this repo with Python 3.14.6.
- Install deps:
  ```bash
  python -m venv venv
  source venv/bin/activate  # on Windows: venv\\Scripts\\activate
  pip install -r requirements.txt
  ```
- CLI run:
  ```bash
  python -m src.main --mode linkedin
  python -m src.main --mode linkedin --angle "why hiring for technical skill alone misses the point"
  python -m src.main --mode newsletter
  ```
- Streamlit run:
  ```bash
  streamlit run app.py
  ```
- Expected env vars:
  - `OPENAI_API_KEY` for generation and embeddings
  - `NEWS_API_KEY` for live news fetches
  - `.env` is loaded via `python-dotenv`; do not hardcode secrets in source files

## Repo Map
- `knowledge_base/primary/`
  - personal voice / branding / background markdown
  - keep these as plain markdown files
- `knowledge_base/secondary/`
  - `topics.md` plus ingested secondary sources under `ingested/`
  - secondary content is chunked and may be retrieved by embeddings
- `src/prompt_templates.py`
  - LinkedIn, newsletter, and diagram decision prompts
- `src/content_pipeline.py`
  - prompt assembly and post generation flow
- `src/main.py`
  - CLI entry point
- `app.py`
  - Streamlit UI for generation, source ingestion, and feedback
- `src/chunker.py`
  - deterministic chunking for the secondary KB
- `src/embeddings.py`
  - embedding cache and retrieval ranking for secondary chunks
- `src/document_processor.py`
  - PDF, article URL, and YouTube ingestion into the secondary KB
- `src/knowledge_base.py`
  - KB loading, context assembly, and output saving

## Conventions For Agent Edits
- Keep changes scoped to the active card and its Must ID(s).
- Prefer small, explicit edits over broad refactors.
- Use existing file names and module boundaries; add new files only when the task needs a new capability or a companion note.
- Put reusable source code in `src/`.
- Put markdown knowledge-base content in `knowledge_base/` and keep it as markdown.
- Keep KB filenames descriptive and lowercase with underscores or double-underscore topic prefixes when the existing convention uses them.
- Avoid inventing new config formats, CLI flags, or APIs unless the task explicitly requires them.
- If a change affects behavior, update the relevant docs in the same change if they are part of the requested scope.

## Definition of Done
An agent-assisted change is done only when all of the following are true:
- It maps to one card and the relevant Must ID(s).
- The requested behavior is implemented without unrelated scope creep.
- It is verified with the smallest reasonable check: compile, unit test, smoke run, or manual run path.
- Any user-facing or repo-facing documentation that is part of the task is updated.
- No secrets, dead code, or unrelated formatting changes are introduced.
- The change is ready to hand back without requiring the next agent to guess intent.

## Never Do
- Never commit secrets, API keys, or `.env` contents.
- Never invent APIs, dependencies, or file paths that are not already in the repo or explicitly requested.
- Never expand a task into items listed under `Won't have this sprint` in `project_structure.md`.
- Never change the retrieval/generation architecture unless the card explicitly asks for it.
- Never rewrite unrelated files just because they are nearby.
- Never turn a scoped card into a broad cleanup.

## How The Team Uses Agents
- Work one Trello card at a time.
- Paste the card description plus the relevant Must ID(s) into the agent prompt.
- Tell the agent whether the card is implementation, review, or documentation.
- Ask the agent to stay within the card boundary and to report any blocked assumptions before branching out.
- If a card touches multiple files, keep the changes tightly coupled to that one card and do not pick up adjacent cleanup work.

