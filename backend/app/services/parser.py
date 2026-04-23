from __future__ import annotations

import json
import re
from typing import Any


JSON_BLOCK_PATTERN = re.compile(r"```json\s*(?P<body>\{.*?\})\s*```", re.DOTALL)
JSON_OBJECT_PATTERN = re.compile(r"(?P<body>\{.*\})", re.DOTALL)


def parse_model_json(raw: str | None) -> dict[str, Any] | None:
    if not raw:
        return None

    candidates = [raw.strip()]
    fenced_match = JSON_BLOCK_PATTERN.search(raw)
    if fenced_match:
        candidates.insert(0, fenced_match.group("body"))

    object_match = JSON_OBJECT_PATTERN.search(raw)
    if object_match:
        candidates.append(object_match.group("body"))

    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue

    return None
