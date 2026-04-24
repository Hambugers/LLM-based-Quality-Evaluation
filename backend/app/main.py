from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.config import Settings
from app.schemas import EvaluationRequest
from app.services.evaluator import WorkflowService
from app.services.image_tools import validate_and_save_uploads


def create_app(
    test_overrides: dict[str, Any] | None = None,
    workflow_service: WorkflowService | Any | None = None,
) -> FastAPI:
    overrides = test_overrides or {}
    env = {**os.environ, **overrides.get("env", {})}
    project_root = resolve_path(env.get("LLM_EVAL_PROJECT_ROOT")) or Path(__file__).resolve().parents[2]
    settings = Settings.load(
        env=env,
        model_file_path=overrides.get("model_file_path")
        or resolve_path(env.get("LLM_EVAL_MODEL_FILE"))
        or project_root / "model.txt",
        uploads_dir=overrides.get("uploads_dir")
        or resolve_path(env.get("LLM_EVAL_UPLOADS_DIR")),
        sample_assets_dir=overrides.get("sample_assets_dir")
        or resolve_path(env.get("LLM_EVAL_SAMPLE_ASSETS_DIR"))
        or project_root / "images",
        frontend_dist_dir=overrides.get("frontend_dist_dir")
        or resolve_path(env.get("LLM_EVAL_FRONTEND_DIST_DIR"))
        or project_root / "frontend" / "dist",
        project_root=project_root,
    )
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)

    app = FastAPI(
        title="图文回复评估平台",
        version="0.1.0",
    )
    app.state.settings = settings
    app.state.workflow_service = workflow_service or WorkflowService(settings)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.mount("/uploads", StaticFiles(directory=settings.uploads_dir), name="uploads")
    if settings.sample_assets_dir.exists():
        app.mount(
            "/sample-assets",
            StaticFiles(directory=settings.sample_assets_dir),
            name="sample-assets",
        )

    @app.get("/health")
    async def health() -> dict[str, bool]:
        return {"ok": True}

    @app.post("/api/evaluate")
    async def evaluate(
        user_question: str = Form(...),
        model_answer: str = Form(...),
        images: list[UploadFile] = File(default_factory=list),
        text_model: str | None = Form(default=None),
        vision_model: str | None = Form(default=None),
    ) -> dict[str, Any]:
        request = build_evaluation_request(
            settings=settings,
            user_question=user_question,
            model_answer=model_answer,
            images=images,
            text_model=text_model,
            vision_model=vision_model,
        )
        return await app.state.workflow_service.evaluate(request)

    @app.post("/api/evaluate/stream")
    async def evaluate_stream(
        user_question: str = Form(...),
        model_answer: str = Form(...),
        images: list[UploadFile] = File(default_factory=list),
        text_model: str | None = Form(default=None),
        vision_model: str | None = Form(default=None),
    ) -> StreamingResponse:
        request = build_evaluation_request(
            settings=settings,
            user_question=user_question,
            model_answer=model_answer,
            images=images,
            text_model=text_model,
            vision_model=vision_model,
        )

        async def stream() -> Any:
            queue: asyncio.Queue[tuple[str, dict[str, Any]] | None] = asyncio.Queue()

            async def emitter(event_name: str, payload: dict[str, Any]) -> None:
                await queue.put((event_name, payload))

            async def runner() -> None:
                try:
                    await app.state.workflow_service.evaluate(request, emitter=emitter)
                except Exception as exc:  # noqa: BLE001
                    await emitter(
                        "run_failed",
                        {
                            "ok": False,
                            "error": str(exc),
                        },
                    )
                finally:
                    await queue.put(None)

            task = asyncio.create_task(runner())
            try:
                while True:
                    item = await queue.get()
                    if item is None:
                        break
                    event_name, payload = item
                    yield format_sse(event_name, payload)
            finally:
                await task

        return StreamingResponse(stream(), media_type="text/event-stream")

    mount_frontend(app, settings.frontend_dist_dir)

    return app


def resolve_path(value: str | None) -> Path | None:
    if not value:
        return None
    return Path(value).expanduser().resolve()


def mount_frontend(app: FastAPI, frontend_dist_dir: Path) -> None:
    index_html = frontend_dist_dir / "index.html"
    if not index_html.exists():
        return

    assets_dir = frontend_dist_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")

    @app.get("/", include_in_schema=False)
    async def frontend_index() -> FileResponse:
        return FileResponse(index_html)

    @app.get("/{path:path}", include_in_schema=False)
    async def frontend_fallback(path: str) -> FileResponse:
        if path.startswith(("api/", "uploads/", "sample-assets/")) or path in {"health", "openapi.json"}:
            raise HTTPException(status_code=404, detail="Not found")
        requested = (frontend_dist_dir / path).resolve()
        try:
            requested.relative_to(frontend_dist_dir.resolve())
        except ValueError:
            raise HTTPException(status_code=404, detail="Not found") from None
        if requested.is_file():
            return FileResponse(requested)
        return FileResponse(index_html)


def build_evaluation_request(
    settings: Settings,
    user_question: str,
    model_answer: str,
    images: list[UploadFile],
    text_model: str | None,
    vision_model: str | None,
) -> EvaluationRequest:
    if not user_question.strip():
        raise HTTPException(status_code=422, detail="用户问题不能为空")
    if not model_answer.strip():
        raise HTTPException(status_code=422, detail="模型回复不能为空")
    if len(user_question) > 4000 or len(model_answer) > 16000:
        raise HTTPException(status_code=422, detail="输入文本过长，请压缩后重试")

    saved_images = validate_and_save_uploads(images, settings.uploads_dir)
    return EvaluationRequest(
        user_question=user_question,
        model_answer=model_answer,
        images=saved_images,
        text_model=(text_model or "").strip() or None,
        vision_model=(vision_model or "").strip() or None,
    )


def format_sse(event_name: str, payload: dict[str, Any]) -> str:
    return f"event: {event_name}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


app = create_app()
