import pytest
from unittest.mock import MagicMock, patch
import json
import os
from app.moderate import moderate_post, flag_post

@patch('app.moderate.client')
@patch('app.moderate.get_db_connection')
def test_moderate_post_flagged(mock_db, mock_client, tmp_path):
    # Setup mock workspace
    workspace = tmp_path / "workspace"
    (workspace / "canonical").mkdir(parents=True)
    (workspace / "flagged").mkdir(parents=True)
    
    # Create test file
    post_id = "test_flag"
    data = {
        "title": "Bad content",
        "op": "bad_user",
        "selftext": "This is bad",
        "comments": []
    }
    with open(workspace / "canonical" / f"{post_id}.json", "w") as f:
        json.dump(data, f)
        
    # Mock Gemini response
    mock_client.generate_json.return_value = {
        "flag": True,
        "reasons": ["Hate speech"]
    }
    
    # Mock DB
    mock_cursor = MagicMock()
    mock_db.return_value.cursor.return_value = mock_cursor
    
    # Run moderation
    with patch('app.moderate.WORKSPACE_DIR', str(workspace)):
        moderate_post(post_id)
        
    # Verify file moved
    assert not (workspace / "canonical" / f"{post_id}.json").exists()
    assert (workspace / "flagged" / f"{post_id}.json").exists()
    
    # Verify DB insert
    mock_cursor.execute.assert_called_once()
    assert "INSERT OR REPLACE INTO flagged" in mock_cursor.execute.call_args[0][0]

@patch('app.moderate.client')
def test_moderate_post_safe(mock_client, tmp_path):
    # Setup mock workspace
    workspace = tmp_path / "workspace"
    (workspace / "canonical").mkdir(parents=True)
    
    # Create test file
    post_id = "test_safe"
    data = {
        "title": "Good content",
        "op": "good_user",
        "selftext": "This is good",
        "comments": []
    }
    with open(workspace / "canonical" / f"{post_id}.json", "w") as f:
        json.dump(data, f)
        
    # Mock Gemini response
    mock_client.generate_json.return_value = {
        "flag": False,
        "reasons": []
    }
    
    # Run moderation
    with patch('app.moderate.WORKSPACE_DIR', str(workspace)):
        moderate_post(post_id)
        
    # Verify file NOT moved
    assert (workspace / "canonical" / f"{post_id}.json").exists()
