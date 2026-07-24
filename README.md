# FreshTake

Generates branded LinkedIn posts (2x/week) and a monthly newsletter for an
AI consultant, combining a personal knowledge base (voice, branding, topics)
with fresh daily news.

## Setup

```bash
python -m venv venv
source venv/bin/activate  # on Windows: venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env  # then fill in your API keys
```

## Run

```bash
python -m src.main --mode linkedin
python -m src.main --mode newsletter
```

Output is saved as JSON under `output/`.

## Project structure

```
src/                    # pipeline code
knowledge_base/primary/    # your background, branding, tone & style
knowledge_base/secondary/  # topics + sources to monitor
output/                 # generated posts (saved as JSON)
```

## Docs

- `project_structure.md` — classical PM kickoff
- `agents.md` — coding-agent instructions
- `rag_decision.md` — RAG vs non-RAG decision + defense
