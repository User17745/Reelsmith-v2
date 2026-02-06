import json
import wave

from app.validation import generate_validation_report


def _write_wav(path, duration_sec, sample_rate=24000):
    frames = int(duration_sec * sample_rate)
    with wave.open(path, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b"\x00\x00" * frames)


def test_generate_validation_report(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    output_dir = workspace / "output"
    output_dir.mkdir(parents=True)

    post_id = "validate_post"
    _write_wav(output_dir / f"{post_id}.wav", 3.0)
    (output_dir / f"{post_id}.srt").write_text("1\n00:00:00,000 --> 00:00:03,000\nHello\n")
    (output_dir / f"{post_id}_bg.json").write_text(json.dumps({"duration": 3.0}))

    monkeypatch.setattr("app.validation.WORKSPACE_DIR", str(workspace))
    report_path = generate_validation_report(post_id)

    report = json.loads((output_dir / f"{post_id}_validation.json").read_text())
    assert report_path.endswith(f"{post_id}_validation.json")
    assert report["audio_duration"] == 3.0
    assert report["subtitle_duration"] == 3.0
    assert report["montage_duration"] == 3.0
