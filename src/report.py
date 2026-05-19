from __future__ import annotations

from datetime import date
from pathlib import Path

from .models import JobCandidate


def render_markdown(jobs: list[JobCandidate], config: dict) -> str:
    today = date.today().isoformat()
    lines = [
        f"# 27届实习岗位推荐 - {today}",
        "",
        f"简历画像：{config.get('profile_analysis', {}).get('summary', '未配置，使用默认画像')}",
        f"目标城市：{', '.join(config['locations'])}",
        f"岗位方向：{', '.join(config['role_keywords'][:5])}",
        "",
    ]
    if not jobs:
        lines.extend(
            [
                "本次没有找到符合条件的新岗位。",
                "",
                "建议下次扩大关键词，或加入更多公司官网招聘页；本项目不会用招聘平台链接凑数。",
            ]
        )
        return "\n".join(lines)

    if len(jobs) < int(config["search"]["limit"]):
        lines.extend(
            [
                f"本次只找到 {len(jobs)} 条较高匹配的新岗位，少于目标数量。",
                "",
            ]
        )

    for index, job in enumerate(jobs, 1):
        risks = "；".join(job.risks) if job.risks else "暂无明显风险"
        lines.extend(
            [
                f"## {index}. {job.title}",
                "",
                f"- 公司：{job.company}",
                f"- 城市：{job.city}",
                f"- 来源：{job.source}",
                f"- 匹配分：{job.score}/100",
                f"- 投递链接：{job.url}",
                f"- 公司介绍：{job.company_intro}",
                f"- 匹配理由：{job.match_reason}",
                f"- 风险提示：{risks}",
                "",
            ]
        )
    return "\n".join(lines)


def save_report(markdown: str, reports_dir: Path) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / f"{date.today().isoformat()}.md"
    path.write_text(markdown, encoding="utf-8")
    return path
