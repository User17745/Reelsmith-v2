import json
import wave

from app.subtitles import generate_subtitles, verify_subtitle_timing


def _write_wav(path, duration_sec, sample_rate=24000):
    frames = int(duration_sec * sample_rate)
    with wave.open(path, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b"\x00\x00" * frames)


def test_generate_subtitles_matches_audio_duration(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    (workspace / "scripts").mkdir(parents=True)
    (workspace / "output").mkdir(parents=True)

    post_id = "subtitle_test"
    script = {
        "scenes": [
            {"text": "Hello world"},
            {"text": "This is a test subtitle"},
        ]
    }
    with open(workspace / "scripts" / f"{post_id}.json", "w") as f:
        json.dump(script, f)

    _write_wav(workspace / "output" / f"{post_id}.wav", duration_sec=4.0)

    monkeypatch.setattr("app.subtitles.WORKSPACE_DIR", str(workspace))
    segments, subtitle_path, audio_duration = generate_subtitles(post_id)

    assert subtitle_path is not None
    assert audio_duration == 4.0
    assert segments[-1].end == audio_duration
    assert verify_subtitle_timing(segments, audio_duration) == []


def test_verify_subtitle_timing_detects_overlap():
    segments = [
        type("Seg", (), {"start": 0.0, "end": 2.0, "text": "a"})(),
        type("Seg", (), {"start": 1.5, "end": 3.0, "text": "b"})(),
    ]
    errors = verify_subtitle_timing(segments, audio_duration=3.0)
    assert "overlap" in errors
