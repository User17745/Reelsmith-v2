import os


class ConfigError(ValueError):
    pass


def _require_env(var_name, message):
    value = os.getenv(var_name)
    if not value:
        raise ConfigError(message)
    return value


def _validate_elevenlabs_output_format(output_format):
    if not output_format.startswith("pcm_"):
        raise ConfigError(
            f"Unsupported ELEVENLABS_OUTPUT_FORMAT '{output_format}'. "
            "Use a PCM format like pcm_24000 to keep WAV output compatible."
        )
    rate_str = output_format.replace("pcm_", "")
    try:
        int(rate_str)
    except ValueError as exc:
        raise ConfigError(
            f"Invalid ELEVENLABS_OUTPUT_FORMAT '{output_format}'. "
            "Expected like pcm_24000."
        ) from exc


def validate_tts_config():
    provider = os.getenv("TTS_PROVIDER", "gemini").strip().lower()
    if provider == "gemini":
        gemini_keys = os.getenv("GEMINI_API_KEYS")
        gemini_key = os.getenv("GEMINI_API_KEY")
        if not gemini_keys and not gemini_key:
            raise ConfigError(
                "GEMINI_API_KEYS (JSON list) or GEMINI_API_KEY is required when TTS_PROVIDER=gemini"
            )
        return

    if provider == "elevenlabs":
        _require_env(
            "ELEVENLABS_API_KEY",
            "ELEVENLABS_API_KEY is required when TTS_PROVIDER=elevenlabs",
        )
        _require_env(
            "ELEVENLABS_VOICE_ID",
            "ELEVENLABS_VOICE_ID is required when TTS_PROVIDER=elevenlabs",
        )
        output_format = os.getenv("ELEVENLABS_OUTPUT_FORMAT", "pcm_24000")
        _validate_elevenlabs_output_format(output_format)
        return

    raise ConfigError(
        f"Unsupported TTS_PROVIDER '{provider}'. Use 'gemini' or 'elevenlabs'."
    )


def validate_config():
    validate_tts_config()
