from app.services.aggregator import aggregate_results


def test_aggregate_results_returns_usable_for_strong_outputs() -> None:
    result = aggregate_results(
        preprocess={
            "strong_visual_dependency": False,
            "task_type": "recommendation",
        },
        text_eval={"score": 0.82, "risks": []},
        image_eval={"score": 0.9, "duplicate_ratio": 0.0, "invalid_count": 0},
        cross_modal_eval={
            "score": 0.88,
            "misleading_risk": 0.1,
            "irrelevant_image_ratio": 0.0,
        },
    )

    assert result["hard_fail"] is False
    assert result["final_label"] == "可用"
    assert result["final_score"] >= 0.75


def test_aggregate_results_hard_fails_when_visual_task_has_no_images() -> None:
    result = aggregate_results(
        preprocess={
            "strong_visual_dependency": True,
            "task_type": "oracle-bone-script",
        },
        text_eval={"score": 0.72, "risks": []},
        image_eval={
            "score": 0.0,
            "duplicate_ratio": 0.0,
            "invalid_count": 0,
            "image_count": 0,
        },
        cross_modal_eval={
            "score": 0.0,
            "misleading_risk": 1.0,
            "irrelevant_image_ratio": 1.0,
        },
    )

    assert result["hard_fail"] is True
    assert result["final_label"] == "不可用"
    assert "强视觉依赖" in result["hard_fail_reason"]
