from app.services.parser import parse_model_json


def test_parse_model_json_accepts_wrapped_json() -> None:
    raw = """
    Here is the result:
    ```json
    {"score": 0.81, "label": "good", "evidence": ["clear"], "summary": "ok"}
    ```
    """

    parsed = parse_model_json(raw)

    assert parsed["score"] == 0.81
    assert parsed["label"] == "good"


def test_parse_model_json_returns_none_for_invalid_content() -> None:
    assert parse_model_json("not-json-at-all") is None
