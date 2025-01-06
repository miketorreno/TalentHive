import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_update(mocker):
    return mocker.MagicMock()

@pytest.fixture
def mock_context(mocker):
    return mocker.MagicMock()

def test_start_command(mock_update, mock_context):
    from main import start_command
    start_command(mock_update, mock_context)
    mock_update.message.reply_text.assert_called_once_with("Welcome to the bot!")
