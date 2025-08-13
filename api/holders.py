import os
import json
import uuid
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

TOKEN_MINT_ADDRESS = os.getenv("TOKEN_ADDRESS")
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")

DATA_FILE = "data/metrics/daily/token_holder_metrics.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                if "entries" not in data:
                    data = {
                        "dataset_name": "token_holder_metrics",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "entries": []
                    }
                return data
        except json.JSONDecodeError:
            pass
    return {
        "dataset_name": "token_holder_metrics",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "entries": []
    }

def save_data(data):
    data["created_at"] = datetime.now(timezone.utc).isoformat()
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

import time

def fetch_token_holders(max_retries=5, backoff_factor=2):
    url = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"

    payload = {
        "jsonrpc": "2.0",
        "id": "get-holders",
        "method": "getTokenAccounts",
        "params": {
            "mint": TOKEN_MINT_ADDRESS,
            "limit": 1000,
            "options": {
                "showZeroBalance": False
            }
        }
    }

    headers = {"Content-Type": "application/json"}

    unique_holders = set()
    has_more = True
    cursor = None
    retries = 0

    while has_more:
        if cursor:
            payload["params"]["cursor"] = cursor
        else:
            payload["params"].pop("cursor", None)

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            data = response.json()

            if "error" in data:
                print(f"API Error: {data['error']['message']}")
                return 0

            result = data.get("result", {})
            accounts = result.get("token_accounts", [])

            for account in accounts:
                owner = account.get("owner")
                if owner:
                    unique_holders.add(owner)

            cursor = result.get("cursor")
            has_more = bool(cursor)

            retries = 0  # reset retries on successful response

        elif response.status_code == 429:
            retries += 1
            if retries > max_retries:
                print("Max retries reached due to rate limiting. Aborting.")
                return len(unique_holders)
            wait_time = backoff_factor ** retries
            print(f"Rate limited (429). Waiting {wait_time} seconds before retry {retries}...")
            time.sleep(wait_time)

        else:
            print(f"Error fetching data: HTTP {response.status_code}")
            has_more = False

    return len(unique_holders)

def log_holder_count(count):
    data = load_data()
    new_entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "holder_count": count
    }
    data["entries"].append(new_entry)
    save_data(data)

def get_token_stats():
    count = fetch_token_holders()
    log_holder_count(count)
    formatted_count = "{:,}".format(count)
    return f"💊 $ARC Holders  >>  {formatted_count}"
