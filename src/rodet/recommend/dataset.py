from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

import pandas as pd

from rodet.recommend.car_dictionary import CAR_PATTERNS
from rodet.storage.db import connect, init_db


@dataclass(frozen=True)
class TrainingExample:
    post_id: str
    text: str
    label: str


def _compile_patterns(patterns: dict[str, list[str]]):
    compiled: dict[str, list[re.Pattern]] = {}
    for label, pats in patterns.items():
        compiled[label] = [re.compile(p, flags=re.IGNORECASE) for p in pats]
    return compiled


_COMPILED = _compile_patterns(CAR_PATTERNS)


def extract_label_from_comments(comments: Iterable[str]) -> str | None:
    """Return the most-mentioned label or None if nothing matched."""
    counts = {label: 0 for label in _COMPILED.keys()}

    for text in comments:
        for label, pats in _COMPILED.items():
            for pat in pats:
                if pat.search(text):
                    counts[label] += 1
                    break

    best_label, best_count = max(counts.items(), key=lambda kv: kv[1])
    if best_count == 0:
        return None
    return best_label


def build_training_dataframe(min_label_count: int = 1) -> pd.DataFrame:
    """
    Build a dataframe with columns:
      - post_id
      - text
      - label
    """
    conn = connect()
    init_db(conn)

    posts = conn.execute(
        "SELECT post_id, title, body FROM posts ORDER BY created_utc DESC"
    ).fetchall()

    rows = []
    for p in posts:
        post_id = p["post_id"]
        text = f"{p['title']}\n\n{p['body'] or ''}".strip()

        comments = conn.execute(
            "SELECT body FROM comments WHERE post_id = ?",
            (post_id,),
        ).fetchall()
        comment_texts = [c["body"] for c in comments]

        label = extract_label_from_comments(comment_texts)
        if label is None:
            continue

        rows.append({"post_id": post_id, "text": text, "label": label})

    conn.close()
    df = pd.DataFrame(rows)

    # opcional: filtrar clases con pocos ejemplos
    if not df.empty and min_label_count > 1:
        vc = df["label"].value_counts()
        keep = set(vc[vc >= min_label_count].index)
        df = df[df["label"].isin(keep)].reset_index(drop=True)

    return df