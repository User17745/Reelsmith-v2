import json
import os
import wave
from datetime import datetime, timezone

WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "workspace")


def _audio_duration_seconds(audio_path):
    with wave.open(audio_path, "rb") as wav_file:
        frames = wav_file.getnframes()
        rate = wav_file.getframerate()
        return frames / float(rate)


def _subtitle_duration_seconds(subtitle_path):
    if not os.path.exists(subtitle_path):
        return None
    last_end = None
    with open(subtitle_path, "r") as f:
        for line in f:
            if "-->" in line:
                end = line.split("-->")[1].strip()
                last_end = end
    if not last_end:
        return None
    time_part, millis = last_end.split(",")
    hours, minutes, seconds = [int(x) for x in time_part.split(":")]
    total = hours * 3600 + minutes * 60 + seconds + int(millis) / 1000.0
    return total


def _montage_duration_seconds(metadata_path):
    if not os.path.exists(metadata_path):
        return None
    with open(metadata_path, "r") as f:
        data = json.load(f)
    return data.get("duration")


def generate_validation_report(post_id):
    output_dir = os.path.join(WORKSPACE_DIR, "output")
    audio_path = os.path.join(output_dir, f"{post_id}.wav")
    subtitle_path = os.path.join(output_dir, f"{post_id}.srt")
    montage_metadata_path = os.path.join(output_dir, f"{post_id}_bg.json")
    report_path = os.path.join(output_dir, f"{post_id}_validation.json")

    audio_duration = _audio_duration_seconds(audio_path) if os.path.exists(audio_path) else None
    subtitle_duration = _subtitle_duration_seconds(subtitle_path)
    montage_duration = _montage_duration_seconds(montage_metadata_path)

    report = {
        "post_id": post_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "audio_duration": audio_duration,
        "subtitle_duration": subtitle_duration,
        "montage_duration": montage_duration,
    }

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    return report_path
