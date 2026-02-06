import os
import pytest

from app.config import validate_config, ConfigError


def test_validate_config_gemini_requires_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEYS", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("TTS_PROVIDER", "gemini")
    with pytest.raises(ConfigError):
        validate_config()


def test_validate_config_gemini_accepts_single_key(monkeypatch):
    monkeypatch.setenv("TTS_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    validate_config()


def test_validate_config_elevenlabs_requires_keys(monkeypatch):
    monkeypatch.setenv("TTS_PROVIDER", "elevenlabs")
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    monkeypatch.delenv("ELEVENLABS_VOICE_ID", raising=False)
    with pytest.raises(ConfigError):
        validate_config()


def test_validate_config_elevenlabs_output_format(monkeypatch):
    monkeypatch.setenv("TTS_PROVIDER", "elevenlabs")
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key")
    monkeypatch.setenv("ELEVENLABS_VOICE_ID", "voice")
    monkeypatch.setenv("ELEVENLABS_OUTPUT_FORMAT", "mp3")
    with pytest.raises(ConfigError):
        validate_config()


def test_validate_config_unsupported_provider(monkeypatch):
    monkeypatch.setenv("TTS_PROVIDER", "unknown")
    with pytest.raises(ConfigError):
        validate_config()
