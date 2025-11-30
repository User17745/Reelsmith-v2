import pytest
import os
from unittest.mock import MagicMock, patch
from app.genai_client import GeminiClient
from google.api_core import exceptions

def test_client_initialization_no_keys():
    with patch.dict('os.environ', {}, clear=True):
        with pytest.raises(ValueError):
            GeminiClient()

@patch.dict(os.environ, {"GEMINI_API_KEYS": '["key1", "key2"]'})
def test_load_keys_from_env_list():
    client = GeminiClient()
    assert client.keys == ["key1", "key2"]

@patch.dict(os.environ, {"GEMINI_API_KEY": "single_key"})
def test_load_keys_from_single_env():
    # Ensure list env is not set
    with patch.dict(os.environ, {}, clear=True):
        os.environ["GEMINI_API_KEY"] = "single_key"
        client = GeminiClient()
        assert client.keys == ["single_key"]

def test_key_rotation():
    client = GeminiClient()
    client.keys = ['key1', 'key2']
    
    assert client._get_next_key() == 'key1'
    assert client._get_next_key() == 'key2'
    assert client._get_next_key() == 'key1'

@patch('google.generativeai.GenerativeModel')
def test_generate_content_success(mock_model_cls):
    mock_model = MagicMock()
    mock_model.generate_content.return_value.text = "Success"
    mock_model_cls.return_value = mock_model
    
    client = GeminiClient()
    client.keys = ['key1']
    
    result = client.generate_content("prompt")
    assert result == "Success"

@patch('google.generativeai.GenerativeModel')
def test_generate_content_retry_on_429(mock_model_cls):
    mock_model = MagicMock()
    # Fail once with 429, then succeed
    mock_model.generate_content.side_effect = [
        exceptions.ResourceExhausted("Quota exceeded"),
        MagicMock(text="Success")
    ]
    mock_model_cls.return_value = mock_model
    
    client = GeminiClient()
    client.keys = ['key1', 'key2']
    
    # Mock sleep to speed up test
    with patch('time.sleep', return_value=None):
        result = client.generate_content("prompt")
    
    assert result == "Success"
    assert mock_model.generate_content.call_count == 2
