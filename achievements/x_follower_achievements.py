import os
import json
from datetime import datetime, timezone

X_FOLLOWER_METRICS_FILE = "data/metrics/daily/x_follower_metrics.json"
X_FOLLOWER_ACHIEVEMENTS_FILE = "data/achievements/x_follower_achievements.json"

def load_json_file(filepath):
    if not os.path.exists(filepath):
        return {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data
    except json.JSONDecodeError as e:
        return {}

def save_json_file(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def get_latest_metrics_entry(metrics):
    if not metrics.get("entries"):
        return None
    latest = sorted(metrics["entries"], key=lambda e: e["timestamp"], reverse=True)[0]
    return latest

def check_follower_count_milestones(latest_entry, achievements):
    milestones = []
    follower_milestone_step = 1000  # milestone every 1000 followers

    last_follower_milestone = achievements.get("last_follower_milestone", 0)
    follower_count = latest_entry.get("followers", 0)

    current_milestone = (follower_count // follower_milestone_step) * follower_milestone_step

    if current_milestone > last_follower_milestone:
        milestones.append(f"🎉 X Follower milestone reached: {current_milestone} followers!")
        achievements["last_follower_milestone"] = current_milestone

    return milestones, achievements

def check_x_follower_achievements():
    metrics = load_json_file(X_FOLLOWER_METRICS_FILE)
    achievements = load_json_file(X_FOLLOWER_ACHIEVEMENTS_FILE)

    if not achievements:
        achievements = {
            "dataset_name": "x_follower_achievements",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "entries": [],
            "last_follower_milestone": 0
        }

    latest_entry = get_latest_metrics_entry(metrics)
    if not latest_entry:
        return []

    new_achievements = []

    milestone_msgs, achievements = check_follower_count_milestones(latest_entry, achievements)
    new_achievements.extend(milestone_msgs)

    if new_achievements:
        achievement_entry = {
            "id": latest_entry.get("id", ""),
            "timestamp": latest_entry.get("timestamp", ""),
            "messages": new_achievements
        }
        achievements["entries"].append(achievement_entry)
        save_json_file(X_FOLLOWER_ACHIEVEMENTS_FILE, achievements)

    return new_achievements

if __name__ == "__main__":
    check_x_follower_achievements()
