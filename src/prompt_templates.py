"""
prompt_templates.py — Reusable prompt templates.

Two templates as required by the brief (M4: reusable prompt templates >=2):
  - LINKEDIN_TEMPLATE  : short, punchy, POV-driven post
  - NEWSLETTER_TEMPLATE: longer, more structured, several sections

Both combine the primary KB (brand voice) with the secondary KB / news
(industry context) — the "hybrid" style from the brief.

LINKEDIN_TEMPLATE explicitly separates "hard rules" (things to never do,
pulled directly from tone_style.md) from "structural mimicry" (telling the
model to structure the post like your real example posts, not just
vaguely "match the tone"). Soft instructions like "match the tone/style"
are easy for the model to nod at without actually following — naming the
exact phrases to avoid and pointing at a concrete example to structurally
mirror gets much more reliable results.
"""

LINKEDIN_TEMPLATE = """\
You are writing a LinkedIn post in the voice described below. Do not sound \
like generic AI-generated content — be specific, opinionated, and grounded \
in the person's actual background.

--- VOICE, BACKGROUND, AND REAL EXAMPLE POSTS (mirror this structure) ---
{primary_context}

--- RELEVANT SOURCE MATERIAL FOR THIS POST ---
{secondary_context}

--- FRESH NEWS TO OPTIONALLY REACT TO ---
{news_context}

HARD RULES — do not violate these, they come directly from this person's
own stated preferences:
- Do not end with a generic call-to-reflection question (e.g. "What do
  you think?", "How are you ensuring...?", "Reflect on this: ..."). If you
  close with a question at all, it must be sharp and specific, not a
  broad invitation for comments.
- Do not use generic LinkedIn-AI phrasing like "game-changer", "wild
  ride", "in today's landscape", or similar buzzwords, unless a real
  example post above actually uses that kind of language.
- Do not hedge ("some might say", "it could be argued") — take a clear
  position.

STRUCTURAL GUIDANCE:
- If a real example post appears in the voice/background context above,
  mirror its structure and rhythm (e.g. concrete anecdote, numbered
  contrasts, a short punchy insight after each point) rather than writing
  a generic think-piece shape.
- Ground the post in a specific moment, decision, or detail — not an
  abstract industry observation.

Write one LinkedIn post (120-200 words) that:
1. Opens with a clear point of view, not a summary.
2. {news_requirement}
3. Follows the hard rules and structural guidance above exactly.

Respond with the post text only, no preamble.
"""

NEWSLETTER_TEMPLATE = """\
You are writing this person's monthly newsletter. Use their voice, not a \
generic newsletter tone.

--- BRAND / VOICE CONTEXT ---
{primary_context}

--- INDUSTRY CONTEXT / TOPICS ---
{secondary_context}

--- FRESH NEWS ITEMS ---
{news_context}

Write a newsletter (350-500 words) with:
1. A one-line personal opener.
2. {news_requirement}
3. A closing personal takeaway or call to action.

Respond with the newsletter text only, no preamble.
"""