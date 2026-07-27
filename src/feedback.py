"""
feedback.py — Post-publication feedback: mark a post as the final/published
version (with edits), and rate its performance.

Ratings are stored per post in output/*.json. A post rated "good" feeds back
into the voice: knowledge_base.add_voice_example() gets called for it (see
app.py's Feedback tab), so future generations draw on writing that's
actually confirmed to work, not just anything that got published. That's
the "feed the logic with good and bad" loop — "medium"/"poor" ratings are
recorded but deliberately don't feed anything back in yet.
"""

import json
from pathlib import Path

OUTPUT_DIR = Path("output")
VALID_RATINGS = {"good", "medium", "poor"}


def list_posts(status: str | None = None) -> list[dict]:
    """Return saved post records, most recent first.

    status=None (default) returns everything, drafts included — unchanged
    behavior for any existing caller.
    status="final" returns only posts that have been marked as final via
    mark_as_final(). Use this in the Feedback tab so drafts never show up
    there; a post should only be rateable once it's actually been posted,
    not while it's still a draft.
    """
    posts = []
    for path in sorted(OUTPUT_DIR.glob("*.json"), reverse=True):
        record = json.loads(path.read_text(encoding="utf-8"))
        record["_path"] = str(path)
        if status is not None and record.get("status") != status:
            continue
        posts.append(record)
    return posts


def mark_as_final(post_path: str, final_text: str) -> None:
    """Save the actual text that was posted (may differ from the generated draft).

    Does NOT touch voice_examples.md — marking a post final just means it
    was published, not that it was good. See mark_voice_example_added() /
    app.py's Feedback tab for the actual "good post -> voice example" step.
    """
    path = Path(post_path)
    record = json.loads(path.read_text(encoding="utf-8"))
    record["status"] = "final"
    record["final_text"] = final_text
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")


def rate_post(post_path: str, rating: str) -> None:
    """Attach a subjective good/medium/poor performance rating to a post."""
    if rating not in VALID_RATINGS:
        raise ValueError(f"rating must be one of {VALID_RATINGS}, got {rating!r}")
    path = Path(post_path)
    record = json.loads(path.read_text(encoding="utf-8"))
    record["rating"] = rating
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")


def mark_voice_example_added(post_path: str) -> None:
    """Record that this specific post has already been appended to
    voice_examples.md, so re-rating it "good" again (or re-rating it away
    and back) doesn't insert a duplicate entry."""
    path = Path(post_path)
    record = json.loads(path.read_text(encoding="utf-8"))
    record["added_to_voice_examples"] = True
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")