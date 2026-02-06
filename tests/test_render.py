import json
import os
import wave
from unittest.mock import MagicMock, patch

import pytest

from app.render import generate_video, _build_transition_filters

@patch('app.render.subprocess.run')
@patch('app.render.create_card')
def test_generate_video_success(mock_create_card, mock_subprocess, tmp_path):
    # Setup mock workspace
    workspace = tmp_path / "workspace"
    (workspace / "scripts").mkdir(parents=True)
    (workspace / "output").mkdir(parents=True)
    
    # Create test files
    post_id = "test_render"
    data = {
        "scenes": [
            {"text": "Scene 1", "duration": 2.0},
            {"text": "Scene 2", "duration": 3.0}
        ]
    }
    with open(workspace / "scripts" / f"{post_id}.json", "w") as f:
        json.dump(data, f)
        
    with wave.open(str(workspace / "output" / f"{post_id}.wav"), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(24000)
        wav_file.writeframes(b"\x00\x00" * 24000)
        
    def _fake_run(cmd, check, stdout, stderr):
        output_path = workspace / "output" / f"{post_id}.mp4"
        output_path.write_bytes(b"fake_video")
        return MagicMock()

    mock_subprocess.side_effect = _fake_run

    # Run render
    with patch('app.render.WORKSPACE_DIR', str(workspace)):
        generate_video(post_id)
        
    # Verify create_card called
    assert mock_create_card.call_count == 2
    
    # Verify FFmpeg called
    mock_subprocess.assert_called_once()
    cmd = mock_subprocess.call_args[0][0]
    assert "ffmpeg" in cmd
    assert str(workspace / "output" / f"{post_id}.mp4") in cmd

@patch('app.render.subprocess.run')
def test_generate_video_missing_files(mock_subprocess, tmp_path):
    # Setup mock workspace
    workspace = tmp_path / "workspace"
    
    # Run render with missing files
    with patch('app.render.WORKSPACE_DIR', str(workspace)):
        generate_video("missing_id")
        
    # Verify FFmpeg NOT called
    mock_subprocess.assert_not_called()


def test_transition_filters_include_boundaries():
    filters = _build_transition_filters([2.0, 3.0], transition_duration=0.2)
    assert "fade=t=out:st=1.8:d=0.2" in filters
    assert "fade=t=in:st=2.0:d=0.2" in filters


@patch('app.render.subprocess.run')
@patch('app.render.create_card')
def test_subtitles_use_outline_style(mock_create_card, mock_subprocess, tmp_path):
    workspace = tmp_path / "workspace"
    (workspace / "scripts").mkdir(parents=True)
    (workspace / "output").mkdir(parents=True)

    post_id = "subtitle_render"
    data = {"scenes": [{"text": "Scene 1", "duration": 2.0}]}
    with open(workspace / "scripts" / f"{post_id}.json", "w") as f:
        json.dump(data, f)
    with wave.open(str(workspace / "output" / f"{post_id}.wav"), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(24000)
        wav_file.writeframes(b"\x00\x00" * 24000)
    with open(workspace / "output" / f"{post_id}.srt", "w") as f:
        f.write("1\n00:00:00,000 --> 00:00:02,000\nHello\n")

    def _fake_run(cmd, check, stdout, stderr):
        output_path = workspace / "output" / f"{post_id}.mp4"
        output_path.write_bytes(b"fake_video")
        return MagicMock()

    mock_subprocess.side_effect = _fake_run

    with patch('app.render.WORKSPACE_DIR', str(workspace)):
        generate_video(post_id)

    cmd = mock_subprocess.call_args[0][0]
    assert any("force_style" in part for part in cmd)
