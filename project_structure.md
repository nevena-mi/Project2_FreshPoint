# project_structure.md — Gonelu

## 1. Project identity
- **Project name:** Gonelu
- **Primary project type:** R&D (building a working AI system within a fixed 2-day window; novel combination of KB + retrieval + news + generation)
- **Defined goal (1 sentence):** Gonelu generates branded, on-topic LinkedIn posts and a monthly newsletter for any user, combining their own background and voice (entered directly in the app) with retrieved source material and optional fresh news.
- **Start / end:** Day 1 morning → Day 2 presentation
- **Why this is a project (tick ≥4):**
  - [x] defined goal
  - [x] limited resources (2 days, 3 people, free/low-cost API tier)
  - [ ] interdisciplinary
  - [x] responsibility for results (graded deliverable)
  - [x] complex (multi-stage pipeline: fetch → chunk → retrieve → generate → edit → store)
  - [x] novel (first time building this exact pipeline)
  - [x] defined start/end

## 2. Objectives (Quality / Time / Cost)

| Constraint | Your objective |
|---|---|
| **Quality** | Generated content must sound like the specific user's POV, not generic AI output — grounded in their own background/tone (entered via the app, not hardcoded), on-topic, and demonstrably different from a raw ChatGPT prompt on the same topic. |
| **Time** | Hard deadline: Day 2 presentation. Internal milestone: working LLM response (KB + at least one prompt template) by end of Day 1. |
| **Cost** | Use free-tier APIs (OpenAI free/low-cost model, NewsAPI free tier) where possible; cap test runs so no single day exceeds a small, predictable API spend. Each generation now runs two LLM calls (draft + edit pass), which roughly doubles per-post cost — still cheap in absolute terms for text generation. |

## 3. Stakeholder analysis (quadrants I–IV)

| Role | Interest | Influence | Quadrant | Engagement in this project |
|---|---|---|---|---|
| Louise (builder + first real user) | H | H | I | Provides real KB content via the app's "Add about you" tab; owns prompt design, retrieval logic, and generation quality |
| Nevena (builder) | H | H | I | Owns news fetching, chunking/selection, Trello + GitHub setup |
| Gordan (builder) | H | H | I | Owns UI (generate/view posts) + feedback loop (mark final version, rating) |
| Instructor | H | H | I | Grades against rubric; needs clear RAG defense, Kanban evidence, working demo |
| Any future user | H | L | II | The product is designed so anyone can input their own background/tone and use it, not just the original builders |
| Classmates | L | L | IV | Informed via required Slack thread share of the one-sentence project description |

## 4. Requirements → implementation

**Use case (1 sentence):** A professional needs a system that turns their own background, voice, and (optionally) fresh news or reference sources into ready-to-post LinkedIn content and a newsletter, without sounding like generic AI output.

**Must have:**

| ID | Must requirement | Maps to (file / module) | How we verify |
|---|---|---|---|
| M1 | Any user can input their own background and tone/style directly in the app | `app.py` ("Add about you" tab) + `knowledge_base.py` (`get_background`/`save_background`/`get_tone_style`/`save_tone_style`) | Enter background/tone in the UI, confirm it's saved and reflected in the next generated post |
| M2 | Ingest secondary KB markdown, chunk it, and retrieve the most relevant pieces for generation | `knowledge_base.py` + `src/chunker.py` + `src/embeddings.py` + `knowledge_base/secondary/` | Confirm chunked secondary context is returned through embedding-based retrieval, ranked by the post's angle |
| M3 | Fetch fresh news relevant to topics, only when explicitly requested | `news_fetcher.py` + `app.py` ("Post from News") | Run "Post from News"; confirm real articles are fetched and the post is built around one; confirm "General Post"/"Newsletter" never fetch news |
| M4 | Chunk/select news down to relevant snippets before prompt injection | `content_pipeline.py` (`_chunk_and_select`, `_select_best_news_item`) | Compare raw article length vs. injected snippet length; confirm the most angle-relevant article is selected |
| M5 | Call LLM to generate a draft, then run a second editing pass against a style checklist | `llm_integration.py` + `content_pipeline.py` + `src/editor.py` | Generated post is grounded in KB + source content; confirm the edit pass measurably reduces generic phrasing/em-dashes vs. the raw draft |
| M6 | Reusable prompt templates (≥2) | `prompt_templates.py` (LinkedIn + newsletter templates) | Both templates produce valid, distinct-format output |
| M7 | End-to-end pipeline commands (CLI + UI) | `main.py` + `app.py` | `python -m src.main --mode linkedin` and `--mode newsletter` run without error; the three Streamlit generate actions each work independently |
| M8 | Uniqueness evidence vs. generic ChatGPT | comparison doc/slide | Side-by-side: Gonelu output vs. plain ChatGPT prompt on same topic |
| M9 | RAG decision documented | `rag_decision.md` | Choice stated + ≥3 criteria addressed; document matches the implemented secondary-side embedding retrieval |
| M10 | Project structured + agents guided | `project_structure.md` (this file), `agents.md` | Sections complete; agents.md referenced when prompting coding agents |
| M11 | UI to generate and review posts, organized by action | `app.py` ("Generate & Review" tab with General Post / Post from News / Newsletter sub-tabs) | A team member can trigger any of the three actions independently and read the result without opening raw JSON |
| M12 | Mark a post as "final/published version" (with edits), and rate its performance | `app.py` ("Performance Feedback" tab) + `src/feedback.py` | A saved post record can be edited, flagged final, and rated; a "Good" rating adds it to voice examples |
| M13 | Ingest PDF, article URL, and YouTube video as extra secondary KB sources | `src/document_processor.py` + `app.py` (Add Sources tab) | Upload/paste one of each type, confirm a new tagged `.md` file appears under `knowledge_base/secondary/ingested/`, gets chunked, and becomes eligible for retrieval |
| M14 | Rebrand: real logo, brand colors, and app theme | `assets/logo.png` + `.streamlit/config.toml` + `app.py` | App shows the real Gonelu logo centered in the header; Streamlit's built-in theme (not fragile CSS) drives the green/gray accent colors throughout |

