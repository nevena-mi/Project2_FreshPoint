# Gonelu

Generates branded LinkedIn posts and a monthly newsletter from your own
background, voice, and (optionally) reference sources and fresh news —
built so anyone can use it with their own input, not hardcoded to one person.

## Setup

```bash
python -m venv venv
source venv/bin/activate  # on Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # then fill in your API keys (OPENAI_API_KEY, NEWS_API_KEY)
```

Add the logo asset (required for the app header):

```bash
mkdir -p assets
# place logo.png at assets/logo.png
```

## Run

```bash
streamlit run app.py
```

The app has four tabs:
- **Add about you** — enter your own background and tone/style; this is
  what makes generated posts sound like you specifically
- **Add Sources** — add PDFs, article URLs, or YouTube videos as reference
  material, tagged by topic
- **Generate & Review** — three actions: General Post (no news), Post from
  News (anchored on a real fetched article), and Newsletter
- **Performance Feedback** — rate posts you've marked final; a "Good"
  rating feeds that post back in as a voice example for future generations

CLI is also available for quick prompt testing:

```bash
python -m src.main --mode linkedin
python -m src.main --mode linkedin --angle "why hiring for technical skill alone misses the point"
python -m src.main --mode linkedin --news-only
python -m src.main --mode newsletter
```

Output is saved as JSON under `output/`.

## Project structure

```
src/                       # pipeline code
assets/logo.png            # app logo
.streamlit/config.toml     # Streamlit theme (brand colors)
knowledge_base/primary/    # background, tone & style (set via the app)
knowledge_base/secondary/  # topics + ingested reference sources
output/                    # generated posts (saved as JSON)
```

## Docs

- `project_structure.md` — classical PM kickoff
- `agents.md` — coding-agent instructions
- `rag_decision.md` — RAG decision + defense