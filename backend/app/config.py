from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path


MODEL_PATTERN = re.compile(r'model\s*=\s*"(?P<model>[^"]+)"')
API_PATTERN = re.compile(r"API:(?P<api_key>\S+)")


@dataclass(slots=True)
class Settings:
    openrouter_api_key: str
    openrouter_base_url: str
    openrouter_text_model: str
    openrouter_vision_model: str
    openrouter_timeout_seconds: int
    openrouter_max_retries: int
    uploads_dir: Path
    sample_assets_dir: Path
    project_root: Path

    @classmethod
    def load(
        cls,
        env: dict[str, str] | None = None,
        model_file_path: Path | None = None,
        uploads_dir: Path | None = None,
        sample_assets_dir: Path | None = None,
        project_root: Path | None = None,
    ) -> "Settings":
        raw_env = dict(os.environ if env is None else env)
        defaults = parse_model_file(model_file_path)

        api_key = raw_env.get("OPENROUTER_API_KEY") or defaults.get("api_key")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY is required")

        text_model = (
            raw_env.get("OPENROUTER_TEXT_MODEL") or defaults.get("model") or "google/gemma-4-31b-it:free"
        )
        vision_model = raw_env.get("OPENROUTER_VISION_MODEL") or text_model
        if not vision_model.strip():
            vision_model = text_model

        base_url = raw_env.get("OPENROUTER_BASE_URL") or defaults.get(
            "base_url",
            "https://openrouter.ai/api/v1",
        )

        resolved_project_root = (
            project_root
            if project_root is not None
            else (model_file_path.parent if model_file_path is not None else Path.cwd())
        )

        resolved_uploads_dir = uploads_dir or resolved_project_root / "backend" / "uploads"
        resolved_sample_assets_dir = sample_assets_dir or resolved_project_root / "images"

        return cls(
            openrouter_api_key=api_key,
            openrouter_base_url=base_url,
            openrouter_text_model=text_model,
            openrouter_vision_model=vision_model,
            openrouter_timeout_seconds=int(raw_env.get("OPENROUTER_TIMEOUT_SECONDS", 120)),
            openrouter_max_retries=int(raw_env.get("OPENROUTER_MAX_RETRIES", 2)),
            uploads_dir=resolved_uploads_dir,
            sample_assets_dir=resolved_sample_assets_dir,
            project_root=resolved_project_root,
        )


def parse_model_file(model_file_path: Path | None) -> dict[str, str]:
    if model_file_path is None or not model_file_path.exists():
        return {}

    content = model_file_path.read_text(encoding="utf-8")
    parsed: dict[str, str] = {}

    api_match = API_PATTERN.search(content)
    if api_match:
        parsed["api_key"] = api_match.group("api_key")

    model_match = MODEL_PATTERN.search(content)
    if model_match:
        parsed["model"] = model_match.group("model")

    if "https://openrouter.ai/api/v1" in content:
        parsed["base_url"] = "https://openrouter.ai/api/v1"

    return parsed
