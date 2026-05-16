from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from .models import JobCandidate


HEADER = [
    "url",
    "first_seen",
    "title",
    "company",
    "city",
    "source",
    "score",
]


def ensure_history(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(HEADER)


def load_seen_urls(path: Path) -> set[str]:
    ensure_history(path)
    seen: set[str] = set()
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            url = (row.get("url") or "").strip().lower()
            if url:
                seen.add(url)
    return seen


def append_history(path: Path, jobs: list[JobCandidate]) -> None:
    ensure_history(path)
    today = date.today().isoformat()
    with path.open("a", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh)
        for job in jobs:
            writer.writerow(
                [
                    job.url,
                    today,
                    job.title,
                    job.company,
                    job.city,
                    job.source,
                    job.score,
                ]
            )
