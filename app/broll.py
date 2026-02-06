import json
import logging
import os
import subprocess
from urllib.parse import urlparse

import requests

from app.logging_utils import configure_logging, log_event

DEFAULT_REGISTRY_PATH = os.getenv("MEDIA_REGISTRY_PATH", "data/media_registry.json")
WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "workspace")

configure_logging()
logger = logging.getLogger("reelsmith.broll")


class MediaRegistryError(ValueError):
    pass


def _load_registry(registry_path=DEFAULT_REGISTRY_PATH):
    if not os.path.exists(registry_path):
        raise MediaRegistryError(f"Media registry not found: {registry_path}")
    with open(registry_path, "r") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise MediaRegistryError("Media registry must be a JSON list")
    return data


def _validate_entry(entry):
    required = ["id", "source", "license", "attribution", "allowed_edits"]
    missing = [key for key in required if key not in entry or entry[key] in (None, "")]
    if missing:
        raise MediaRegistryError(f"Missing license metadata: {', '.join(missing)}")

    if "local_path" not in entry and "source_url" not in entry:
        raise MediaRegistryError("Registry entry must include local_path or source_url")


def load_media_registry(registry_path=DEFAULT_REGISTRY_PATH):
    registry = _load_registry(registry_path)
    for entry in registry:
        _validate_entry(entry)
    return registry


def _download_clip(entry, cache_dir):
    os.makedirs(cache_dir, exist_ok=True)
    filename = f"{entry['id']}.mp4"
    output_path = os.path.join(cache_dir, filename)
    if os.path.exists(output_path):
        return output_path

    source_url = entry.get("source_url")
    if not source_url:
        raise MediaRegistryError(f"No source_url for entry {entry['id']}")

    response = requests.get(source_url, timeout=120)
    response.raise_for_status()
    with open(output_path, "wb") as f:
        f.write(response.content)
    return output_path


def _resolve_clip_path(entry, cache_dir):
    local_path = entry.get("local_path")
    if local_path and os.path.exists(local_path):
        return local_path
    return _download_clip(entry, cache_dir)


def _is_allowed_source(entry, allowlist):
    if not allowlist:
        return False
    source_url = entry.get("source_url") or entry.get("source")
    if not source_url:
        return False
    domain = urlparse(source_url).netloc.lower()
    return domain in allowlist


def _score_entry(entry, tone, target_duration):
    score = 0.0
    motion_score = float(entry.get("motion_score", 0.0))
    score += motion_score

    tone_tags = [tag.lower() for tag in entry.get("tone_tags", [])]
    if tone and tone.lower() in tone_tags:
        score += 1.0

    duration_seconds = entry.get("duration_seconds")
    if duration_seconds and target_duration:
        duration_score = min(float(duration_seconds) / target_duration, 1.0)
        score += duration_score

    return score


def select_background_clip(registry, tone=None, target_duration=None):
    if not registry:
        raise MediaRegistryError("Media registry is empty")
    scored = sorted(
        registry,
        key=lambda entry: _score_entry(entry, tone, target_duration),
        reverse=True,
    )
    return scored[0]


def generate_background_montage(post_id, target_duration, registry_path=DEFAULT_REGISTRY_PATH, tone=None):
    try:
        registry = load_media_registry(registry_path)
    except MediaRegistryError as exc:
        log_event(logger, "broll_registry_error", error=str(exc))
        return None

    allowlist = [domain.strip().lower() for domain in os.getenv("BROLL_ALLOWLIST", "").split(",") if domain.strip()]
    try:
        entry = select_background_clip(registry, tone=tone, target_duration=target_duration)
    except MediaRegistryError as exc:
        log_event(logger, "broll_registry_error", error=str(exc))
        return None
    if not _is_allowed_source(entry, allowlist):
        log_event(
            logger,
            "broll_allowlist_blocked",
            post_id=post_id,
            source=entry.get("source_url") or entry.get("source"),
        )
        return None
    cache_dir = os.path.join(WORKSPACE_DIR, "media")
    clip_path = _resolve_clip_path(entry, cache_dir)

    output_dir = os.path.join(WORKSPACE_DIR, "output")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{post_id}_bg.mp4")

    cmd = [
        "ffmpeg",
        "-y",
        "-stream_loop",
        "-1",
        "-i",
        clip_path,
        "-t",
        f"{target_duration}",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        output_path,
    ]

    log_event(
        logger,
        "broll_generate_start",
        post_id=post_id,
        clip_id=entry.get("id"),
        duration=target_duration,
    )
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if os.path.exists(output_path):
            metadata_path = os.path.join(output_dir, f"{post_id}_bg.json")
            with open(metadata_path, "w") as f:
                json.dump(
                    {
                        "post_id": post_id,
                        "clip_id": entry.get("id"),
                        "duration": target_duration,
                        "source": entry.get("source_url") or entry.get("source"),
                    },
                    f,
                )
            log_event(logger, "broll_generate_saved", post_id=post_id, path=output_path)
            return output_path
        log_event(logger, "broll_generate_missing", post_id=post_id, path=output_path)
        return None
    except subprocess.CalledProcessError as exc:
        log_event(logger, "broll_generate_error", post_id=post_id, error=exc.stderr.decode())
        return None
