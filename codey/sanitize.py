# sanitize_llm.py

import unicodedata
import re

def sanitize_string(s: str, max_length: int = 100_000) -> str:
    """
    Strip out unsafe/control Unicode categories (except newline/tab),
    collapse repeated whitespace, and truncate to max_length.
    """
    # 1. remove control characters (C*), except \n and \t
    cleaned = []
    for ch in s:
        cat = unicodedata.category(ch)
        if cat.startswith("C") and ch not in ("\n", "\t"):
            continue
        cleaned.append(ch)
    cleaned = "".join(cleaned)

    # 2. collapse any runs of whitespace to a single space (optional)
    cleaned = re.sub(r"[ \t\f\v]{2,}", " ", cleaned)

    # 3. enforce length limit
    if len(cleaned) > max_length:
        return cleaned[:max_length]
    return cleaned


def sanitize_payload(obj, *, max_length: int = 100_000):
    """
    Recursively walk a dict/list/str structure and sanitize every string.
    Other types are left untouched.
    """
    if isinstance(obj, str):
        return sanitize_string(obj, max_length)
    elif isinstance(obj, dict):
        return {k: sanitize_payload(v, max_length=max_length) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_payload(v, max_length=max_length) for v in obj]
    else:
        return obj
