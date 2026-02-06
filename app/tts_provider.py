import json
import os
from dataclasses import dataclass

import requests
from dotenv import load_dotenv

from app.genai_client import client as gemini_client
from app.retry import retry_with_backoff

load_dotenv()


@dataclass
class AudioSpec:
    sample_rate: int
    sample_width: int
    channels: int


class GeminiTTSClient:
    def __init__(self):
        # Gemini returns 16-bit PCM at 24kHz (audio/L16;rate=24000)
        self.audio_spec = AudioSpec(sample_rate=24000, sample_width=2, channels=1)

    def generate_audio(self, text):
        audio_bytes = gemini_client.generate_audio(text)
        return audio_bytes, self.audio_spec


class ElevenLabsTTSClient:
    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID")
        self.model_id = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")
        self.output_format = os.getenv("ELEVENLABS_OUTPUT_FORMAT", "pcm_24000")
        self.base_url = os.getenv("ELEVENLABS_BASE_URL", "https://api.elevenlabs.io")
        self.voice_settings_json = os.getenv("ELEVENLABS_VOICE_SETTINGS_JSON")

        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY is required when TTS_PROVIDER=elevenlabs")
        if not self.voice_id:
            raise ValueError("ELEVENLABS_VOICE_ID is required when TTS_PROVIDER=elevenlabs")

        self.audio_spec = self._audio_spec_from_output_format(self.output_format)

    def _audio_spec_from_output_format(self, output_format):
        if not output_format.startswith("pcm_"):
            raise ValueError(
                f"Unsupported ELEVENLABS_OUTPUT_FORMAT '{output_format}'. "
                "Use a PCM format like pcm_24000 to keep WAV output compatible."
            )
        rate_str = output_format.replace("pcm_", "")
        try:
            sample_rate = int(rate_str)
        except ValueError as exc:
            raise ValueError(
                f"Invalid ELEVENLABS_OUTPUT_FORMAT '{output_format}'. "
                "Expected like pcm_24000."
            ) from exc
        return AudioSpec(sample_rate=sample_rate, sample_width=2, channels=1)

    def generate_audio(self, text):
        url = f"{self.base_url}/v1/text-to-speech/{self.voice_id}"
        params = {"output_format": self.output_format}
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            "model_id": self.model_id,
        }
        if self.voice_settings_json:
            try:
                payload["voice_settings"] = json.loads(self.voice_settings_json)
            except json.JSONDecodeError as exc:
                raise ValueError("ELEVENLABS_VOICE_SETTINGS_JSON must be valid JSON.") from exc

        def _call():
            response = requests.post(url, params=params, headers=headers, json=payload, timeout=60)
            if response.status_code >= 400:
                raise RuntimeError(
                    f"ElevenLabs TTS failed ({response.status_code}): {response.text}"
                )
            return response

        response = retry_with_backoff(_call, retries=3, base_delay=1.0, exceptions=(RuntimeError, requests.RequestException))

        return response.content, self.audio_spec


def get_tts_client():
    provider = os.getenv("TTS_PROVIDER", "gemini").strip().lower()
    if provider == "gemini":
        return GeminiTTSClient()
    if provider == "elevenlabs":
        return ElevenLabsTTSClient()

    raise ValueError(f"Unsupported TTS_PROVIDER '{provider}'. Use 'gemini' or 'elevenlabs'.")
