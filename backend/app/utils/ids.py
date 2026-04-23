from __future__ import annotations

from datetime import datetime
from secrets import token_hex


def new_run_id() -> str:
    return f"run_{datetime.utcnow():%Y%m%d%H%M%S}_{token_hex(4)}"
