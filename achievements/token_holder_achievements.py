import os
import json
from datetime import datetime, timezone

TOKEN_HOLDER_METRICS_FILE = "data/metrics/daily/token_holder_metrics.json"
TOKEN_HOLDER_ACHIEVEMENTS_FILE = "data/achievements/token_holder_achievements.json"

def load_json_file(filepath):
    if not os.path.exists(filepath):
        return {}
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
            return data
    except json.JSONDecodeError as e:
        return {}

def save_json_file(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

def get_latest_metrics_entry(metrics):
    if not metrics.get("entries"):
        return None
    latest = sorted(metrics["entries"], key=lambda e: e["timestamp"], reverse=True)[0]
    return latest

def check_holder_count_milestones(latest_entry, achievements):
    milestones = []
    holder_milestone_step = 1000  # Milestone every 1000 holders

    last_holder_milestone = achievements.get("last_holder_milestone", 0)
    holder_count = latest_entry.get("holder_count", 0)

    current_milestone = (holder_count // holder_milestone_step) * holder_milestone_step

    if current_milestone > last_holder_milestone:
        milestones.append(f"🎉 Token holder milestone reached: {current_milestone} holders!")
        achievements["last_holder_milestone"] = current_milestone

    return milestones, achievements

def check_token_holder_achievements():

    metrics = load_json_file(TOKEN_HOLDER_METRICS_FILE)
    achievements = load_json_file(TOKEN_HOLDER_ACHIEVEMENTS_FILE)

    if not achievements:
        achievements = {
            "dataset_name": "token_holder_achievements",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "entries": [],
            "last_holder_milestone": 0
        }

    latest_entry = get_latest_metrics_entry(metrics)
    if not latest_entry:
        return []

    new_achievements = []

    milestone_msgs, achievements = check_holder_count_milestones(latest_entry, achievements)
    new_achievements.extend(milestone_msgs)

    if new_achievements:
        achievement_entry = {
            "id": latest_entry.get("id", ""),
            "timestamp": latest_entry.get("timestamp", ""),
            "messages": new_achievements
        }
        achievements["entries"].append(achievement_entry)
        save_json_file(TOKEN_HOLDER_ACHIEVEMENTS_FILE, achievements)

    return new_achievements

if __name__ == "__main__":
    check_token_holder_achievements()
