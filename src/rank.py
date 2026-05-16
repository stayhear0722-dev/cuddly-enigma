from __future__ import annotations

import re
from urllib.parse import urlparse

from .models import JobCandidate


COMPANY_PATTERNS = [
    re.compile(r"实习招聘-([\u4e00-\u9fa5A-Za-z0-9（）()·\-/\s]{2,30})实习生招聘"),
    re.compile(r"招聘-([\u4e00-\u9fa5A-Za-z0-9（）()·\-/\s]{2,30})实习生招聘"),
    re.compile(r"公司[:：]\s*([\u4e00-\u9fa5A-Za-z0-9（）()·\-\s]{2,30})"),
    re.compile(r"([\u4e00-\u9fa5A-Za-z0-9（）()·\-]{2,30})(?:招聘|校招|实习)"),
]


def contains_any(text: str, keywords: list[str]) -> bool:
    lower = text.lower()
    return any(keyword.lower() in lower for keyword in keywords)


def count_matches(text: str, keywords: list[str]) -> int:
    lower = text.lower()
    return sum(1 for keyword in keywords if keyword.lower() in lower)


def infer_city(text: str, cities: list[str]) -> str:
    for city in cities:
        if city in text:
            return city
    return "待确认"


def infer_company(job: JobCandidate, text: str) -> str:
    if job.company != "待确认":
        return job.company
    for pattern in COMPANY_PATTERNS:
        match = pattern.search(text)
        if match:
            value = re.sub(r"\s+", "", match.group(1))
            if 2 <= len(value) <= 30:
                return value
    host = urlparse(job.url).netloc.lower().replace("www.", "")
    return host or "待确认"


def build_company_intro(text: str, industries: list[str]) -> str:
    size = "规模公开信息未明确"
    for pattern in [
        r"(\d{2,6}\s*-\s*\d{2,6}人)",
        r"(\d{2,6}人以上)",
        r"(\d{2,6}人以内)",
        r"(少于\d{2,6}人)",
    ]:
        match = re.search(pattern, text)
        if match:
            size = match.group(1)
            break

    matched_industries = [item for item in industries if item.lower() in text.lower()]
    industry = "、".join(matched_industries[:3]) if matched_industries else "行业公开信息未明确"

    business = "主营业务公开信息未明确"
    for marker in ("主营业务", "业务包括", "专注于", "致力于", "公司介绍", "关于我们"):
        index = text.find(marker)
        if index >= 0:
            business = text[index : index + 90]
            break
    return f"{size}；{industry}；{business}"


def score_job(job: JobCandidate, page_text: str, config: dict) -> JobCandidate | None:
    text = f"{job.title} {job.snippet} {page_text}"
    if contains_any(text, config["exclude_keywords"]):
        return None

    role_hits = count_matches(text, config["role_keywords"])
    grad_hits = count_matches(text, config["graduation_keywords"])
    industry_hits = count_matches(text, config["industries"])
    city = infer_city(text, config["locations"])

    if role_hits == 0:
        return None
    if city == "待确认":
        return None

    score = 50
    score += min(role_hits, 4) * 10
    score += min(grad_hits, 2) * 8
    score += min(industry_hits, 3) * 5
    if any(word in text for word in ("数据清洗", "统计", "机器学习", "建模", "Excel", "Python", "SQL")):
        score += 10
    if job.source in ("牛客", "实习僧", "智联招聘", "猎聘", "前程无忧", "BOSS直聘"):
        score += 5
    if is_listing_page(job.url):
        score -= 15
    score = min(score, 100)

    job.city = city
    job.company = infer_company(job, text)
    job.company_intro = build_company_intro(text, config["industries"])
    job.score = score
    job.match_reason = build_match_reason(text)
    job.risks = build_risks(job, text, grad_hits)
    return job


def is_listing_page(url: str) -> bool:
    return any(
        marker in url
        for marker in (
            "/interns?",
            "/zhaopin/",
            "/joblist/",
            "/jobs?",
            "/search",
        )
    )


def build_match_reason(text: str) -> str:
    reasons = []
    if any(word in text for word in ("数据分析", "数据运营", "商业分析")):
        reasons.append("岗位方向与数据分析/数据运营目标一致")
    if any(word in text for word in ("Excel", "统计", "报表", "指标")):
        reasons.append("能对应简历中的 Excel、基础统计和资料汇总能力")
    if any(word in text for word in ("机器学习", "建模", "预测", "算法", "Python", "SQL")):
        reasons.append("能体现建模、数据清洗和结构化数据处理项目经验")
    if any(word in text for word in ("AI", "人工智能", "智能硬件", "物联网", "IoT")):
        reasons.append("公司或岗位方向贴近 AI/智能硬件/互联网行业")
    return "；".join(reasons[:3]) or "岗位关键词与你的数据类实习目标匹配"


def build_risks(job: JobCandidate, text: str, grad_hits: int) -> list[str]:
    risks: list[str] = []
    if grad_hits == 0:
        risks.append("页面未明确写 27届/2027届，需打开链接确认")
    if job.company == "待确认":
        risks.append("公司名称需打开页面确认")
    if any(word in text for word in ("登录", "验证码")):
        risks.append("投递可能需要登录或验证码")
    if is_listing_page(job.url):
        risks.append("该链接可能是搜索列表页，需点进具体岗位后投递")
    if not any(word in text for word in ("发布", "更新", "2026", "2025")):
        risks.append("发布时间不明确，可能已下线")
    return risks
