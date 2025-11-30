from unittest.mock import patch
from app.worker import run_pipeline

@patch('app.worker.harvest')
@patch('app.worker.run_scoring')
@patch('app.worker.run_extraction')
@patch('app.worker.run_moderation')
@patch('app.worker.run_script_gen')
@patch('app.worker.run_tts')
@patch('app.worker.run_render')
def test_run_pipeline(mock_render, mock_tts, mock_script, mock_mod, mock_extract, mock_score, mock_harvest):
    run_pipeline()
    
    mock_harvest.assert_called_once()
    mock_score.assert_called_once()
    mock_extract.assert_called_once()
    mock_mod.assert_called_once()
    mock_script.assert_called_once()
    mock_tts.assert_called_once()
    mock_render.assert_called_once()
