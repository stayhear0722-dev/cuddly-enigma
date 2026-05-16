from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from .config import ROOT, load_config
from .emailer import send_email
from .history import append_history, load_seen_urls
from .profile import analyze_resume, apply_resume_profile
from .rank import score_job
from .report import render_markdown, save_report
from .search import fetch_page_text, fetch_search_results
from .sources import fetch_shixiseng_jobs


NOISE_DOMAINS = (
    "baike.baidu.com",
    "wikipedia.org",
    "zhihu.com",
    "hangzhou.gov.cn",
    "gotravellingworld.com",
)


def build_queries(config: dict) -> list[str]:
    queries = []
    for city in config["locations"]:
        for template in config["search_queries"]:
            queries.append(template.format(city=city))
    return queries


def is_candidate_relevant(candidate, config: dict) -> bool:
    text = f"{candidate.title} {candidate.snippet} {candidate.url}"
    if any(domain in candidate.url for domain in NOISE_DOMAINS):
        return False
    if any(city in text for city in config["locations"]) and (
        any(keyword in text for keyword in config["role_keywords"])
        or "实习" in text
        or "校招" in text
        or "招聘" in text
    ):
        return True
    return any(source in candidate.source for source in ("牛客", "实习僧", "智联招聘", "猎聘", "前程无忧", "BOSS直聘"))


def collect_jobs(config: dict, history_path: Path) -> list:
    timeout = int(config["search"]["timeout_seconds"])
    user_agent = config["search"]["user_agent"]
    max_candidates = int(config["search"]["max_candidates"])
    max_detail_pages = int(config["search"].get("max_detail_pages", 20))
    limit = int(config["search"]["limit"])
    seen_urls = load_seen_urls(history_path)

    candidates = []
    candidate_urls = set(seen_urls)
    for result in fetch_shixiseng_jobs(config):
        key = result.key()
        if key and key not in candidate_urls and is_candidate_relevant(result, config):
            candidate_urls.add(key)
            candidates.append(result)
        if len(candidates) >= max_candidates:
            break

    search_errors = 0
    for query in build_queries(config):
        if len(candidates) >= max_candidates:
            break
        try:
            results = fetch_search_results(
                query,
                timeout=timeout,
                user_agent=user_agent,
            )
        except Exception as exc:
            search_errors += 1
            print(f"[warn] search failed: {query}: {exc}")
            continue

        for result in results:
            key = result.key()
            if not key or key in candidate_urls:
                continue
            if not is_candidate_relevant(result, config):
                continue
            candidate_urls.add(key)
            candidates.append(result)
            if len(candidates) >= max_candidates:
                break
        if len(candidates) >= max_candidates:
            break

    print(f"[info] candidates collected: {len(candidates)}; search errors: {search_errors}")
    prelim = []
    for candidate in candidates:
        scored = score_job(candidate, "", config)
        if scored:
            prelim.append(scored)

    prelim.sort(key=lambda item: item.score, reverse=True)
    print(f"[info] preliminary matches: {len(prelim)}")

    ranked = []
    detail_errors = 0
    for candidate in prelim[:max_detail_pages]:
        try:
            page_text = fetch_page_text(
                candidate.url,
                timeout=timeout,
                user_agent=user_agent,
            )
        except Exception as exc:
            detail_errors += 1
            page_text = ""
            candidate.risks.append(f"页面详情抓取失败：{exc}")

        scored = score_job(candidate, page_text, config)
        if scored:
            ranked.append(scored)

    if len(ranked) < limit:
        seen_ranked = {job.key() for job in ranked}
        for candidate in prelim:
            if candidate.key() not in seen_ranked:
                ranked.append(candidate)
            if len(ranked) >= limit:
                break

    print(f"[info] matched jobs: {len(ranked)}; detail fetch errors: {detail_errors}")
    ranked.sort(key=lambda item: item.score, reverse=True)
    return ranked[:limit]


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan domestic internship roles and email a digest.")
    parser.add_argument("--config", default="config.yml", help="Path to config.yml")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing history or sending email")
    parser.add_argument("--no-email", action="store_true", help="Generate report without sending email")
    parser.add_argument("--limit", type=int, default=None, help="Override digest size")
    args = parser.parse_args()

    config = load_config(args.config)
    resume_profile = analyze_resume()
    config = apply_resume_profile(config, resume_profile)
    if args.limit is not None:
        config["search"]["limit"] = args.limit

    print(f"[info] resume profile: {resume_profile.summary()}")

    history_path = ROOT / "data" / "history.csv"
    report_dir = ROOT / "reports"
    jobs = collect_jobs(config, history_path)
    markdown = render_markdown(jobs, config)
    report_path = save_report(markdown, report_dir)

    print(markdown)
    print(f"\n[ok] report saved: {report_path}")

    if args.dry_run:
        print("[ok] dry run: skipped history update and email")
        return

    append_history(history_path, jobs)

    if args.no_email:
        print("[ok] email skipped by --no-email")
        return

    subject = f"{config['email']['subject_prefix']} - {date.today().isoformat()}"
    send_email(subject, markdown, config)
    print("[ok] email sent")


if __name__ == "__main__":
    main()
