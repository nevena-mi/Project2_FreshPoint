"""
prompt_templates.py — Reusable prompt templates.

Two templates as required by the brief (M4: reusable prompt templates >=2):
  - LINKEDIN_TEMPLATE  : short, punchy, POV-driven post
  - NEWSLETTER_TEMPLATE: longer, more structured, several sections

LINKEDIN_TEMPLATE is written as first-person embodiment ("you ARE this
person, write as yourself") rather than third-person instruction-following
("mimic this description of someone"). Source material and news are
clearly marked as optional grounding, not equal-weight content, and rules
are kept short and plain rather than a long taxonomy competing for
attention.

Both templates take a news_requirement string, supplied by
content_pipeline.py, which changes depending on whether this is a normal
generation (news is optional flavor) or a news_only generation (the post
must be built around a specific news item) — see content_pipeline.py's
generate_post() for exactly how that string is built.
"""

LINKEDIN_TEMPLATE = """\
You are writing this LinkedIn post as yourself — this is not a description \
to follow, this is who you are. Write in first person, in your own voice.

--- WHO YOU ARE AND HOW YOU WRITE ---
{primary_context}

--- OPTIONAL SOURCE MATERIAL FOR THIS POST (use only if it genuinely strengthens the point — don't force it in; if nothing here is relevant, write from who you are above instead) ---
{secondary_context}

--- RECENT NEWS ---
{news_context}
{news_requirement}

RULES:
- Never end with a generic call-to-reflection question ("What do you
  think?", "Thoughts?", "How are you ensuring...?"). If you close with a
  question, make it sharp and specific, not a broad invitation for comments.
- Default to short, unnumbered lines. Only use a numbered list if the
  content truly cannot be expressed any other way, and each point must be
  a real diagnosis, not a decorative summary.
- No buzzwords ("game-changer", "wild ride", "in today's landscape"), no
  hedging ("some might say"), no em-dashes.
- Ground the post in something specific and personal — not an abstract
  industry take. Pick one clear, specific angle to write about — don't
  try to cover everything above.

Write one LinkedIn post, 120-200 words. Respond with the post text only,
no preamble.
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