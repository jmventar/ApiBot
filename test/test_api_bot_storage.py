import os
import json
import pytest
from unittest.mock import MagicMock, patch
from src.api_bot.api_bot import ApiBot

class MockArgs:
    def __init__(self, url="http://example.com/{{0}}", source="json_array", dry=False, method="GET", delay=0, token="test-token", avoid_storage=False, clean=False):
        self.url = url
        self.source = source
        self.dry = dry
        self.method = method
        self.delay = delay
        self.token = token
        self.avoid_storage = avoid_storage
        self.clean = clean

def test_persist_to_storage():
    # Arrange
    args = MockArgs(avoid_storage=False)
    log_file = "test_log.json"
    result_file = "test_result.json"
    
    # Ensure files don't exist
    if os.path.exists(log_file): os.remove(log_file)
    if os.path.exists(result_file): os.remove(result_file)
    
    bot = ApiBot(args, ["elem1"], ["0"], log_filename=log_file, result_filename=result_file)
    bot.response_log = [{"log": "data"}]
    bot.response_data = [{"result": "data"}]
    
    # Act
    bot._persist_to_storage()
    
    # Assert
    assert os.path.exists(log_file)
    assert os.path.exists(result_file)
    
    with open(log_file, "r") as f:
        log_content = json.load(f)
    with open(result_file, "r") as f:
        result_content = json.load(f)
        
    assert log_content == [{"log": "data"}]
    assert result_content == [{"result": "data"}]
    
    # Cleanup
    os.remove(log_file)
    os.remove(result_file)

def test_persist_to_storage_avoid():
    # Arrange
    args = MockArgs(avoid_storage=True)
    log_file = "test_log_avoid.json"
    result_file = "test_result_avoid.json"
    
    bot = ApiBot(args, ["elem1"], ["0"], log_filename=log_file, result_filename=result_file)
    bot.response_log = [{"log": "data"}]
    bot.response_data = [{"result": "data"}]
    
    # Act
    bot._persist_to_storage()
    
    # Assert
    assert not os.path.exists(log_file)
    assert not os.path.exists(result_file)

@patch("src.api_bot.api_bot.requests.request")
def test_run_calls_persist_periodically(mock_request):
    # Arrange
    # Create enough elements to trigger periodic save (interval is 50)
    elements = [f"elem{i}" for i in range(55)]
    args = MockArgs(url="http://example.com/{{0}}")
    
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "application/json"}
    mock_response.json.return_value = {"key": "value"}
    mock_response.content = b'{"key": "value"}'
    mock_request.return_value = mock_response
    
    bot = ApiBot(args, elements, ["0"], log_filename="periodic_log.json", result_filename="periodic_result.json")
    
    with patch.object(bot, "_persist_to_storage") as mock_persist:
        # Act
        bot.run()
        
        # Assert
        # Should be called once at count 50 and once at the end
        assert mock_persist.call_count == 2
    
    # Final cleanup if files were created (though we mocked persist)
    if os.path.exists("periodic_log.json"): os.remove("periodic_log.json")
    if os.path.exists("periodic_result.json"): os.remove("periodic_result.json")
