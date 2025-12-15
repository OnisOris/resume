from __future__ import annotations

from typing import Iterable, List


def tags_to_text(tags: Iterable[str] | None) -> str | None:
    if not tags:
        return None
    cleaned = [t.strip() for t in tags if t and t.strip()]
    return ",".join(cleaned) if cleaned else None


def tags_from_text(text: str | None) -> List[str]:
    if not text:
        return []
    return [tag.strip() for tag in text.split(",") if tag.strip()]
