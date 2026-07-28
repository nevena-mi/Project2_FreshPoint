# Gonelu — Agent Guide

## Project Purpose
Gonelu generates branded LinkedIn posts and a monthly newsletter for any
user by combining a personal knowledge base (entered directly in the app
by anyone — not hardcoded to one person), chunked-and-retrieved secondary
sources, and fresh news. `project_structure.md` is the source of truth
for scope, and agents should use the relevant Must IDs from that file
when scoping work. If a task does not map cleanly to a Must ID, treat it
as out of scope unless the user explicitly says otherwise.

This file is a working document written during the build, not a
retrospective idealisation of it — it includes what actually went wrong,
not just what worked.

## 1. Which agents, and for what

| Agent | Used for |
|---|---|
| Claude (chat, with file access) | Architecture decisions, multi-file refactors, writing and reviewing modules, verifying behaviour with test harnesses, drafting docs |
| Codex | Targeted single-file edits, mostly on `news_fetcher.py` |

Humans owned every decision. Agents produced code and arguments; the
team chose what to keep.

## 2. Standing instructions we gave the agents

These were given repeatedly, because agents drift back to defaults
across a long session.

1. Be a critical reviewer, not an agreeable one. Find weaknesses, flawed
   logic, and blind spots. Contradict us when we are wrong. State
   uncertainty explicitly instead of guessing confidently.
2. Verify before asserting. If a claim about the codebase can be checked
   by reading the code, read the code. If a claim about an API can be
   checked by searching, search.
3. Do not silently change things you were not asked to change. Flag it
   and wait.
4. No em dashes or hyphens used as punctuation in generated prose.
5. Give complete, runnable code and literal step by step instructions,
   not partial snippets or abstract directions.

## Stack & How To Run
- Python: tested in this repo with Python 3.14.6.
- Install deps:
  ```bash
  python -m venv venv
  source venv/bin/activate  # on Windows: venv\Scripts\activate
  pip install -r requirements.txt
  ```
