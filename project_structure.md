# project_structure.md — FreshPoint

## 1. Project identity
- **Project name:** FreshPoint
- **Primary project type:** R&D (building a working AI system within a fixed 2-day window; novel combination of KB + live news + generation)
- **Defined goal (1 sentence):** FreshPoint generates branded, on-topic LinkedIn posts (2x/week minimum) and a monthly newsletter for an AI consultant, combining their personal brand voice with fresh industry news, with optional diagrams on select posts.
- **Start / end:** Day 1 morning → Day 2 presentation
- **Why this is a project (tick ≥4):**
  - [x] defined goal
  - [x] limited resources (2 days, 2 people, free/low-cost API tier)
  - [ ] interdisciplinary
  - [x] responsibility for results (graded deliverable)
  - [x] complex (multi-stage pipeline: fetch → chunk → generate → optional diagram → store)
  - [x] novel (first time building this exact pipeline)
  - [x] defined start/end

## 2. Objectives (Quality / Time / Cost)

| Constraint | Your objective |
|---|---|
| **Quality** | Generated content must sound like a specific person's POV, not generic AI output — branded (colors/tone consistent with KB), on-topic (AI, Product, Leadership, Coaching), and demonstrably different from a raw ChatGPT prompt on the same topic. |
| **Time** | Hard deadline: Day 2 presentation. Internal milestone: working LLM response (KB + at least one prompt template) by end of Day 1. |
| **Cost** | Use free-tier APIs (OpenAI free/low-cost model, NewsAPI free tier) where possible; cap test runs so no single day exceeds a small, predictable API spend; diagram generation is opt-in per post, not run automatically on every post, to control cost. Cohere is a fallback-only call (used only if OpenAI fails), so it adds no cost in normal operation. |

## 3. Stakeholder analysis (quadrants I–IV)

| Role | Interest | Influence | Quadrant | Engagement in this project |
|---|---|---|---|---|
| Louise (end user + builder) | H | H | I | The actual "AI consultant" persona the system is built for; provides real KB content (background, branding, tone); owns input processing + prompt/post generation; team can adapt the system for themselves after |
| Nevena (builder) | H | H | I | Owns news fetching + chunking/selection, Trello + GitHub setup |
| Gordan (builder) | H | H | I | Owns UI (generate/view posts) + feedback loop (mark final version, subjective rating) |
| Instructor | H | H | I | Grades against rubric; needs clear RAG defense, Kanban evidence, working demo |
| LinkedIn audience / readers | L | L | IV | Passive — ultimate quality bar for "does this sound authentic," not directly engaged during build |
| Classmates | L | L | IV | Informed via required Slack thread share of the one-sentence project description |

## 4. Requirements → implementation

**Use case (1 sentence):** An AI consultant needs a system that turns their background, brand voice, and fresh industry news into ready-to-post LinkedIn content (and a monthly newsletter) without sounding like generic AI output.

**Must have:**

| ID | Must requirement | Maps to (file / module) | How we verify |
|---|---|---|---|
| M1 | Ingest primary KB markdown (background, branding, tone/style) | `knowledge_base.py` + `knowledge_base/primary/` | Run pipeline, confirm KB text appears in generated prompt |
| M2 | Ingest secondary KB markdown (topics + sources) | `knowledge_base.py` + `knowledge_base/secondary/` | Same — topics list correctly parsed |
| M3 | Fetch fresh news relevant to topics | `news_fetcher.py` | Run with valid API key, confirm real articles returned; confirm graceful empty-list fallback without key |
| M4 | Chunk/select news down to relevant snippets before prompt injection | `content_pipeline.py` (`_chunk_and_select`) | Compare raw article length vs. injected snippet length in a test run |
| M5 | Call LLM with combined KB + news context (OpenAI primary, Cohere fallback if OpenAI fails) | `llm_integration.py` + `content_pipeline.py` | Generated post references both brand voice and a real news item; fallback path triggers correctly when OpenAI call is forced to fail |
| M6 | Reusable prompt templates (≥2) | `prompt_templates.py` (LinkedIn + newsletter templates) | Both templates produce valid, distinct-format output |
| M7 | End-to-end pipeline command | `main.py` | `python -m src.main --mode linkedin` and `--mode newsletter` both run without error |
| M8 | Uniqueness evidence vs. generic ChatGPT | comparison doc/slide | Side-by-side: FreshPoint output vs. plain ChatGPT prompt on same topic |
| M9 | RAG decision documented | `rag_decision.md` | Choice stated + ≥3 criteria addressed |
| M10 | Project structured + agents guided | `project_structure.md` (this file), `agents.md` | Sections complete; agents.md referenced when prompting coding agents |
| M11 | UI to generate and view posts | `app.py` | A team member can trigger generation and read the result without opening raw JSON |
| M12 | Mark a post as "final/published version" (with edits) | `app.py` + `src/feedback.py` + `output/` storage | A saved post record can be edited and flagged as the actual version that was posted |
| M13 | Ingest PDF, audio, and YouTube video as extra secondary KB sources | `src/document_processor.py` + `app.py` (Add Sources tab) | Upload one of each type, confirm a new .md file appears under `knowledge_base/secondary/ingested/` and its content shows up in the next generated post's context |
| M14 | Let the user record favorite topics/articles to steer content | `knowledge_base.py` (`add_favorite`) + `app.py` (Favorites tab) + `knowledge_base/primary/favorites.md` | Add a favorite via the UI, confirm it appears in `favorites.md` and in the primary KB context on next load |

