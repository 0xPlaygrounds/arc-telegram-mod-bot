import json

def load_json(file_path: str) -> dict:
    """Load a JSON file and return as dict."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_phrases(file_path: str) -> list:
    """Load a text file (one phrase per line) into a list, lowercased."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return [line.strip().lower() for line in f if line.strip()]
