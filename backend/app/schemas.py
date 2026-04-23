from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal


NodeStatus = Literal["waiting", "running", "completed", "failed"]


@dataclass(slots=True)
class RequestImage:
    filename: str
    content_type: str
    saved_path: Path
    size_bytes: int
    width: int
    height: int
    sha256: str
    url: str


@dataclass(slots=True)
class EvaluationRequest:
    user_question: str
    model_answer: str
    images: list[RequestImage] = field(default_factory=list)
    text_model: str | None = None
    vision_model: str | None = None


@dataclass(slots=True)
class WorkflowNodeState:
    node_key: str
    node_name: str
    status: NodeStatus = "waiting"
    started_at: str | None = None
    ended_at: str | None = None
    duration_ms: int | None = None
    summary: str | None = None
    error: str | None = None
    output: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_key": self.node_key,
            "node_name": self.node_name,
            "status": self.status,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "duration_ms": self.duration_ms,
            "summary": self.summary,
            "error": self.error,
            "output": self.output or {},
        }


def default_workflow_nodes() -> list[WorkflowNodeState]:
    return [
        WorkflowNodeState(node_key="input", node_name="输入接收"),
        WorkflowNodeState(node_key="preprocess", node_name="预处理"),
        WorkflowNodeState(node_key="text_eval", node_name="文本评估"),
        WorkflowNodeState(node_key="image_eval", node_name="图片基础质检"),
        WorkflowNodeState(node_key="cross_modal_eval", node_name="图文一致性评估"),
        WorkflowNodeState(node_key="aggregate", node_name="结果聚合"),
        WorkflowNodeState(node_key="final_decision", node_name="最终裁决"),
    ]
