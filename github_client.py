import os
import json
import logging
from datetime import datetime, timezone
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

def fetch_github_data(url: str, token: str | None = None) -> list | dict | None:
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Resume-Screening-App")
    if token:
        req.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        logger.warning(f"GitHub API returned HTTP {e.code} for {url}: {e.reason}")
    except Exception as e:
        logger.warning(f"Failed to connect to GitHub API for {url}: {e}")
    return None

def enrich_github_profile(username: str | None) -> dict:
 
    if not username:
        return {
            "github_score": 0,
            "github_summary": "No GitHub profile provided."
        }

    token = os.getenv("GITHUB_TOKEN")
    
    repos_url = f"https://api.github.com/users/{username}/repos?sort=updated&per_page=10"
    repos = fetch_github_data(repos_url, token)

    events_url = f"https://api.github.com/users/{username}/events/public?per_page=10"
    events = fetch_github_data(events_url, token)

    if repos is None and events is None:
        return {
            "github_score": 0,
            "github_summary": "GitHub enrichment skipped: Profile not found or rate limit reached."
        }

    activity_score = 0
    repo_score = 0
    now = datetime.now(timezone.utc)

    if isinstance(events, list) and len(events) > 0:
        latest_event_time_str = events[0].get("created_at")
        if latest_event_time_str:
            latest_date = datetime.fromisoformat(latest_event_time_str.replace("Z", "+00:00"))
            days_since_active = (now - latest_date).days

            if days_since_active <= 30:
                activity_score = 5
            elif days_since_active <= 90:
                activity_score = 3
            else:
                activity_score = 1

    if isinstance(repos, list):
        public_repo_count = len(repos)
        has_python_repo = any(
            (repo.get("language") or "").lower() == "python"
            for repo in repos
        )

        if public_repo_count >= 5 and has_python_repo:
            repo_score = 5
        elif public_repo_count >= 1 and has_python_repo:
            repo_score = 4
        elif public_repo_count >= 1:
            repo_score = 2

    total_github_score = min(activity_score + repo_score, 10)

    summary = (
        f"Active within last 90 days with {len(repos) if isinstance(repos, list) else 0} "
        f"public repositories evaluated (Python repos identified)."
        if total_github_score >= 5
        else "Limited or older public GitHub activity found."
    )

    return {
        "github_score": total_github_score,
        "github_summary": summary
    }