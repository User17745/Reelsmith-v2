import pytest
import os
import time
from unittest.mock import patch
from app.retention import cleanup_workspace

def test_cleanup_workspace(tmp_path):
    # Setup mock workspace
    workspace = tmp_path / "workspace"
    (workspace / "raw").mkdir(parents=True)
    
    # Create old file
    old_file = workspace / "raw" / "old.json"
    old_file.touch()
    # Set mtime to 8 days ago
    os.utime(old_file, (time.time() - 8*24*3600, time.time() - 8*24*3600))
    
    # Create new file
    new_file = workspace / "raw" / "new.json"
    new_file.touch()
    
    # Run cleanup
    with patch('app.retention.WORKSPACE_DIR', str(workspace)):
        cleanup_workspace(max_age_hours=168) # 7 days
        
    # Verify old file deleted
    assert not old_file.exists()
    
    # Verify new file exists
    assert new_file.exists()

def test_cleanup_nested_dirs(tmp_path):
    # Setup mock workspace with nested frames
    workspace = tmp_path / "workspace"
    frames_dir = workspace / "frames" / "post1"
    frames_dir.mkdir(parents=True)
    
    # Create old file in nested dir
    old_frame = frames_dir / "frame.png"
    old_frame.touch()
    os.utime(old_frame, (time.time() - 8*24*3600, time.time() - 8*24*3600))
    
    # Run cleanup
    with patch('app.retention.WORKSPACE_DIR', str(workspace)):
        cleanup_workspace(max_age_hours=168)
        
    # Verify file deleted
    assert not old_frame.exists()
    
    # Verify empty dir removed
    assert not frames_dir.exists()
