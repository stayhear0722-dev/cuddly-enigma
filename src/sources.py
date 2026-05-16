from __future__ import annotations

from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from .models import JobCandidate
from .search import clean_text


PRIVATE_USE_CHARS = dict.fromkeys(range(0xE000, 0xF8FF + 1), None)


def clean_job_title(value: str) -> str:
    return clean_text(value.translate(PRIVATE_USE_CHARS)).replace("  ", " ")


def fetch_shixiseng_jobs(config: dict) -> list[JobCandidate]:
    timeout = int(config["search"]["timeout_seconds"])
    user_agent = config["search"]["user_agent"]
    headers = {
        "User-Agent": user_agent,
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    keywords = [
        keyword.replace("实习", "")
        for keyword in config.get("profile_analysis", {}).get("role_keywords", [])
    ]
    keywords.extend(["数据分析", "数据运营", "商业分析", "数据产品", "AI数据", "数据标注"])
    keywords = list(dict.fromkeys(keyword for keyword in keywords if keyword))
    jobs: list[JobCandidate] = []
    seen: set[str] = set()

    for keyword in keywords:
        for city in config["locations"]:
            url = (
                "https://www.shixiseng.com/interns?"
                f"page=1&type=intern&keyword={quote(keyword)}&salary=-0&city={quote(city)}"
            )
            try:
                response = requests.get(url, headers=headers, timeout=timeout)
                response.raise_for_status()
            except Exception as exc:
                print(f"[warn] shixiseng failed: {city} {keyword}: {exc}")
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            description = ""
            meta = soup.select_one('meta[name="description"]')
            if meta and meta.get("content"):
                description = clean_text(meta["content"])

            for item in soup.select(".intern-item"):
                link = item.select_one('a[href*="/intern/"]')
                if not link:
                    continue
                href = link.get("href") or ""
                title = clean_job_title(link.get_text(" "))
                if not href or not title:
                    continue
                if href.startswith("//"):
                    href = "https:" + href
                elif href.startswith("/"):
                    href = "https://www.shixiseng.com" + href
                key = href.split("?")[0]
                if key in seen:
                    continue
                seen.add(key)
                company_node = item.select_one(".intern-detail__company a.title")
                company = clean_text(company_node.get_text(" ")) if company_node else "待确认"
                tip_nodes = [clean_job_title(node.get_text(" ")) for node in item.select(".tip")]
                label_nodes = [clean_job_title(node.get_text(" ")) for node in item.select(".intern-label, .company-label")]
                snippet = " ".join(
                    part
                    for part in [
                        city,
                        keyword,
                        company,
                        " ".join(tip_nodes),
                        " ".join(label_nodes),
                        description,
                    ]
                    if part
                )
                jobs.append(
                    JobCandidate(
                        title=title,
                        company=company or "待确认",
                        city=city,
                        url=href,
                        source="实习僧",
                        snippet=snippet,
                    )
                )
    return jobs
