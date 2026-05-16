from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus, unquote, urlparse, parse_qs

import requests
from bs4 import BeautifulSoup

from .models import JobCandidate


SEARCH_ENDPOINT = "https://www.bing.com/search?q={query}&count=10"
BING_RSS_ENDPOINT = "https://www.bing.com/search?format=rss&q={query}"
DUCKDUCKGO_ENDPOINT = "https://duckduckgo.com/html/?q={query}"


def clean_text(value: str) -> str:
    text = html.unescape(value or "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_bing_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc.endswith("bing.com") and parsed.path == "/ck/a":
        qs = parse_qs(parsed.query)
        for key in ("u", "url"):
            if key in qs and qs[key]:
                value = qs[key][0]
                if value.startswith("a1"):
                    value = value[2:]
                return unquote(value)
    return url


def infer_source(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if "nowcoder" in host:
        return "牛客"
    if "shixiseng" in host:
        return "实习僧"
    if "zhaopin" in host:
        return "智联招聘"
    if "liepin" in host:
        return "猎聘"
    if "51job" in host:
        return "前程无忧"
    if "zhipin" in host:
        return "BOSS直聘"
    return host or "搜索结果"


def fetch_search_results(
    query: str,
    *,
    timeout: int,
    user_agent: str,
) -> list[JobCandidate]:
    combined: list[JobCandidate] = []
    seen: set[str] = set()
    backends = [
        fetch_duckduckgo_results,
        fetch_bing_rss_results,
        fetch_bing_html_results,
    ]
    for backend in backends:
        try:
            results = backend(query, timeout=timeout, user_agent=user_agent)
        except Exception:
            continue
        for result in results:
            key = result.key()
            if not key or key in seen:
                continue
            seen.add(key)
            combined.append(result)
    return combined


def fetch_bing_html_results(
    query: str,
    *,
    timeout: int,
    user_agent: str,
) -> list[JobCandidate]:
    headers = {
        "User-Agent": user_agent,
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    url = SEARCH_ENDPOINT.format(query=quote_plus(query))
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    results: list[JobCandidate] = []
    for item in soup.select("li.b_algo"):
        link = item.select_one("h2 a")
        if not link or not link.get("href"):
            continue
        target_url = normalize_bing_url(link["href"])
        title = clean_text(link.get_text(" "))
        snippet_node = item.select_one(".b_caption p")
        snippet = clean_text(snippet_node.get_text(" ") if snippet_node else "")
        results.append(
            JobCandidate(
                title=title,
                company="待确认",
                city="待确认",
                url=target_url,
                source=infer_source(target_url),
                snippet=snippet,
            )
        )
    return results


def fetch_bing_rss_results(
    query: str,
    *,
    timeout: int,
    user_agent: str,
) -> list[JobCandidate]:
    headers = {
        "User-Agent": user_agent,
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    url = BING_RSS_ENDPOINT.format(query=quote_plus(query))
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()

    root = ET.fromstring(response.text)
    results: list[JobCandidate] = []
    for item in root.findall(".//item"):
        title = clean_text(item.findtext("title") or "")
        target_url = clean_text(item.findtext("link") or "")
        snippet = clean_text(item.findtext("description") or "")
        if not title or not target_url:
            continue
        results.append(
            JobCandidate(
                title=title,
                company="待确认",
                city="待确认",
                url=normalize_bing_url(target_url),
                source=infer_source(target_url),
                snippet=snippet,
            )
        )
    return results


def fetch_duckduckgo_results(
    query: str,
    *,
    timeout: int,
    user_agent: str,
) -> list[JobCandidate]:
    headers = {
        "User-Agent": user_agent,
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    url = DUCKDUCKGO_ENDPOINT.format(query=quote_plus(query))
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    results: list[JobCandidate] = []
    for item in soup.select(".result"):
        link = item.select_one(".result__a")
        if not link or not link.get("href"):
            continue
        title = clean_text(link.get_text(" "))
        snippet_node = item.select_one(".result__snippet")
        snippet = clean_text(snippet_node.get_text(" ") if snippet_node else "")
        target_url = normalize_duckduckgo_url(link["href"])
        results.append(
            JobCandidate(
                title=title,
                company="待确认",
                city="待确认",
                url=target_url,
                source=infer_source(target_url),
                snippet=snippet,
            )
        )
    return results


def normalize_duckduckgo_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc.endswith("duckduckgo.com") and parsed.path == "/l/":
        qs = parse_qs(parsed.query)
        if "uddg" in qs and qs["uddg"]:
            return unquote(qs["uddg"][0])
    return url


def fetch_page_text(url: str, *, timeout: int, user_agent: str) -> str:
    headers = {
        "User-Agent": user_agent,
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    if "text" not in content_type and "html" not in content_type:
        return ""
    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return clean_text(soup.get_text(" "))
