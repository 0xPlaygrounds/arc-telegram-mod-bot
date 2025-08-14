import unicodedata
import re

def normalize_name(name: str) -> str:
    name = unicodedata.normalize("NFKD", name or "")
    name = ''.join(c for c in name if not unicodedata.combining(c))
    name = re.sub(r'[^a-zA-Z0-9_ ]+', '', name)
    name = name.lower()
    name = name.strip()
    name = re.sub(r'\s+', ' ', name)
    return name
