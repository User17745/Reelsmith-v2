import os
import json
import wave
import logging

from app.tts_provider import get_tts_client
from app.config import validate_config, ConfigError
from app.logging_utils import configure_logging, log_event

WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "workspace")
configure_logging()
logger = logging.getLogger("reelsmith.tts")

def generate_tts(post_id):
    scripts_dir = os.path.join(WORKSPACE_DIR, "scripts")
    script_path = os.path.join(scripts_dir, f"{post_id}.json")
    
    if not os.path.exists(script_path):
        log_event(logger, "tts_missing_script", post_id=post_id, path=script_path)
        return None

    with open(script_path, "r") as f:
        data = json.load(f)

    # Extract text from scenes
    narration_text = ""
    for scene in data.get("scenes", []):
        if "text" in scene:
            narration_text += f"{scene['text']} "
    
    narration_text = narration_text.strip()
    if not narration_text:
        log_event(logger, "tts_no_text", post_id=post_id)
        return None

    try:
        log_event(logger, "tts_generate_start", post_id=post_id)
        tts_client = get_tts_client()
        audio_bytes, audio_spec = tts_client.generate_audio(narration_text)
        
        if audio_bytes:
            output_dir = os.path.join(WORKSPACE_DIR, "output")
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"{post_id}.wav")
            
            # Write WAV file
            with wave.open(output_path, "wb") as wav_file:
                wav_file.setnchannels(audio_spec.channels)
                wav_file.setsampwidth(audio_spec.sample_width)
                wav_file.setframerate(audio_spec.sample_rate)
                wav_file.writeframes(audio_bytes)

            if os.path.exists(output_path):
                log_event(logger, "tts_audio_saved", post_id=post_id, path=output_path)
                return output_path
            log_event(logger, "tts_audio_missing", post_id=post_id, path=output_path)
            return None
        else:
            log_event(logger, "tts_generate_failed", post_id=post_id)
            return None
            
    except Exception as e:
        log_event(logger, "tts_generate_error", post_id=post_id, error=str(e))
        return None

def run_tts():
    try:
        validate_config()
    except ConfigError as e:
        log_event(logger, "tts_config_error", error=str(e))
        return

    scripts_dir = os.path.join(WORKSPACE_DIR, "scripts")
    if not os.path.exists(scripts_dir):
        log_event(logger, "tts_no_scripts_dir", path=scripts_dir)
        return

    files = [f for f in os.listdir(scripts_dir) if f.endswith(".json")]
    log_event(logger, "tts_batch_start", count=len(files))
    
    for filename in files:
        post_id = filename.replace(".json", "")
        generate_tts(post_id)

if __name__ == "__main__":
    run_tts()
