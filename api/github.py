import os
import json
import requests
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

GITHUB_METRICS_FILE = "data/metrics/daily/github_metrics.json"

def get_github_stats():
    """Fetches GitHub repository statistics and appends to metrics file."""
    repo = os.getenv("REPO")
    if not repo:
        return "❌ REPO not set in environment."

    # Fetch general repo info
    url = f"https://api.github.com/repos/{repo}"
    response = requests.get(url)
    if response.status_code != 200:
        return "❌ Error fetching GitHub stats."

    data = response.json()
    stars = data.get("stargazers_count", 0)
    forks = data.get("forks_count", 0)

    # Fetch releases and filter for rig-core
    releases_url = f"https://api.github.com/repos/{repo}/releases"
    releases_response = requests.get(releases_url)
    if releases_response.status_code != 200:
        return "❌ Error fetching releases."

    releases = releases_response.json()
    rig_core_versions = [
        release.get("tag_name", "N/A")
        for release in releases
        if "rig-core" in release.get("tag_name", "")
    ]

    if not rig_core_versions:
        release_version = "N/A"
    else:
        rig_core_versions.sort(reverse=True)
        release_version = rig_core_versions[0]

    # Build metrics entry
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = {
        "id": str(uuid.uuid4()),
        "timestamp": timestamp,
        "stars": stars,
        "forks": forks,
        "release_version": release_version
    }

    save_github_metrics(entry)

    return (
        f"⭐️ Github Stars  >>  {stars:,}\n"
        f"🍴 Github Forks  >>  {forks:,}\n"
        f"🔖 Rig Version   >>  {release_version}"
    )

def save_github_metrics(new_entry):
    """Appends the new GitHub stats entry to the metrics file."""
    if os.path.exists(GITHUB_METRICS_FILE):
        with open(GITHUB_METRICS_FILE, "r") as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                existing_data = {}
    else:
        existing_data = {}

    if not existing_data:
        existing_data = {
            "dataset_name": "github_metrics",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "entries": []
        }

    existing_data["entries"].append(new_entry)

    with open(GITHUB_METRICS_FILE, "w") as f:
        json.dump(existing_data, f, indent=2)