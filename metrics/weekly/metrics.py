import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DAILY_DIR = PROJECT_ROOT / "data" / "metrics" / "daily"
WEEKLY_DIR = PROJECT_ROOT / "data" / "metrics" / "weekly"
FILTERS_DIR = PROJECT_ROOT / "filters"
FILTERS_DIR.mkdir(parents=True, exist_ok=True)

DATASETS = {
    "github_metrics": {
        "keys": ["stars", "forks"],
        "emojis": {"stars": "⭐️", "forks": "🍴"},
        "display_names": {"stars": "GitHub Stars", "forks": "GitHub Forks"},
    },
    "telegram_metrics": {
        "keys": ["member_count"],
        "emojis": {"member_count": "👥"},
        "display_names": {"member_count": "Telegram Members"},
    },
    "token_holder_metrics": {
        "keys": ["holder_count"],
        "emojis": {"holder_count": "💊"},
        "display_names": {"holder_count": "$ARC Holders"},
    },
    "x_follower_metrics": {
        "keys": ["followers"],
        "emojis": {"followers": "🐦"},
        "display_names": {"followers": "X Followers"},
    },
}

def load_json_file(path: Path):
    if not path.exists() or path.stat().st_size == 0:
        print(f"[!] File missing or empty: {path}")
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[!] Failed to load JSON {path}: {e}")
        return None

def save_json_file(path: Path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"[✓] Saved file: {path.name}")

def calculate_pct_change(current_val, previous_val):
    try:
        if previous_val is None or previous_val == 0:
            return 0.0
        return round(((current_val - previous_val) / previous_val) * 100, 2)
    except Exception:
        return 0.0

def save_last_weekly_metrics_message(message: str):
    data = {"last_weekly_metrics_message": message}
    metrics_path = FILTERS_DIR / "growth.json"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)  # ensure directory exists
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"[✓] Saved last weekly metrics message to {metrics_path}")

def format_number(n):
    return f"{n:,}"

def update_weekly_metrics():
    updated_any = False
    message_lines = []

    for dataset_name, info in DATASETS.items():
        keys = info["keys"]
        emojis = info["emojis"]
        display_names = info["display_names"]

        daily_file = DAILY_DIR / f"{dataset_name}.json"
        weekly_filename = dataset_name.replace("_metrics", "_weekly_metrics") + ".json"
        weekly_file = WEEKLY_DIR / weekly_filename

        daily_data = load_json_file(daily_file)
        if not daily_data or "entries" not in daily_data or not daily_data["entries"]:
            print(f"[!] No daily data found for {dataset_name}. Skipping.")
            continue

        latest_record = daily_data["entries"][-1]

        weekly_data = load_json_file(weekly_file) or {}

        previous = weekly_data.get("current")
        current = {key: latest_record.get(key, 0) or 0 for key in keys}

        if previous is None:
            previous = current.copy()

        change = {}
        for key in keys:
            cur_val = current.get(key, 0)
            prev_val = previous.get(key, 0)
            change[key] = calculate_pct_change(cur_val, prev_val)

        new_weekly_data = {
            "dataset_name": dataset_name.replace("_metrics", "_weekly_metrics"),
            "created_at": datetime.utcnow().isoformat() + "Z",
            "previous": previous,
            "current": current,
            "change": change,
        }

        save_json_file(weekly_file, new_weekly_data)
        updated_any = True

        # Format each metric line, then join with newlines between keys of this dataset
        for key in keys:
            emoji = emojis.get(key, "")
            display_name = display_names.get(key, key)
            current_val = format_number(current.get(key, 0))
            pct_change = f"{change[key]:+.2f}%"
            message_lines.append(f"{emoji} {display_name} >> {current_val} ({pct_change})")

        # Add a blank line between datasets
        message_lines.append("")

    if not updated_any:
        print("[!] No metrics data found or updated.")
        return False, ""

    full_message = "\n".join(message_lines)
    return True, full_message

def main():
    updated, message = update_weekly_metrics()
    if updated:
        save_last_weekly_metrics_message(message)

if __name__ == "__main__":
    main()
