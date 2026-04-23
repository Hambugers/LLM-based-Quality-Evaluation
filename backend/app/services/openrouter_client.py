from __future__ import annotations

import asyncio
import base64
from typing import Any

import httpx

from app.config import Settings
from app.services.parser import parse_model_json


class OpenRouterClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def judge_text(self, model: str, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        return await self._chat_json(
            model=model,
            system_prompt=system_prompt,
            user_payload=user_prompt,
        )

    async def judge_vision(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        image_parts: list[dict[str, Any]],
    ) -> dict[str, Any]:
        content: list[dict[str, Any]] = [{"type": "text", "text": user_prompt}]
        content.extend(image_parts)
        return await self._chat_json(
            model=model,
            system_prompt=system_prompt,
            user_payload=content,
        )

    async def _chat_json(
        self,
        model: str,
        system_prompt: str,
        user_payload: str | list[dict[str, Any]],
    ) -> dict[str, Any]:
        url = f"{self.settings.openrouter_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "Multimodal Response Evaluation Platform",
        }
        payload = {
            "model": model,
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_payload},
            ],
        }

        last_error: Exception | None = None
        for attempt in range(self.settings.openrouter_max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.settings.openrouter_timeout_seconds) as client:
                    response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                body = response.json()
                message = body["choices"][0]["message"]["content"]
                content_text = normalize_content(message)
                parsed = parse_model_json(content_text)
                return {
                    "raw": body,
                    "content": content_text,
                    "parsed": parsed,
                }
            except (httpx.HTTPError, KeyError, ValueError) as exc:
                last_error = exc
                if attempt >= self.settings.openrouter_max_retries:
                    break
                await asyncio.sleep(min(1 + attempt, 3))

        raise RuntimeError(f"OpenRouter 调用失败: {last_error}") from last_error


def normalize_content(message_content: Any) -> str:
    if isinstance(message_content, str):
        return message_content
    if isinstance(message_content, list):
        text_parts = []
        for part in message_content:
            if isinstance(part, dict) and part.get("type") == "text":
                text_parts.append(part.get("text", ""))
        return "\n".join(text_parts)
    return str(message_content)


def image_to_openrouter_part(image_path: str, mime_type: str) -> dict[str, Any]:
    encoded = base64.b64encode(Path(image_path).read_bytes()).decode("ascii")
    return {
        "type": "image_url",
        "image_url": {
            "url": f"data:{mime_type};base64,{encoded}",
        },
    }


from pathlib import Path