**Nice to have (build only once Musts M1–M14 are green):**

| Nice-to-have | Why it's deferred |
|---|---|
| Subjective feedback rating (green/orange/red) per post | Useful signal for future tuning, but inherently subjective and not needed to prove the core pipeline works |
| Using past ratings (including "red"/underperforming posts) to adjust future prompts | Only meaningful once enough rated posts exist — a learning loop, not a 2-day build target |

**Won't have this sprint:**

| Won't | Why deferred |
|---|---|
| Full vector RAG stack (embeddings, vector DB) | Corpus is small and personal; live news fetch + light chunking covers freshness without the added build cost — see `rag_decision.md` |
| Automated publishing directly to LinkedIn | Out of scope for 2 days; output saved locally for manual posting instead |
| Automatic post-success feedback/rating loop | Nice-to-have only, subjective to measure reliably in 2 days |

## 5. WBS (2 levels) → becomes Trello cards

```
1. Structure & board
   1.1 Write project_structure.md
   1.2 Create Trello lists + WIP + DoD
   1.3 Write agents.md
   1.4 Create cards from this WBS
2. Knowledge bases
   2.1 Primary KB (background, branding, tone/style)
   2.2 Secondary KB (topics + sources)
3. Ingest & context
   3.1 Markdown loader
   3.2 News fetcher (fresh sources)
   3.3 Chunk/select relevant news snippets
   3.4 PDF / audio / YouTube ingestion into secondary KB
   3.5 Favorites tracking (topics/articles) into primary KB
4. Generate & differentiate
   4.1 LLM client + .env
   4.2 Prompt templates (LinkedIn + newsletter)
   4.3 End-to-end pipeline command
   4.4 Optional diagram decision step
   4.5 Uniqueness comparison artifact (vs. generic ChatGPT)
5. UI & feedback
   5.1 UI to trigger generation and view posts
   5.2 Mark a post as "final/published version" (with edits)
   5.3 (Nice to have) Subjective green/orange/red rating per post
   5.4 (Nice to have) Feed ratings back into future prompts
6. Close
   6.1 Finalize rag_decision.md (+ section 7 below)
   6.2 README + demo prep
   6.3 Day 1 / Day 2 Kanban board screenshots
```

## 6. Risks (exactly 3)

| Risk | P (L/M/H) | I (L/M/H) | Strategy | Concrete action |
|---|---|---|---|---|
| News API / LLM cost or rate limits during testing | M | M | Reduction | Cache sample responses for demo; limit live test calls per day; graceful fallback to KB-only content if news fetch fails |
| Generated content still reads as generic "AI-slop" | M | H | Reduction | Run uniqueness comparison by midday Day 2; deepen KB detail (real background, real example post) rather than relying on prompt wording alone |
| Diagram/visual feature blows the time budget | M | M | Mitigation | Keep diagram generation as a separate, skippable pipeline step (already isolated in `content_pipeline.py`); only build it once text MVP (M1–M7) is solid |

## 7. Bridge to rag_decision.md

The AI consultant's Quality objective — content that sounds authentically like them, not generic — drives a context strategy built on a small, stable personal KB (M1, M2) rather than large-scale retrieval. None of the Musts force a search-over-large-corpus approach: the personal KB is a handful of files that fit entirely in a prompt (M1, M2), and freshness (M3) is solved by fetching a few live articles per run rather than searching a stored archive. Query diversity is also low — one or two posts per week from a predictable, small topic set, not many unpredictable questions against a large library. Decision in one line: **non-RAG, with a lightweight chunk/select step (M4) over freshly fetched news** — full defense in `rag_decision.md`. Revisit when the news/article archive grows large enough that finding the most relevant *past* article (not just today's) becomes the bottleneck, or when the personal KB itself grows past what comfortably fits in one prompt.