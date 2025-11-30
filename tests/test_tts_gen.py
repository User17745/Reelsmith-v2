import pytest
from unittest.mock import MagicMock, patch
import json
import os
from app.tts_gen import generate_tts

@patch('app.tts_gen.client')
def test_generate_tts_success(mock_client, tmp_path):
    # Setup mock workspace
    workspace = tmp_path / "workspace"
    (workspace / "scripts").mkdir(parents=True)
    (workspace / "output").mkdir(parents=True)
    
    # Create test file
    post_id = "test_tts"
    data = {
        "scenes": [
            {"text": "Hello world"},
            {"text": "This is a test"}
        ]
    }
    with open(workspace / "scripts" / f"{post_id}.json", "w") as f:
        json.dump(data, f)
        
    # Mock Gemini response
    mock_client.generate_audio.return_value = b"fake_audio_bytes"
    
    # Run TTS
    with patch('app.tts_gen.WORKSPACE_DIR', str(workspace)):
        generate_tts(post_id)
        
    # Verify file created
    assert (workspace / "output" / f"{post_id}.wav").exists()
    with open(workspace / "output" / f"{post_id}.wav", "rb") as f:
        # Check for RIFF header
        assert f.read(4) == b"RIFF"
    
    # Verify client call
    mock_client.generate_audio.assert_called_once()
    args = mock_client.generate_audio.call_args[0][0]
    assert "Hello world" in args
    assert "This is a test" in args

@patch('app.tts_gen.client')
def test_generate_tts_no_text(mock_client, tmp_path):
    # Setup mock workspace
    workspace = tmp_path / "workspace"
    (workspace / "scripts").mkdir(parents=True)
    
    # Create test file
    post_id = "test_no_text"
    data = {"scenes": [{"visual": "image only"}]}
    with open(workspace / "scripts" / f"{post_id}.json", "w") as f:
        json.dump(data, f)
        
    # Run TTS
    with patch('app.tts_gen.WORKSPACE_DIR', str(workspace)):
        generate_tts(post_id)
        
    # Verify client NOT called
    mock_client.generate_audio.assert_not_called()
    assert not (workspace / "output" / f"{post_id}.wav").exists()
