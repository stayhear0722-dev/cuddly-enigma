from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

import requests
from dotenv import load_dotenv

from .profile import analyze_resume
from .resume_extract import extract_resume_text


DEFAULT_REPOSITORY = "stayhear0722-dev/cuddly-enigma"
DEFAULT_WORKFLOW = "job-digest.yml"
DEFAULT_REF = "main"
MAX_WORKFLOW_INPUT_CHARS = 60000


def find_sensitive_hints(text: str) -> list[str]:
    hints: list[str] = []
    if re.search(r"1[3-9]\d{9}", text):
        hints.append("手机号")
    if re.search(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", text):
        hints.append("邮箱")
    if re.search(r"\b\d{17}[\dXx]\b", text):
        hints.append("身份证号")
    if any(word in text for word in ("家庭住址", "身份证", "户籍", "详细地址")):
        hints.append("敏感身份/地址字段")
    return sorted(set(hints))


def build_payload(resume_text: str, ref: str) -> dict:
    text = resume_text.strip()
    if len(text) > MAX_WORKFLOW_INPUT_CHARS:
        text = text[:MAX_WORKFLOW_INPUT_CHARS]
    return {
        "ref": ref,
        "inputs": {
            "resume_text": text,
        },
    }


def dispatch_workflow(
    *,
    token: str,
    repository: str,
    workflow: str,
    ref: str,
    resume_text: str,
) -> None:
    url = f"https://api.github.com/repos/{repository}/actions/workflows/{workflow}/dispatches"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "career-ops-lite",
    }
    response = requests.post(url, headers=headers, json=build_payload(resume_text, ref), timeout=30)
    if response.status_code != 204:
        raise RuntimeError(
            f"Failed to dispatch workflow: HTTP {response.status_code} {response.text}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract resume text from a local file and trigger the GitHub Actions job digest."
    )
    parser.add_argument("--file", "-f", required=True, help="Path to resume file (.pdf, .docx, .txt)")
    parser.add_argument("--dry-run", action="store_true", help="Extract and summarize without triggering GitHub Actions")
    parser.add_argument("--repository", default=None, help="GitHub repository in owner/name form")
    parser.add_argument("--workflow", default=None, help="Workflow file name or ID")
    parser.add_argument("--ref", default=None, help="Git ref to run workflow from")
    args = parser.parse_args()

    load_dotenv()
    repository = args.repository or os.environ.get("GITHUB_REPOSITORY", DEFAULT_REPOSITORY)
    workflow = args.workflow or os.environ.get("GITHUB_WORKFLOW", DEFAULT_WORKFLOW)
    ref = args.ref or os.environ.get("GITHUB_REF", DEFAULT_REF)

    resume_text = extract_resume_text(Path(args.file))
    if not resume_text:
        raise RuntimeError("No text could be extracted from the resume file.")

    profile = analyze_resume(resume_text)
    sensitive_hints = find_sensitive_hints(resume_text)

    print(f"[ok] extracted characters: {len(resume_text)}")
    print(f"[ok] resume profile: {profile.summary()}")
    if sensitive_hints:
        print(f"[warn] possible sensitive fields detected: {', '.join(sensitive_hints)}")
        print("[warn] They will be sent to GitHub Actions input for this run. Remove them from the file if needed.")
    if len(resume_text) > MAX_WORKFLOW_INPUT_CHARS:
        print(f"[warn] resume text truncated to {MAX_WORKFLOW_INPUT_CHARS} characters for workflow input.")

    if args.dry_run:
        print("[ok] dry run: skipped GitHub Actions dispatch")
        return

    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Missing GITHUB_TOKEN. Create a local .env from .env.example and set GITHUB_TOKEN.")

    dispatch_workflow(
        token=token,
        repository=repository,
        workflow=workflow,
        ref=ref,
        resume_text=resume_text,
    )
    print(f"[ok] dispatched workflow: {repository}/{workflow} on {ref}")


if __name__ == "__main__":
    main()