**Nice to have (build only once Musts M1–M14 are green):**

| Nice-to-have | Why it's deferred |
|---|---|
| A first-run prompt steering brand-new users straight to "Add about you" | Usability polish, not required to prove the core pipeline works |
| Using past ratings at scale (beyond feeding "Good" posts into voice examples) to further tune prompts | Only meaningful once many rated posts exist — a learning loop, not a 2-day build target |

**Won't have this sprint:**

| Won't | Why deferred |
|---|---|
| Diagram/visual generation for posts | Built, then deliberately cut — added complexity with no clear uniqueness payoff versus text quality work |
| Cohere as a secondary LLM fallback | Was scaffolded, never actually wired in, and removed as dead weight |
| A "Favorites" (preferred topics/articles) feature | Explicitly cut — redundant with source ingestion once PDFs/articles/YouTube can be tagged by topic directly |
| Automated publishing directly to LinkedIn | Out of scope for 2 days; output saved locally for manual posting instead |

## 5. WBS (2 levels) → becomes Trello cards

```
1. Structure & board
   1.1 Write project_structure.md
   1.2 Create Trello lists + WIP + DoD
   1.3 Write agents.md
   1.4 Create cards from this WBS
2. Knowledge bases
   2.1 "Add about you" tab (background + tone/style, any user)
   2.2 Secondary KB (topics + ingested sources)
3. Ingest & context
   3.1 Markdown loader
   3.2 Secondary KB chunking
   3.3 Embedding cache + retrieval ranking for secondary KB
   3.4 News fetcher (fresh sources, per-topic query, relevance sort)
   3.5 Chunk/select relevant news snippets + best-match selection by angle
   3.6 PDF / article URL / YouTube ingestion into secondary KB, tagged by topic
4. Generate & differentiate
   4.1 LLM client + .env
   4.2 Prompt templates (LinkedIn + newsletter), first-person framing
   4.3 Second-pass editor (generic openers/endings, em-dashes, buzzwords)
   4.4 End-to-end pipeline command (CLI + UI, 3 separate actions)
   4.5 Uniqueness comparison artifact (vs. generic ChatGPT)
5. UI & feedback
   5.1 UI restructured: Add about you / Add Sources / Generate & Review / Performance Feedback
   5.2 Mark a post as "final/published version" (with edits)
   5.3 Subjective Good/Medium/Poor rating per post
   5.4 "Good" ratings feed the post into voice examples automatically
6. Rebrand & polish
   6.1 Real logo + brand colors extracted from it
   6.2 Streamlit theme via config.toml (reliable, not CSS hacks)
7. Close
   7.1 Finalize rag_decision.md (+ section 7 below)
   7.2 README + demo prep
   7.3 Day 1 / Day 2 Kanban board screenshots
```

## 6. Risks (exactly 3)

| Risk | P (L/M/H) | I (L/M/H) | Strategy | Concrete action |
|---|---|---|---|---|
| News API / LLM cost or rate limits during testing | M | M | Reduction | Cache sample responses for demo; limit live test calls per day; graceful fallback to KB-only content if news fetch fails |
| Generated content still reads as generic "AI-slop" (generic openers/endings, repeated anecdotes) | H | H | Reduction | Second-pass editor checklist; explicit "vary which real fact you use" rule in tone_style.md; run uniqueness comparison before the demo |
| Merge conflicts / lost work across 3 people editing overlapping files (prompt_templates.py, content_pipeline.py) | M | M | Mitigation | Clear "who owns which file today" Slack convention; pull before starting, push right after finishing; resolve conflicts by re-verifying against the actual pushed file, not assumption |

## 7. Bridge to rag_decision.md

The Quality objective — content that sounds authentically like the actual user, not generic — drives a context strategy split in two: the primary KB (background, tone/style, voice examples, now entered by any user via the app) stays small and is injected directly, no retrieval needed. The secondary KB (books, articles, PDFs, YouTube transcripts a user adds) is chunked and embedded once at ingestion, then ranked by semantic similarity to each post's specific angle at generation time. This split exists because the two have fundamentally different scaling behavior: primary content stays small by design, while secondary content can grow unboundedly (a single book alone produces hundreds of chunks) — direct injection breaks down there, real retrieval doesn't. Decision in one line: **primary direct context + secondary-side embedding retrieval** — full defense in `rag_decision.md`. Revisit if primary content itself grows past what comfortably fits in one prompt, or if secondary retrieval needs to consider more than semantic similarity (e.g. recency weighting) as the source library keeps growing.