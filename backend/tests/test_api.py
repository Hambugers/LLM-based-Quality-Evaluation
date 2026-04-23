from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from app.main import create_app


class StubWorkflowService:
    async def evaluate(self, request, emitter=None):  # noqa: ANN001
        if emitter is not None:
            await emitter("run_started", {"run_id": "run_test"})
            await emitter(
                "node_update",
                {
                    "node_key": "preprocess",
                    "status": "completed",
                    "summary": "预处理完成",
                },
            )
            await emitter("run_completed", {"run_id": "run_test"})
        uploaded_images = [
            {
                "name": image.filename,
                "url": f"/uploads/{image.filename}",
                "size_bytes": image.size_bytes,
            }
            for image in request.images
        ]
        return {
            "ok": True,
            "run_id": "run_test",
            "workflow": {
                "status": "completed",
                "started_at": "2026-04-23T00:00:00Z",
                "ended_at": "2026-04-23T00:00:01Z",
                "duration_ms": 1000,
                "nodes": [],
            },
            "preprocess": {"task_type": "recommendation"},
            "text_eval": {"score": 0.8},
            "image_eval": {"score": 0.9},
            "cross_modal_eval": {"score": 0.85},
            "final_eval": {"final_label": "可用", "final_score": 0.85},
            "uploaded_images": uploaded_images,
            "logs": [{"time": "2026-04-23T00:00:00Z", "level": "info", "message": "ok"}],
        }


def make_png_bytes() -> bytes:
    image = Image.new("RGB", (32, 24), color=(12, 32, 64))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_health_endpoint(tmp_path: Path) -> None:
    client = TestClient(create_app(test_overrides={"uploads_dir": tmp_path / "uploads"}))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_evaluate_endpoint_accepts_multipart(tmp_path: Path) -> None:
    client = TestClient(
        create_app(
            test_overrides={
                "uploads_dir": tmp_path / "uploads",
                "sample_assets_dir": tmp_path / "assets",
            },
            workflow_service=StubWorkflowService(),
        )
    )

    response = client.post(
        "/api/evaluate",
        data={
            "user_question": "30万以内商务车推荐",
            "model_answer": "推荐 GL8。",
        },
        files=[
            ("images", ("car.png", make_png_bytes(), "image/png")),
        ],
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["uploaded_images"][0]["name"] == "car.png"


def test_evaluate_endpoint_rejects_invalid_image_type(tmp_path: Path) -> None:
    client = TestClient(create_app(test_overrides={"uploads_dir": tmp_path / "uploads"}))

    response = client.post(
        "/api/evaluate",
        data={
            "user_question": "30万以内商务车推荐",
            "model_answer": "推荐 GL8。",
        },
        files=[
            ("images", ("bad.gif", b"gif89a", "image/gif")),
        ],
    )

    assert response.status_code == 422
    assert "格式" in response.json()["detail"]


def test_evaluate_stream_endpoint_emits_sse_events(tmp_path: Path) -> None:
    client = TestClient(
        create_app(
            test_overrides={"uploads_dir": tmp_path / "uploads"},
            workflow_service=StubWorkflowService(),
        )
    )

    with client.stream(
        "POST",
        "/api/evaluate/stream",
        data={
            "user_question": "森和林的甲骨文长什么样",
            "model_answer": "这是一个解释。",
        },
        files=[
            ("images", ("oracle.png", make_png_bytes(), "image/png")),
        ],
    ) as response:
        body = "".join(response.iter_text())

    assert response.status_code == 200
    assert "event: run_started" in body
    assert "event: node_update" in body
    assert "event: run_completed" in body
