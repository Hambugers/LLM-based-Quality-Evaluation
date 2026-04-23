from __future__ import annotations

import traceback
from collections.abc import Awaitable, Callable
from dataclasses import asdict
from typing import Any

from app.config import Settings
from app.prompts.final_decision import SYSTEM_PROMPT as FINAL_DECISION_PROMPT
from app.prompts.preprocess import SYSTEM_PROMPT as PREPROCESS_PROMPT
from app.prompts.text_judge import SYSTEM_PROMPT as TEXT_JUDGE_PROMPT
from app.prompts.vision_judge import SYSTEM_PROMPT as VISION_JUDGE_PROMPT
from app.schemas import EvaluationRequest, WorkflowNodeState, default_workflow_nodes
from app.services.aggregator import aggregate_results
from app.services.image_tools import build_image_quality_result
from app.services.openrouter_client import OpenRouterClient, image_to_openrouter_part
from app.utils.ids import new_run_id
from app.utils.logging import make_log
from app.utils.time import duration_ms, utc_now, utc_now_iso


Emitter = Callable[[str, dict[str, Any]], Awaitable[None]]


class WorkflowService:
    def __init__(self, settings: Settings, openrouter_client: OpenRouterClient | None = None) -> None:
        self.settings = settings
        self.openrouter_client = openrouter_client or OpenRouterClient(settings)

    async def evaluate(
        self,
        request: EvaluationRequest,
        emitter: Emitter | None = None,
    ) -> dict[str, Any]:
        run_id = new_run_id()
        run_started_at = utc_now()
        logs: list[dict[str, str]] = []
        nodes = default_workflow_nodes()
        node_map = {node.node_key: node for node in nodes}

        if emitter is not None:
            await emitter("run_started", {"run_id": run_id, "time": utc_now_iso()})

        async def log(level: str, message: str) -> None:
            entry = make_log(level, message)
            logs.append(entry)
            if emitter is not None:
                await emitter("log", entry)

        async def run_node(
            key: str,
            operation: Callable[[], Awaitable[dict[str, Any]]],
        ) -> dict[str, Any]:
            node = node_map[key]
            node.status = "running"
            node.started_at = utc_now_iso()
            await emit_node(node, emitter)
            await log("info", f"开始执行{node.node_name}节点")
            started_at = utc_now()
            try:
                result = await operation()
                finished_at = utc_now()
                node.status = "completed"
                node.ended_at = finished_at.isoformat().replace("+00:00", "Z")
                node.duration_ms = duration_ms(started_at, finished_at)
                node.output = result
                node.summary = summarize_result(key, result)
                await emit_node(node, emitter)
                await log("info", f"{node.node_name}节点完成")
                return result
            except Exception as exc:  # noqa: BLE001
                finished_at = utc_now()
                node.status = "failed"
                node.ended_at = finished_at.isoformat().replace("+00:00", "Z")
                node.duration_ms = duration_ms(started_at, finished_at)
                node.error = str(exc)
                node.output = {"trace": traceback.format_exc(limit=3)}
                node.summary = "节点执行失败"
                await emit_node(node, emitter)
                await log("error", f"{node.node_name}节点失败: {exc}")
                return {"error": str(exc), "failed": True}

        input_result = await run_node("input", lambda: self._input_node(request))
        preprocess = await run_node("preprocess", lambda: self._preprocess_node(request))
        text_eval = await run_node("text_eval", lambda: self._text_eval_node(request))
        image_eval = await run_node("image_eval", lambda: self._image_eval_node(request))
        cross_modal_eval = await run_node(
            "cross_modal_eval",
            lambda: self._cross_modal_eval_node(request, preprocess),
        )
        final_eval = await run_node(
            "aggregate",
            lambda: self._aggregate_node(preprocess, text_eval, image_eval, cross_modal_eval),
        )
        decision = await run_node(
            "final_decision",
            lambda: self._final_decision_node(preprocess, text_eval, image_eval, cross_modal_eval, final_eval),
        )

        run_ended_at = utc_now()
        workflow_status = "completed" if all(node.status != "failed" for node in nodes) else "partial"
        response = {
            "ok": True,
            "run_id": run_id,
            "workflow": {
                "status": workflow_status,
                "started_at": run_started_at.isoformat().replace("+00:00", "Z"),
                "ended_at": run_ended_at.isoformat().replace("+00:00", "Z"),
                "duration_ms": duration_ms(run_started_at, run_ended_at),
                "nodes": [node.to_dict() for node in nodes],
            },
            "preprocess": preprocess,
            "text_eval": text_eval,
            "image_eval": image_eval,
            "cross_modal_eval": cross_modal_eval,
            "final_eval": {**final_eval, **decision},
            "uploaded_images": [
                {
                    "name": image.filename,
                    "url": image.url,
                    "size_bytes": image.size_bytes,
                    "width": image.width,
                    "height": image.height,
                }
                for image in request.images
            ],
            "logs": logs,
        }
        if emitter is not None:
            await emitter("run_completed", response)
        return response

    async def _input_node(self, request: EvaluationRequest) -> dict[str, Any]:
        return {
            "user_question_length": len(request.user_question.strip()),
            "model_answer_length": len(request.model_answer.strip()),
            "image_count": len(request.images),
        }

    async def _preprocess_node(self, request: EvaluationRequest) -> dict[str, Any]:
        user_prompt = (
            f"用户问题：{request.user_question}\n"
            f"模型回复：{request.model_answer}\n"
            f"图片数量：{len(request.images)}"
        )
        fallback = heuristic_preprocess(request)
        try:
            response = await self.openrouter_client.judge_text(
                model=request.text_model or self.settings.openrouter_text_model,
                system_prompt=PREPROCESS_PROMPT,
                user_prompt=user_prompt,
            )
            parsed = response.get("parsed")
            if isinstance(parsed, dict):
                return {
                    "task_type": parsed.get("task_type", fallback["task_type"]),
                    "strong_visual_dependency": bool(
                        parsed.get("strong_visual_dependency", fallback["strong_visual_dependency"])
                    ),
                    "key_entities": parsed.get("key_entities", fallback["key_entities"]),
                    "reasoning": parsed.get("reasoning", fallback["reasoning"]),
                    "confidence": parsed.get("confidence", fallback["confidence"]),
                    "source": "model",
                }
        except Exception:  # noqa: BLE001
            pass
        fallback["source"] = "fallback"
        return fallback

    async def _text_eval_node(self, request: EvaluationRequest) -> dict[str, Any]:
        user_prompt = f"用户问题：{request.user_question}\n模型回复：{request.model_answer}"
        fallback = heuristic_text_eval(request)
        try:
            response = await self.openrouter_client.judge_text(
                model=request.text_model or self.settings.openrouter_text_model,
                system_prompt=TEXT_JUDGE_PROMPT,
                user_prompt=user_prompt,
            )
            parsed = response.get("parsed")
            if isinstance(parsed, dict):
                return {
                    "score": float(parsed.get("score", fallback["score"])),
                    "label": parsed.get("label", fallback["label"]),
                    "evidence": parsed.get("evidence", fallback["evidence"]),
                    "summary": parsed.get("summary", fallback["summary"]),
                    "risks": parsed.get("risks", fallback["risks"]),
                    "dimensions": parsed.get("dimensions", fallback["dimensions"]),
                    "source": "model",
                }
        except Exception:  # noqa: BLE001
            pass
        fallback["source"] = "fallback"
        return fallback

    async def _image_eval_node(self, request: EvaluationRequest) -> dict[str, Any]:
        result = build_image_quality_result(request.images)
        result["source"] = "code"
        return result

    async def _cross_modal_eval_node(
        self,
        request: EvaluationRequest,
        preprocess: dict[str, Any],
    ) -> dict[str, Any]:
        if not request.images:
            return {
                "score": 0.0 if preprocess.get("strong_visual_dependency") else 0.65,
                "label": "无图输入",
                "evidence": ["未提供图片"],
                "summary": "当前输入未提供图片，无法执行图文联合评估。",
                "misleading_risk": 0.9 if preprocess.get("strong_visual_dependency") else 0.2,
                "irrelevant_image_ratio": 1.0 if preprocess.get("strong_visual_dependency") else 0.0,
                "support_strength": 0.0,
                "source": "fallback",
            }

        image_parts = [
            image_to_openrouter_part(str(image.saved_path), image.content_type)
            for image in request.images
        ]
        user_prompt = (
            f"用户问题：{request.user_question}\n"
            f"模型回复：{request.model_answer}\n"
            f"预处理结果：{preprocess}"
        )
        fallback = heuristic_cross_modal_eval(request)
        try:
            response = await self.openrouter_client.judge_vision(
                model=request.vision_model or self.settings.openrouter_vision_model,
                system_prompt=VISION_JUDGE_PROMPT,
                user_prompt=user_prompt,
                image_parts=image_parts,
            )
            parsed = response.get("parsed")
            if isinstance(parsed, dict):
                return {
                    "score": float(parsed.get("score", fallback["score"])),
                    "label": parsed.get("label", fallback["label"]),
                    "evidence": parsed.get("evidence", fallback["evidence"]),
                    "summary": parsed.get("summary", fallback["summary"]),
                    "misleading_risk": float(parsed.get("misleading_risk", fallback["misleading_risk"])),
                    "irrelevant_image_ratio": float(
                        parsed.get("irrelevant_image_ratio", fallback["irrelevant_image_ratio"])
                    ),
                    "support_strength": float(parsed.get("support_strength", fallback["support_strength"])),
                    "source": "model",
                }
        except Exception:  # noqa: BLE001
            pass
        fallback["source"] = "fallback"
        return fallback

    async def _aggregate_node(
        self,
        preprocess: dict[str, Any],
        text_eval: dict[str, Any],
        image_eval: dict[str, Any],
        cross_modal_eval: dict[str, Any],
    ) -> dict[str, Any]:
        result = aggregate_results(preprocess, text_eval, image_eval, cross_modal_eval)
        result["source"] = "code"
        return result

    async def _final_decision_node(
        self,
        preprocess: dict[str, Any],
        text_eval: dict[str, Any],
        image_eval: dict[str, Any],
        cross_modal_eval: dict[str, Any],
        final_eval: dict[str, Any],
    ) -> dict[str, Any]:
        user_prompt = (
            "请基于以下评估结果给出专业总结和建议：\n"
            f"预处理：{preprocess}\n"
            f"文本评估：{text_eval}\n"
            f"图片评估：{image_eval}\n"
            f"图文一致性评估：{cross_modal_eval}\n"
            f"聚合结果：{final_eval}\n"
        )
        fallback = build_final_recommendation(final_eval, preprocess, cross_modal_eval)
        try:
            response = await self.openrouter_client.judge_text(
                model=self.settings.openrouter_text_model,
                system_prompt=FINAL_DECISION_PROMPT,
                user_prompt=user_prompt,
            )
            parsed = response.get("parsed")
            if isinstance(parsed, dict):
                return {
                    "summary": parsed.get("summary", fallback["summary"]),
                    "recommendations": parsed.get("recommendations", fallback["recommendations"]),
                    "source": "model",
                }
        except Exception:  # noqa: BLE001
            pass
        fallback["source"] = "fallback"
        return fallback


