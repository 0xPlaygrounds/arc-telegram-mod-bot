import re
from utils.regex_patterns import URL_PATTERN, X_TWITTER_PATTERN

def contains_non_x_links(text: str) -> bool:
    urls = URL_PATTERN.findall(text)
    for url in urls:
        if not X_TWITTER_PATTERN.match(url):
            return True
    return False
