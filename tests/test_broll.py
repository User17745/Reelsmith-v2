import json
from unittest.mock import patch

from app.broll import (
    load_media_registry,
    generate_background_montage,
    MediaRegistryError,
    select_background_clip,
)


def test_registry_missing_license_metadata(tmp_path):
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(json.dumps([{"id": "clip1", "source": "example"}]))

    try:
        load_media_registry(str(registry_path))
        assert False, "Expected MediaRegistryError"
    except MediaRegistryError:
        assert True


@patch("app.broll.subprocess.run")
def test_generate_background_montage_uses_registry(mock_run, tmp_path, monkeypatch):
    registry_path = tmp_path / "registry.json"
    clip_path = tmp_path / "clip1.mp4"
    clip_path.write_bytes(b"fake")

    registry = [
        {
            "id": "clip1",
            "source": "https://local/video",
            "license": "test-license",
            "attribution": "tester",
            "allowed_edits": True,
            "local_path": str(clip_path),
        }
    ]
    registry_path.write_text(json.dumps(registry))

    output_dir = tmp_path / "workspace" / "output"
    output_dir.mkdir(parents=True)
    monkeypatch.setattr("app.broll.WORKSPACE_DIR", str(tmp_path / "workspace"))

    def _fake_run(cmd, check, stdout, stderr):
        out_path = output_dir / "post_bg.mp4"
        out_path.write_bytes(b"bg")
        return None

    mock_run.side_effect = _fake_run

    monkeypatch.setenv("BROLL_ALLOWLIST", "local")
    output = generate_background_montage("post", 5.0, registry_path=str(registry_path))
    assert output is not None
    cmd = mock_run.call_args[0][0]
    assert str(clip_path) in cmd
    assert "5.0" in cmd


def test_select_background_clip_prefers_motion_score():
    registry = [
        {"id": "low", "motion_score": 0.1, "tone_tags": ["funny"]},
        {"id": "high", "motion_score": 0.9, "tone_tags": ["funny"]},
    ]
    selected = select_background_clip(registry, tone="funny", target_duration=10.0)
    assert selected["id"] == "high"


@patch("app.broll.subprocess.run")
def test_allowlist_blocks_unapproved_domain(mock_run, tmp_path, monkeypatch):
    registry_path = tmp_path / "registry.json"
    clip_path = tmp_path / "clip1.mp4"
    clip_path.write_bytes(b"fake")

    registry = [
        {
            "id": "clip1",
            "source": "https://example.com/video",
            "license": "test-license",
            "attribution": "tester",
            "allowed_edits": True,
            "local_path": str(clip_path),
        }
    ]
    registry_path.write_text(json.dumps(registry))
    monkeypatch.setattr("app.broll.WORKSPACE_DIR", str(tmp_path / "workspace"))
    monkeypatch.setenv("BROLL_ALLOWLIST", "allowed.com")

    output = generate_background_montage("post", 5.0, registry_path=str(registry_path))
    assert output is None
    mock_run.assert_not_called()
