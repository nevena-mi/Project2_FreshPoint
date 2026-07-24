"""
prompt_templates.py — Reusable prompt templates.

Two templates as required by the brief (M4: reusable prompt templates >=2):
  - LINKEDIN_TEMPLATE  : short, punchy, POV-driven post
  - NEWSLETTER_TEMPLATE: longer, more structured, several sections

Both combine the primary KB (brand voice) with the secondary KB / news
(industry context) — the "hybrid" style from the brief.
"""

LINKEDIN_TEMPLATE = """\
You are writing a LinkedIn post in the voice described below. Do not sound \
like generic AI-generated content — be specific, opinionated, and grounded \
in the person's actual background.

--- BRAND / VOICE CONTEXT ---
{primary_context}

--- INDUSTRY CONTEXT / TOPICS ---
{secondary_context}

--- FRESH NEWS TO OPTIONALLY REACT TO ---
{news_context}

Write one LinkedIn post (120-200 words) that:
1. Opens with a clear point of view, not a summary.
2. References at most one news item above, only if it's genuinely relevant.
3. Ends with a short, non-generic call to reflection (not "What do you think?").
4. Matches the tone/style described in the brand context.

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
2. 2-3 short sections, each built around one theme or news item above.
3. A closing personal takeaway or call to action.

Respond with the newsletter text only, no preamble.
"""

DIAGRAM_DECISION_TEMPLATE = """\
Given this post text, decide if a simple diagram would strengthen it:

{post_text}

Reply with JSON only: {{"needs_diagram": true/false, "diagram_type": \
"flow|comparison|timeline|none", "diagram_prompt": "short description if needed"}}
"""
