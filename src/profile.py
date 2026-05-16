from __future__ import annotations

import os
import re
from dataclasses import dataclass, field


DEFAULT_PROFILE_TEXT = """
2027届学生，求职方向为数据分析、数据运营、商业分析、数据产品、AI数据相关实习。
具备 Excel、统计分析、数据清洗、结构化数据处理、机器学习建模等能力。
"""


KNOWN_CITIES = [
    "北京",
    "上海",
    "广州",
    "深圳",
    "杭州",
    "厦门",
    "南京",
    "苏州",
    "成都",
    "武汉",
    "西安",
]

ROLE_KEYWORDS = [
    "数据分析",
    "数据运营",
    "商业分析",
    "数据产品",
    "数据科学",
    "AI数据",
    "模型评估",
    "算法数据",
    "数据标注",
    "质检",
    "用户研究",
    "产品运营",
]

SKILL_KEYWORDS = [
    "Excel",
    "SQL",
    "Python",
    "Tableau",
    "Power BI",
    "SPSS",
    "统计",
    "数据清洗",
    "ETL",
    "特征工程",
    "机器学习",
    "随机森林",
    "XGBoost",
    "LSTM",
    "K-means",
    "建模",
    "预测",
    "可视化",
    "报表",
    "指标",
]


@dataclass
class ResumeProfile:
    raw_text: str
    graduation_keywords: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    role_keywords: list[str] = field(default_factory=list)
    skill_keywords: list[str] = field(default_factory=list)

    def summary(self) -> str:
        roles = "、".join(self.role_keywords[:5]) or "数据类实习"
        skills = "、".join(self.skill_keywords[:6]) or "数据处理、分析能力"
        cities = "、".join(self.locations) or "配置中的目标城市"
        grads = "、".join(self.graduation_keywords[:2]) or "实习生"
        return f"{grads}；目标城市：{cities}；岗位方向：{roles}；技能关键词：{skills}"


def load_resume_text() -> str:
    text = os.environ.get("RESUME_TEXT", "").strip()
    return text or DEFAULT_PROFILE_TEXT


def analyze_resume(text: str | None = None) -> ResumeProfile:
    raw = (text or load_resume_text()).strip()
    profile = ResumeProfile(raw_text=raw)

    years = infer_graduation_years(raw)
    for year in years:
        profile.graduation_keywords.extend([year, f"{year}届", f"{year[-2:]}届"])
    if "应届" in raw:
        profile.graduation_keywords.append("应届")
    if "实习" in raw:
        profile.graduation_keywords.append("实习生")
    if not profile.graduation_keywords:
        profile.graduation_keywords = ["实习生", "在校生"]

    profile.locations = infer_target_locations(raw)
    profile.role_keywords = [role for role in ROLE_KEYWORDS if role.lower() in raw.lower()]
    profile.skill_keywords = [skill for skill in SKILL_KEYWORDS if skill.lower() in raw.lower()]

    if not profile.role_keywords:
        profile.role_keywords = ["数据分析", "数据运营", "商业分析"]
    if not profile.skill_keywords:
        profile.skill_keywords = ["Excel", "统计", "数据清洗", "建模"]
    return profile


def infer_graduation_years(text: str) -> list[str]:
    explicit_years = set(re.findall(r"(20(?:2[5-9]|3[0-5]))\s*届", text))
    short_years = set(re.findall(r"(?<!\d)(2[5-9]|3[0-5])\s*届", text))
    for short in short_years:
        explicit_years.add(f"20{short}")
    if explicit_years:
        return sorted(explicit_years, reverse=True)

    education_matches = re.findall(
        r"(?:教育经历|学校|大学|本科|硕士|博士|专业)[\s\S]{0,80}?(20(?:2[5-9]|3[0-5]))(?:\.\d{1,2})?",
        text,
    )
    if education_matches:
        return [max(education_matches)]

    all_years = re.findall(r"20(?:2[5-9]|3[0-5])", text)
    if all_years:
        return [max(all_years)]
    return []


def infer_target_locations(text: str) -> list[str]:
    windows = []
    for marker in ("意向城市", "目标城市", "期望城市", "求职城市", "工作地点", "意向地点"):
        index = text.find(marker)
        if index >= 0:
            windows.append(text[index : index + 80])
    if not windows:
        return []
    joined = "\n".join(windows)
    return [city for city in KNOWN_CITIES if city in joined]


def apply_resume_profile(config: dict, profile: ResumeProfile) -> dict:
    configured_locations = config.get("locations", [])
    if profile.locations:
        config["locations"] = profile.locations
    elif configured_locations:
        config["locations"] = configured_locations

    role_keywords = []
    for role in profile.role_keywords + config.get("role_keywords", []):
        role_keywords.append(role)
        if "实习" not in role:
            role_keywords.append(f"{role}实习")
    config["role_keywords"] = dedupe(role_keywords)

    config["graduation_keywords"] = dedupe(
        profile.graduation_keywords + config.get("graduation_keywords", [])
    )
    config["profile_analysis"] = {
        "summary": profile.summary(),
        "skill_keywords": profile.skill_keywords,
        "role_keywords": profile.role_keywords,
    }
    return config


def dedupe(values: list[str]) -> list[str]:
    result = []
    seen = set()
    for value in values:
        clean = value.strip()
        if clean and clean not in seen:
            seen.add(clean)
            result.append(clean)
    return result
