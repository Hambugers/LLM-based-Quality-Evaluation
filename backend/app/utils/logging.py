from __future__ import annotations

from app.utils.time import utc_now_iso


def make_log(level: str, message: str) -> dict[str, str]:
    return {
        "time": utc_now_iso(),
        "level": level,
        "message": message,
    }
