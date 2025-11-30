import pytest
from unittest.mock import MagicMock, patch
import json
import os
from app.script_gen import generate_script

@patch('app.script_gen.client')
@patch('app.script_gen.get_db_connection')
def test_generate_script_success(mock_db, mock_client, tmp_path):
    # Setup mock workspace
    workspace = tmp_path / "workspace"
    (workspace / "canonical").mkdir(parents=True)
    (workspace / "scripts").mkdir(parents=True)
    
    # Create test file
    post_id = "test_script"
    data = {
        "title": "Funny cat",
        "op": "cat_lover",
        "selftext": "",
        "comments": [{"body": "Haha", "author": "a", "score": 1}]
    }
    with open(workspace / "canonical" / f"{post_id}.json", "w") as f:
        json.dump(data, f)
        
    # Mock Gemini response
    mock_script = {
        "tone": "funny",
        "pacing": "fast",
        "cta": "Follow for more",
        "caption_style": "bold-large",
        "length_seconds": 30,
        "scenes": [{"text": "Look at this cat", "start": 0, "duration": 5, "visual": "cat image"}]
    }
    mock_client.generate_json.return_value = mock_script
    
    # Mock DB
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor
    
    # Run generation
    with patch('app.script_gen.WORKSPACE_DIR', str(workspace)):
        generate_script(post_id)
        
    # Verify file created
    assert (workspace / "scripts" / f"{post_id}.json").exists()
    
    # Verify DB insert
    mock_cursor.execute.assert_called_once()
    assert "INSERT OR REPLACE INTO scripts" in mock_cursor.execute.call_args[0][0]

@patch('app.script_gen.client')
def test_generate_script_invalid_json(mock_client, tmp_path):
    # Setup mock workspace
    workspace = tmp_path / "workspace"
    (workspace / "canonical").mkdir(parents=True)
    
    # Create test file
    post_id = "test_invalid"
    data = {"title": "t", "op": "o", "comments": []}
    with open(workspace / "canonical" / f"{post_id}.json", "w") as f:
        json.dump(data, f)
        
    # Mock Gemini response (missing keys)
    mock_client.generate_json.return_value = {"tone": "funny"}
    
    # Run generation
    with patch('app.script_gen.WORKSPACE_DIR', str(workspace)):
        generate_script(post_id)
        
    # Verify file NOT created
    assert not (workspace / "scripts" / f"{post_id}.json").exists()