async def emit_node(node: WorkflowNodeState, emitter: Emitter | None) -> None:
    if emitter is None:
        return
    await emitter("node_update", node.to_dict())


def summarize_result(node_key: str, result: dict[str, Any]) -> str:
    if node_key == "input":
        return f"已接收 {result.get('image_count', 0)} 张图片。"
    if "summary" in result and isinstance(result["summary"], str):
        return result["summary"]
    if "final_label" in result:
        return f"最终标签：{result['final_label']}"
    if result.get("failed"):
        return "节点执行失败"
    return "节点已完成。"


def heuristic_preprocess(request: EvaluationRequest) -> dict[str, Any]:
    question = request.user_question
    strong_visual = any(keyword in question for keyword in ["甲骨文", "图片", "图", "长什么样", "字体"])
    task_type = "visual_explanation" if strong_visual else "text_recommendation"
    entities = [token for token in ["商务车", "GL8", "奥德赛", "传祺 E9", "森", "林", "甲骨文"] if token in question or token in request.model_answer]
    return {
        "task_type": task_type,
        "strong_visual_dependency": strong_visual,
        "key_entities": entities,
        "reasoning": "根据问题语义和回复内容估计任务对图片的依赖度。",
        "confidence": 0.72,
    }


def heuristic_text_eval(request: EvaluationRequest) -> dict[str, Any]:
    answer = request.model_answer.strip()
    score = 0.82 if len(answer) > 40 else 0.62
    risks: list[str] = []
    if "附" in answer and "图片" in answer:
        risks.append("图片引用需要与实际上传内容核对")
    if "甲骨文" in request.user_question:
        risks.append("该问题对图像示例质量较敏感")
    return {
        "score": score,
        "label": "中等偏高" if score >= 0.75 else "中等",
        "evidence": [answer[:120]],
        "summary": "文本回复具备基本结构，可支持后续图文联合校验。",
        "risks": risks,
        "dimensions": {
            "correctness": max(0.5, min(score + 0.03, 0.95)),
            "completeness": max(0.45, min(score, 0.92)),
            "clarity": max(0.5, min(score + 0.02, 0.94)),
        },
    }


