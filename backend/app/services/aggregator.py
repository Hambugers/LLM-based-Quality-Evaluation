from __future__ import annotations

from typing import Any


def aggregate_results(
    preprocess: dict[str, Any] | None,
    text_eval: dict[str, Any] | None,
    image_eval: dict[str, Any] | None,
    cross_modal_eval: dict[str, Any] | None,
) -> dict[str, Any]:
    preprocess = preprocess or {}
    text_eval = text_eval or {}
    image_eval = image_eval or {}
    cross_modal_eval = cross_modal_eval or {}

    text_score = clamp_score(text_eval.get("score"), default=0.0)
    image_score = clamp_score(image_eval.get("score"), default=0.0)
    cross_modal_score = clamp_score(cross_modal_eval.get("score"), default=0.0)
    misleading_risk = clamp_score(cross_modal_eval.get("misleading_risk"), default=0.0)
    irrelevant_ratio = clamp_score(cross_modal_eval.get("irrelevant_image_ratio"), default=0.0)
    image_count = int(image_eval.get("image_count", 0))
    strong_visual_dependency = bool(preprocess.get("strong_visual_dependency", False))

    hard_fail_reason = ""
    if strong_visual_dependency and image_count == 0:
        hard_fail_reason = "强视觉依赖任务缺少可评估图片"
    elif cross_modal_score < 0.3 and image_count > 0:
        hard_fail_reason = "图文一致性过低"
    elif irrelevant_ratio >= 0.6 and image_count > 0:
        hard_fail_reason = "图片内容混杂，无关图片比例过高"
    elif misleading_risk >= 0.85:
        hard_fail_reason = "图文组合存在较高误导风险"

    final_score = round((text_score * 0.4) + (image_score * 0.15) + (cross_modal_score * 0.45), 4)
    if hard_fail_reason:
        final_score = min(final_score, 0.2)

    final_label = label_for_score(final_score)
    if hard_fail_reason:
        final_label = "不可用"

    reasons = [
        f"文本评估得分 {text_score:.2f}",
        f"图片质检得分 {image_score:.2f}",
        f"图文一致性得分 {cross_modal_score:.2f}",
    ]
    if misleading_risk > 0:
        reasons.append(f"误导风险 {misleading_risk:.2f}")
    if irrelevant_ratio > 0:
        reasons.append(f"无关图片比例 {irrelevant_ratio:.2f}")

    return {
        "hard_fail": bool(hard_fail_reason),
        "hard_fail_reason": hard_fail_reason,
        "final_score": final_score,
        "final_label": final_label,
        "final_reason": "；".join(reasons),
        "weights": {
            "text_eval": 0.4,
            "image_eval": 0.15,
            "cross_modal_eval": 0.45,
        },
    }


def clamp_score(value: Any, default: float) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(score, 1.0))


def label_for_score(score: float) -> str:
    if score >= 0.75:
        return "可用"
    if score >= 0.45:
        return "瑕疵"
    return "不可用"
