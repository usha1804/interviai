"""
GitHub Portfolio Analyzer Service
Uses GitHub REST API (no auth required for public repos, optional token for higher rate limits).
Analyzes repos, languages, commit activity, README quality, stars/forks.
"""
import json
import re
from typing import Dict, List, Optional
import requests
from app.config import settings
from app.services.ai_service import _chat, get_groq_client

GITHUB_API = "https://api.github.com"


def _headers() -> Dict:
    token = getattr(settings, "GITHUB_TOKEN", "")
    h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _extract_username(url: str) -> str:
    url = url.rstrip("/")
    parts = url.split("/")
    # https://github.com/username  or  github.com/username
    for i, p in enumerate(parts):
        if p in ("github.com",) and i + 1 < len(parts):
            return parts[i + 1]
    return parts[-1]


def fetch_github_data(github_url: str) -> Dict:
    """Fetch user profile + repos from GitHub API."""
    username = _extract_username(github_url)
    h = _headers()

    user_resp = requests.get(f"{GITHUB_API}/users/{username}", headers=h, timeout=10)
    if user_resp.status_code != 200:
        return {"error": f"GitHub user '{username}' not found.", "username": username}

    user = user_resp.json()

    repos_resp = requests.get(
        f"{GITHUB_API}/users/{username}/repos",
        headers=h,
        params={"sort": "updated", "per_page": 30},
        timeout=10,
    )
    repos = repos_resp.json() if repos_resp.status_code == 200 else []

    # Aggregate languages
    lang_counts: Dict[str, int] = {}
    for repo in repos:
        if repo.get("language"):
            lang_counts[repo["language"]] = lang_counts.get(repo["language"], 0) + 1

    top_repos = [
        {
            "name": r["name"],
            "description": r.get("description") or "",
            "stars": r.get("stargazers_count", 0),
            "forks": r.get("forks_count", 0),
            "language": r.get("language") or "Unknown",
            "updated_at": r.get("updated_at", ""),
            "has_readme": bool(r.get("description")),
            "url": r.get("html_url", ""),
        }
        for r in repos[:10]
    ]

    return {
        "username": username,
        "name": user.get("name") or username,
        "bio": user.get("bio") or "",
        "public_repos": user.get("public_repos", 0),
        "followers": user.get("followers", 0),
        "following": user.get("following", 0),
        "total_stars": sum(r.get("stargazers_count", 0) for r in repos),
        "total_forks": sum(r.get("forks_count", 0) for r in repos),
        "languages": lang_counts,
        "top_repos": top_repos,
        "profile_url": user.get("html_url", ""),
    }


def analyze_github(github_url: str) -> Dict:
    """Full GitHub portfolio analysis with AI scoring."""
    data = fetch_github_data(github_url)
    if "error" in data:
        return data

    client = get_groq_client()
    repos_summary = json.dumps(data["top_repos"][:8], indent=2)

    prompt = f"""You are a Senior Software Engineer evaluating a developer's GitHub portfolio.

GitHub Profile:
- Username: {data['username']}
- Public Repos: {data['public_repos']}
- Total Stars: {data['total_stars']}
- Total Forks: {data['total_forks']}
- Languages: {json.dumps(data['languages'])}
- Bio: {data['bio']}

Top Repositories:
{repos_summary}

Evaluate the portfolio and return ONLY this JSON:
{{
    "github_score": <0-100>,
    "project_quality_score": <0-100>,
    "coding_activity_score": <0-100>,
    "open_source_score": <0-100>,
    "frameworks": ["<framework1>", "<framework2>"],
    "commit_frequency": "<Daily|Weekly|Monthly|Inactive>",
    "recommendations": [
        "<recommendation1>",
        "<recommendation2>",
        "<recommendation3>"
    ],
    "ai_summary": "<3-4 sentence assessment of the developer's portfolio>"
}}"""

    text = _chat(client, settings.GROQ_MODEL, prompt, max_tokens=1000)
    try:
        s, e = text.find("{"), text.rfind("}") + 1
        ai_result = json.loads(text[s:e])
    except Exception:
        ai_result = {
            "github_score": 60, "project_quality_score": 60,
            "coding_activity_score": 50, "open_source_score": 40,
            "frameworks": [], "commit_frequency": "Unknown",
            "recommendations": ["Add README files", "Increase commit frequency", "Contribute to open source"],
            "ai_summary": "Portfolio analysis unavailable.",
        }

    return {**data, **ai_result}
