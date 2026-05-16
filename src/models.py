from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class JobCandidate:
    title: str
    company: str
    city: str
    url: str
    source: str
    snippet: str = ""
    published_at: str = ""
    company_intro: str = ""
    score: int = 0
    match_reason: str = ""
    risks: list[str] = field(default_factory=list)

    def key(self) -> str:
        return self.url.strip().lower()
