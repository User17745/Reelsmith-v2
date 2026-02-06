from unittest.mock import patch, MagicMock

from app.pipeline_test import run_pipeline_test


@patch("app.render.subprocess.run")
def test_pipeline_test_mode_creates_outputs(mock_run, tmp_path):
    workspace = tmp_path / "workspace"

    def _fake_run(cmd, check, stdout, stderr):
        output_path = workspace / "output" / "fixture_post.mp4"
        output_path.write_bytes(b"video")
        return MagicMock()

    mock_run.side_effect = _fake_run
    run_pipeline_test(post_id="fixture_post", workspace_dir=str(workspace))

    output_dir = workspace / "output"
    assert (output_dir / "fixture_post.mp4").exists()
    assert (output_dir / "fixture_post_validation.json").exists()
