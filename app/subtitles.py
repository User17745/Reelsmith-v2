import json
import logging
import os
import wave
from dataclasses import dataclass

from app.logging_utils import configure_logging, log_event

WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "workspace")
configure_logging()
logger = logging.getLogger("reelsmith.subtitles")


@dataclass
class SubtitleSegment:
    text: str
    start: float
    end: float


def _audio_duration_seconds(audio_path):
    with wave.open(audio_path, "rb") as wav_file:
        frames = wav_file.getnframes()
        rate = wav_file.getframerate()
        return frames / float(rate)


def _format_srt_time(seconds):
    millis = int(round(seconds * 1000))
    hours = millis // 3_600_000
    millis -= hours * 3_600_000
    minutes = millis // 60_000
    millis -= minutes * 60_000
    secs = millis // 1000
    millis -= secs * 1000
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def _segments_from_scenes(scenes, audio_duration):
    texts = [scene.get("text", "").strip() for scene in scenes if scene.get("text", "").strip()]
    if not texts:
        return []

    word_counts = [max(len(text.split()), 1) for text in texts]
    total_words = sum(word_counts)
    durations = [audio_duration * (count / total_words) for count in word_counts]

    segments = []
    cursor = 0.0
    for text, duration in zip(texts, durations):
        start = cursor
        end = cursor + duration
        segments.append(SubtitleSegment(text=text, start=start, end=end))
        cursor = end

    # Force last segment end to match audio duration exactly.
    segments[-1].end = audio_duration
    return segments


def generate_subtitles(post_id):
    scripts_dir = os.path.join(WORKSPACE_DIR, "scripts")
    output_dir = os.path.join(WORKSPACE_DIR, "output")
    script_path = os.path.join(scripts_dir, f"{post_id}.json")
    audio_path = os.path.join(output_dir, f"{post_id}.wav")
    subtitle_path = os.path.join(output_dir, f"{post_id}.srt")

    if not os.path.exists(script_path):
        log_event(logger, "subtitle_missing_script", post_id=post_id, path=script_path)
        return None, None, None
    if not os.path.exists(audio_path):
        log_event(logger, "subtitle_missing_audio", post_id=post_id, path=audio_path)
        return None, None, None

    with open(script_path, "r") as f:
        data = json.load(f)

    audio_duration = _audio_duration_seconds(audio_path)
    segments = _segments_from_scenes(data.get("scenes", []), audio_duration)
    if not segments:
        log_event(logger, "subtitle_no_segments", post_id=post_id)
        return None, None, audio_duration

    os.makedirs(output_dir, exist_ok=True)
    with open(subtitle_path, "w") as f:
        for idx, segment in enumerate(segments, start=1):
            f.write(f"{idx}\n")
            f.write(f"{_format_srt_time(segment.start)} --> {_format_srt_time(segment.end)}\n")
            f.write(f"{segment.text}\n\n")

    log_event(
        logger,
        "subtitle_generated",
        post_id=post_id,
        path=subtitle_path,
        duration=audio_duration,
        segments=len(segments),
    )
    return segments, subtitle_path, audio_duration


def verify_subtitle_timing(segments, audio_duration, tolerance=0.2):
    errors = []
    if not segments:
        errors.append("no_segments")
        return errors

    if abs(segments[-1].end - audio_duration) > tolerance:
        errors.append("duration_mismatch")

    prev_end = 0.0
    for segment in segments:
        if segment.start < prev_end:
            errors.append("overlap")
            break
        if segment.end < segment.start:
            errors.append("negative_duration")
            break
        prev_end = segment.end

    if segments[-1].end > audio_duration + tolerance:
        errors.append("trailing_subtitles")

    return errors


def run_subtitles():
    scripts_dir = os.path.join(WORKSPACE_DIR, "scripts")
    if not os.path.exists(scripts_dir):
        log_event(logger, "subtitle_no_scripts_dir", path=scripts_dir)
        return

    files = [f for f in os.listdir(scripts_dir) if f.endswith(".json")]
    max_duration = float(os.getenv("MAX_SCRIPT_DURATION_SECONDS", "120"))
    for filename in files:
        post_id = filename.replace(".json", "")
        segments, subtitle_path, audio_duration = generate_subtitles(post_id)
        if audio_duration and audio_duration > max_duration:
            log_event(
                logger,
                "subtitle_duration_exceeded",
                post_id=post_id,
                duration=audio_duration,
                max_duration=max_duration,
            )
        if segments and audio_duration is not None:
            subtitle_duration = segments[-1].end
            sync_delta = abs(audio_duration - subtitle_duration)
            errors = verify_subtitle_timing(segments, audio_duration)
            if errors:
                log_event(
                    logger,
                    "subtitle_verification_failed",
                    post_id=post_id,
                    errors=errors,
                    sync_delta=sync_delta,
                )
            else:
                log_event(
                    logger,
                    "subtitle_verification_ok",
                    post_id=post_id,
                    subtitle_duration=subtitle_duration,
                    sync_delta=sync_delta,
                )


if __name__ == "__main__":
    run_subtitles()
