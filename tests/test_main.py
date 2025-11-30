from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import MagicMock, patch

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Reelsmith v2 Dashboard" in response.text

@patch('app.main.get_db_connection')
def test_get_flagged(mock_db):
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        {"post_id": "1", "reason": "bad", "flagged_at": "now", "data_path": "/tmp/1.json"}
    ]
    mock_db.return_value.cursor.return_value = mock_cursor
    
    response = client.get("/api/flagged")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["post_id"] == "1"

@patch('app.main.get_db_connection')
@patch('os.remove')
def test_resolve_flag(mock_remove, mock_db):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = {"data_path": "/tmp/1.json"}
    mock_db.return_value.cursor.return_value = mock_cursor
    
    with patch('os.path.exists', return_value=True):
        response = client.post("/api/flagged/1/resolve")
        
    assert response.status_code == 200
    mock_remove.assert_called_once_with("/tmp/1.json")
    assert "DELETE FROM flagged" in mock_cursor.execute.call_args_list[1][0][0]
