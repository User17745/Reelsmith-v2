import json
import wave
from unittest.mock import MagicMock, patch

from app.tts_gen import generate_tts
from app.tts_provider import AudioSpec


@patch('app.tts_gen.get_tts_client')
def test_generate_tts_success(mock_get_client, tmp_path):
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
        
    mock_client = MagicMock()
    mock_client.generate_audio.return_value = (
        b"fake_audio_bytes",
        AudioSpec(sample_rate=24000, sample_width=2, channels=1),
    )
    mock_get_client.return_value = mock_client
    
    # Run TTS
    with patch('app.tts_gen.WORKSPACE_DIR', str(workspace)):
        generate_tts(post_id)
        
    # Verify file created
    assert (workspace / "output" / f"{post_id}.wav").exists()
    with open(workspace / "output" / f"{post_id}.wav", "rb") as f:
        # Check for RIFF header
        assert f.read(4) == b"RIFF"
    with wave.open(str(workspace / "output" / f"{post_id}.wav"), "rb") as wav_file:
        assert wav_file.getframerate() == 24000
    
    # Verify client call
    mock_client.generate_audio.assert_called_once()
    args = mock_client.generate_audio.call_args[0][0]
    assert "Hello world" in args
    assert "This is a test" in args


@patch('app.tts_gen.get_tts_client')
def test_generate_tts_no_text(mock_get_client, tmp_path):
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
    mock_get_client.assert_not_called()
    assert not (workspace / "output" / f"{post_id}.wav").exists()
