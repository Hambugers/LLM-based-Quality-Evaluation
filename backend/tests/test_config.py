from pathlib import Path

import pytest

from app.config import Settings


def test_settings_fall_back_to_model_file(tmp_path: Path) -> None:
    model_file = tmp_path / "model.txt"
    model_file.write_text(
        'API:sk-test-key\nmodel="google/gemma-4-31b-it:free"\n',
        encoding="utf-8",
    )

    settings = Settings.load(
        env={},
        model_file_path=model_file,
        uploads_dir=tmp_path / "uploads",
        sample_assets_dir=tmp_path / "assets",
    )

    assert settings.openrouter_api_key == "sk-test-key"
    assert settings.openrouter_text_model == "google/gemma-4-31b-it:free"
    assert settings.openrouter_vision_model == "google/gemma-4-31b-it:free"
    assert settings.openrouter_base_url == "https://openrouter.ai/api/v1"


def test_env_values_override_model_file(tmp_path: Path) -> None:
    model_file = tmp_path / "model.txt"
    model_file.write_text(
        'API:sk-model-file\nmodel="google/gemma-4-31b-it:free"\n',
        encoding="utf-8",
    )

    settings = Settings.load(
        env={
            "OPENROUTER_API_KEY": "sk-env",
            "OPENROUTER_TEXT_MODEL": "custom/text",
            "OPENROUTER_VISION_MODEL": "",
            "OPENROUTER_BASE_URL": "https://custom.example/api/v1",
        },
        model_file_path=model_file,
        uploads_dir=tmp_path / "uploads",
        sample_assets_dir=tmp_path / "assets",
    )

    assert settings.openrouter_api_key == "sk-env"
    assert settings.openrouter_text_model == "custom/text"
    assert settings.openrouter_vision_model == "custom/text"
    assert settings.openrouter_base_url == "https://custom.example/api/v1"


def test_missing_api_key_raises(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
        Settings.load(
            env={},
            model_file_path=tmp_path / "missing-model.txt",
            uploads_dir=tmp_path / "uploads",
            sample_assets_dir=tmp_path / "assets",
        )
