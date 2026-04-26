import re


_CURRENCY_CHARS = {"₹", "$", "€", "£", ","}
_CUISINE_SPLIT_RE = re.compile(r"[,/|]+")


def normalize_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def normalize_location(value: object) -> str:
    text = normalize_text(value)
    return " ".join(text.split())


def normalize_cuisines(value: object) -> list[str]:
    text = normalize_text(value)
    if not text:
        return []
    chunks = [part.strip() for part in _CUISINE_SPLIT_RE.split(text)]
    return [chunk for chunk in chunks if chunk]


def normalize_rating(value: object) -> float | None:
    text = normalize_text(value).lower()
    if not text or text in {"na", "n/a", "new", "-", "--"}:
        return None

    filtered = "".join(ch for ch in text if ch.isdigit() or ch in {".", "/"})
    if "/" in filtered:
        parts = filtered.split("/", maxsplit=1)
        if len(parts) == 2 and parts[0] and parts[1]:
            try:
                base = float(parts[1])
                raw = float(parts[0])
                if base > 0:
                    return round((raw / base) * 5.0, 2)
            except ValueError:
                return None
        return None

    try:
        parsed = float(filtered)
    except ValueError:
        return None

    if parsed < 0:
        return None
    # Clamp to standard 0-5 rating scale.
    return min(parsed, 5.0)


def normalize_cost(value: object) -> float | None:
    text = normalize_text(value).lower()
    if not text or text in {"na", "n/a", "-", "--"}:
        return None

    cleaned = text
    for symbol in _CURRENCY_CHARS:
        cleaned = cleaned.replace(symbol, "")
    cleaned = cleaned.replace("for two", "").strip()
    cleaned = "".join(ch for ch in cleaned if ch.isdigit() or ch == ".")
    if not cleaned:
        return None

    try:
        parsed = float(cleaned)
    except ValueError:
        return None
    if parsed < 0:
        return None
    return parsed
