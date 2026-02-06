import json
import os
import wave

from app.subtitles import run_subtitles
from app.render import run_render
from app.validation import generate_validation_report
from app import subtitles as subtitles_module
from app import render as render_module
from app import broll as broll_module

WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "workspace")
FIXTURE_SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "pipeline_script.json")


def _write_fixture_audio(path, duration_sec, sample_rate=24000):
    frames = int(duration_sec * sample_rate)
    with wave.open(path, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b"\x00\x00" * frames)


def run_pipeline_test(post_id="fixture_post", workspace_dir=WORKSPACE_DIR):
    scripts_dir = os.path.join(workspace_dir, "scripts")
    output_dir = os.path.join(workspace_dir, "output")
    os.makedirs(scripts_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(FIXTURE_SCRIPT_PATH):
        raise FileNotFoundError(f"Fixture script missing: {FIXTURE_SCRIPT_PATH}")

    with open(FIXTURE_SCRIPT_PATH, "r") as f:
        script_data = json.load(f)

    script_path = os.path.join(scripts_dir, f"{post_id}.json")
    with open(script_path, "w") as f:
        json.dump(script_data, f, indent=2)

    total_duration = sum(scene.get("duration", 0.0) for scene in script_data.get("scenes", []))
    audio_path = os.path.join(output_dir, f"{post_id}.wav")
    _write_fixture_audio(audio_path, duration_sec=total_duration)

    subtitles_module.WORKSPACE_DIR = workspace_dir
    render_module.WORKSPACE_DIR = workspace_dir
    broll_module.WORKSPACE_DIR = workspace_dir

    run_subtitles()
    run_render()
    generate_validation_report(post_id)


if __name__ == "__main__":
    run_pipeline_test()