- CLI run:
  ```bash
  python -m src.main --mode linkedin
  python -m src.main --mode linkedin --angle "why hiring for technical skill alone misses the point"
  python -m src.main --mode linkedin --news-only
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
  - personal voice / background / tone / voice examples markdown
  - populated via the app's "Add about you" tab, not hand-edited by default
- `knowledge_base/secondary/`
  - `topics.md` plus ingested secondary sources under `ingested/`
  - secondary content is chunked and retrieved by embeddings
- `src/prompt_templates.py`
  - LinkedIn and newsletter generation prompts
- `src/editor.py`
  - second-pass editing checklist run on every draft (generic openers/endings, em-dashes, buzzwords)
- `src/content_pipeline.py`
  - prompt assembly and post generation flow
- `src/main.py`
  - CLI entry point, for prompt testing
- `app.py`
  - Streamlit UI: "Add about you" (user inputs their own background/tone),
    "Add Sources" (PDF/article/YouTube ingestion), "Generate & Review"
    (General Post / Post from News / Newsletter sub-tabs), and
    "Performance Feedback" (rate posts, feed Good ones into voice examples)
- `assets/logo.png` + `.streamlit/config.toml`
  - the real logo and Streamlit's built-in theme config (brand colors) —
    prefer config.toml over CSS injection for theming; CSS injection has
    proven unreliable in this project (see Failure modes below)
- `src/chunker.py`
  - deterministic chunking for the secondary KB
- `src/embeddings.py`
  - embedding cache and retrieval ranking for secondary chunks
- `src/document_processor.py`
  - PDF, article URL, and YouTube ingestion into the secondary KB
- `src/knowledge_base.py`
  - KB loading, context assembly, and output saving

## Conventions For Agent Edits
- Prefer small, explicit edits over broad refactors.
- Use existing file names and module boundaries; add new files only when the task needs a new capability or a companion note.
- Put reusable source code in `src/`.
- Put markdown knowledge-base content in `knowledge_base/` and keep it as markdown.
- Avoid inventing new config formats, CLI flags, or APIs unless the task explicitly requires them.
- If a change affects behavior, update the relevant docs in the same change if they are part of the requested scope.

## 3. Definition of Done
A change is done when all of the following hold. This list exists
because several of these were violated at least once during the build.

- The code runs. Not "should run", actually executed at least once.
- Functions called directly from a Streamlit button have error handling.
  An unhandled exception in an ingest or generation function crashes the
  demo, which is the highest cost failure available to us this week.
- External API calls fail gracefully: missing key or failed request
  returns an empty result or raises a caught, explained error, never a
  silent wrong answer.
- Nothing was changed outside the stated scope of the task.
- Any known remaining gap is written down, not left implicit.

## 4. Verification practices that earned their place
- **Read the source before generating anything derived from it.** When
  generating UML diagrams, the agent grepped every source file for
  classes, functions, and constants first. This caught that only three
  real classes exist in the codebase (`KnowledgeBase`, `GeneratedPost`,
  `NewsItem`) and the rest is procedural. Without that step the diagram
  would have contained invented classes.
- **Build a stub harness rather than claiming untestable things work.**
  The image generation feature was tested with a fake OpenAI client
  returning both possible response shapes (`b64_json` and `url`), driven
  through Streamlit's AppTest. This verified brief construction, byte
  extraction, file saving, session state resets, and JSON record updates.
  It did not verify the live API call, and that limitation was stated
  explicitly rather than papered over.
- **Separate "I tested this" from "I believe this."** Every agent claim
  in this project was expected to carry that distinction. Where the
  agent could not test something, for example the real cost and
  permissions behaviour of `gpt-image-1`, it said so.

## 5. Failure modes we actually hit
- **Stale file re-uploads reverting fixes.** More than once, an older
  copy of a file was re-uploaded after fixes had been applied, silently
  undoing them. Mitigation: check that an incoming file builds on the
  current version before merging, especially when two people are editing
  the same module through different agents.
- **Instructions buried in long prompts get ignored.** The rule against
  generic call-to-reflection closers lived only in `tone_style.md` and
  was ignored by the generation model. Moving it directly into the RULES
  block of `prompt_templates.py` improved compliance, though not
  perfectly: a generated post still ended with "How are you ensuring
  that human connection remains at the forefront of your AI initiatives?",
  which the rules explicitly forbid. Position and repetition in a prompt
  matter more than mere presence. **Update:** this kept recurring even
  after that fix, in new forms (generic openers instead of endings) — the
  second-pass editor (`src/editor.py`) was added as a more reliable,
  mechanical check rather than relying on generation-prompt wording alone.
- **Negation does not work reliably in image prompts.** The OpenAI images
  API exposes only one prompt string, with no negative prompt parameter.
  Writing "no faces" or "no gears" into that string still produced faces
  and gears, because the model keys on the mentioned concept. The fix was
  to keep avoidance rules as instructions to the brief-writing step only,
  and require the final brief to be pure positive description. General
  lesson: constraints must be enforced where they can actually be
  enforced, not merely stated near the thing you want to constrain.
- **Debugging output left in place.** A `print(prompt)` statement in
  `content_pipeline.py` dumped the full prompt to console on every
  generation. It was flagged repeatedly and deliberately left untouched
  by the agent because removing it was never explicitly authorised.
  Correct agent behaviour, but it illustrates that flagging is not
  fixing, and open items need an owner. **Update:** subsequently removed
  once explicitly authorised.
- **Model names are perishable.** Cohere's `command-r-plus` was
  deprecated without warning mid-project. Model identifiers are
  configuration that expires, not constants. The Cohere fallback was
  later removed from the project entirely.

## 6. Sequencing rule we settled on
Lock down function boundaries and return signatures first, then layer
error handling on top. Doing both at once produced churn, because error
handling written against an interface that is still moving has to be
rewritten anyway. This was a correction the team made against the
agent's initial suggestion, and it held up.

## 7. When we stopped
Deduplication of overlapping chunks was documented as a known limitation
rather than solved, because iteration on it had clearly reached
diminishing returns against a two-day deadline. Deciding to write down a
limitation is a legitimate outcome, and agents should be told when that
decision has been made so they stop optimising it.

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