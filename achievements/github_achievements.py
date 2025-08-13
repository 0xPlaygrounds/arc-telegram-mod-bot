import json
import os
from datetime import datetime, timezone

GITHUB_METRICS_FILE = "data/metrics/daily/github_metrics.json"
GITHUB_ACHIEVEMENTS_FILE = "data/achievements/github_achievements.json"

def load_json_file(filepath):
    if not os.path.exists(filepath):
        return {}
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_json_file(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

def get_latest_metrics_entry(metrics):
    if not metrics.get("entries"):
        return None
    return sorted(metrics["entries"], key=lambda e: e["timestamp"], reverse=True)[0]

def detect_release_version_change(metrics):
    entries = metrics.get("entries", [])
    if len(entries) < 2:
        return False, None
    latest = sorted(entries, key=lambda e: e["timestamp"], reverse=True)[0]
    previous = sorted(entries, key=lambda e: e["timestamp"], reverse=True)[1]
    if latest["release_version"] != previous["release_version"]:
        return True, latest["release_version"]
    return False, None

def check_star_fork_milestones(latest_entry, achievements):
    milestones = []
    star_step = 1000
    fork_step = 100
    last_star = achievements.get("last_star_milestone", 0)
    last_fork = achievements.get("last_fork_milestone", 0)
    stars = latest_entry.get("stars", 0)
    forks = latest_entry.get("forks", 0)

    current_star = (stars // star_step) * star_step
    current_fork = (forks // fork_step) * fork_step

    if current_star > last_star:
        milestones.append(f"🎉 Github Star milestone reached: {current_star} stars!")
        achievements["last_star_milestone"] = current_star

    if current_fork > last_fork:
        milestones.append(f"🎉 Github Fork milestone reached: {current_fork} forks!")
        achievements["last_fork_milestone"] = current_fork

    return milestones, achievements

def check_github_achievements():
    metrics = load_json_file(GITHUB_METRICS_FILE)
    achievements = load_json_file(GITHUB_ACHIEVEMENTS_FILE)

    if not achievements:
        achievements = {
            "dataset_name": "github_achievements",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "entries": [],
            "last_star_milestone": 0,
            "last_fork_milestone": 0,
            "last_release_version": None
        }

    latest_entry = get_latest_metrics_entry(metrics)
    if not latest_entry:
        print("No metrics data found.")
        return []

    new_achievements = []

    release_changed, new_version = detect_release_version_change(metrics)
    if release_changed and new_version != achievements.get("last_release_version"):
        msg = f"🎉 New rig-core version detected: {new_version}!"
        new_achievements.append(msg)
        achievements["last_release_version"] = new_version

    star_fork_msgs, achievements = check_star_fork_milestones(latest_entry, achievements)
    new_achievements.extend(star_fork_msgs)

    if new_achievements:
        achievement_entry = {
            "id": latest_entry["id"],
            "timestamp": latest_entry["timestamp"],
            "messages": new_achievements
        }
        achievements["entries"].append(achievement_entry)
        save_json_file(GITHUB_ACHIEVEMENTS_FILE, achievements)

    return new_achievements

if __name__ == "__main__":
    check_github_achievements()
