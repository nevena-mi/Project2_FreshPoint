"""
editor.py — A second, narrow LLM pass that edits a raw draft against a
short mechanical checklist, instead of relying on the single generation
prompt to get everything right at once.

Why this exists: across several rounds of tightening the generation
prompt (hard rules, voice blend, concrete-over-abstract), specific
violations kept slipping through one at a time — first generic endings,
then em-dashes, now generic opening lines. Editing an existing draft
against a short checklist is a narrower, easier task for the model than
generating perfectly from scratch, so it's more reliable at actually
catching these than another round of prompt wording.
"""

from src.llm_integration import complete

EDIT_TEMPLATE = """\
Here is a draft LinkedIn post:

---
{draft}
---

Rewrite it, fixing ONLY these things:
- If the opening line is a generic warm-up ("I've been deep in...",
  "As I dive into...", "Lately I've been reflecting on...", "navigating
  the intersection of..."), replace it with a sharp, specific first line
  — a concrete fact, a real number, or a direct claim, not a mood-setting
  sentence.
- If it ends with a generic reflection question ("What do you think?",
  "How are you...?", "Thoughts?"), replace the ending with a specific
  statement or a real, concrete call to action instead.
- Remove every em-dash — replace with a comma, period, or rephrase.
- Remove buzzwords ("game-changer", "wild ride", "in today's landscape",
  "navigating the intersection of").

Keep everything else — the content, the structure, the voice, the
length — exactly the same. Do not add new ideas. Do not make it longer.

Respond with the rewritten post only, no preamble.
"""


def refine_post(draft: str) -> str:
    """Run a draft through the editing pass and return the rewritten text."""
    prompt = EDIT_TEMPLATE.format(draft=draft.strip())
    return complete(prompt, temperature=0.4)
