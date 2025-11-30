import pytest
from unittest.mock import MagicMock, patch
import json
import os
from app.render import generate_video

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
        
    with open(workspace / "output" / f"{post_id}.wav", "wb") as f:
        f.write(b"fake_audio")
        
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
