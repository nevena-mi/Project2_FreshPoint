"""
feedback.py — Post-publication feedback: mark a post as the final/published
version (with edits), and rate its performance.

Ratings are stored per post in output/*.json. Nothing here trains or fine-
tunes anything yet — the "learn from ratings" step is the nice-to-have
that would come later, once enough rated posts exist (see
project_structure.md section 4).
"""

import json
from pathlib import Path

OUTPUT_DIR = Path("output")
VALID_RATINGS = {"green", "orange", "red"}


def list_posts() -> list[dict]:
    """Return every saved post record, most recent first."""
    posts = []
    for path in sorted(OUTPUT_DIR.glob("*.json"), reverse=True):
        record = json.loads(path.read_text(encoding="utf-8"))
        record["_path"] = str(path)
        posts.append(record)
    return posts


def mark_as_final(post_path: str, final_text: str) -> None:
    """Save the actual text that was posted (may differ from the generated draft)."""
    path = Path(post_path)
    record = json.loads(path.read_text(encoding="utf-8"))
    record["status"] = "final"
    record["final_text"] = final_text
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")


def rate_post(post_path: str, rating: str) -> None:
    """Attach a subjective green/orange/red performance rating to a post."""
    if rating not in VALID_RATINGS:
        raise ValueError(f"rating must be one of {VALID_RATINGS}, got {rating!r}")
    path = Path(post_path)
    record = json.loads(path.read_text(encoding="utf-8"))
    record["rating"] = rating
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")


def rated_posts_by_rating(rating: str) -> list[dict]:
    """Nice-to-have hook: pull all posts with a given rating, e.g. to inspect
    what 'green' posts have in common — the starting point for feeding
    ratings back into future prompts."""
    return [p for p in list_posts() if p.get("rating") == rating]