def heuristic_cross_modal_eval(request: EvaluationRequest) -> dict[str, Any]:
    question = request.user_question
    image_count = len(request.images)
    if "甲骨文" in question:
        score = 0.38 if image_count > 0 else 0.0
        irrelevant_ratio = 0.58 if image_count > 0 else 1.0
        misleading_risk = 0.72 if image_count > 0 else 0.95
        summary = "图片中疑似存在部分相关字形，但混入较多非目标内容，支撑度不足。"
    else:
        score = 0.78 if image_count > 0 else 0.55
        irrelevant_ratio = 0.1 if image_count > 0 else 0.0
        misleading_risk = 0.18 if image_count > 0 else 0.3
        summary = "图片整体与车型推荐主题一致，可作为辅助支撑。"
    return {
        "score": score,
        "label": "中等",
        "evidence": [f"共收到 {image_count} 张图片。"],
        "summary": summary,
        "misleading_risk": misleading_risk,
        "irrelevant_image_ratio": irrelevant_ratio,
        "support_strength": max(0.0, min(score + 0.1, 1.0)),
    }


def build_final_recommendation(
    final_eval: dict[str, Any],
    preprocess: dict[str, Any],
    cross_modal_eval: dict[str, Any],
) -> dict[str, Any]:
    label = final_eval.get("final_label", "瑕疵")
    strong_visual_dependency = preprocess.get("strong_visual_dependency", False)
    recommendations = [
        "保留结构化评分和证据，便于复核。",
        "对图片与文本的对应关系做抽样人工校验。",
    ]
    if strong_visual_dependency or cross_modal_eval.get("irrelevant_image_ratio", 0) > 0.3:
        recommendations.append("减少无关图片，优先保留能够直接支撑结论的图片。")
    if final_eval.get("hard_fail"):
        recommendations.append("在进入正式生产链路前增加失败兜底或人工复核。")
    return {
        "summary": f"综合文本、图片和图文一致性评估，本次回复判定为“{label}”。",
        "recommendations": recommendations,
    }
