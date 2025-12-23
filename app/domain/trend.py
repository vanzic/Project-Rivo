import re
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Trend:
    trend_key: str
    source: str
    title: str
    published_at: str = None

def normalize_text(text: str) -> str:
    """
    Normalizes text for trend aggregation.
    Rules:
    - Lowercase
    - Remove special chars (keep alphanumeric and spaces)
    - Collapse whitespace
    """
    if not text:
        return ""
    
    # Lowercase
    text = text.lower()
    
    # Remove things inside brackets [] (often IDs in our strings)
    text = re.sub(r'\[.*?\]', '', text)
    
    # Remove special chars (keep alphanumeric and spaces)
    text = re.sub(r'[^a-z0-9\s]', '', text)
    
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def parse_trend_string(raw_string: str) -> str:
    """
    Parses the raw trend string from sources to extract the title part
    before normalization.
    Format is usually "Title [ID] | Source" or similar.
    We generally want the part before the first '[' or '|'.
    """
    # Split by '[' or '|' and take the first part
    title_part = re.split(r'[\[\|]', raw_string)[0]
    return title_part.strip()
