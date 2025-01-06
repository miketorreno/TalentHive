import pytest
from unittest.mock import AsyncMock, MagicMock
from applicant import start  # Import your start function here
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup

@pytest.fixture
def mock_update(mocker):
    """Fixture for mocking the update object."""
    update = mocker.MagicMock()
    update.message.reply_text = AsyncMock()  # Mock async method
    return update

@pytest.fixture
def mock_context(mocker):
    """Fixture for mocking the context object."""
    context = mocker.MagicMock()
    context.args = []
    return context

@pytest.fixture
def mock_get_user(mocker):
    """Fixture for mocking the get_user function."""
    return mocker.patch("applicant.get_user")  # Adjust the import path if necessary

@pytest.fixture
def mock_show_job(mocker):
    """Fixture for mocking the show_job function."""
    return mocker.patch("applicant.show_job")  # Adjust the import path if necessary


@pytest.mark.asyncio
async def test_start_user_not_registered(mock_update, mock_context, mock_get_user):
    """Test the case where the user is not registered."""
    # Arrange
    mock_get_user.return_value = None  # Simulate a non-registered user

    # Act
    result = await start(mock_update, mock_context)

    # Assert
    # Verify the correct reply message and keyboard are sent
    mock_update.message.reply_text.assert_called_once_with(
        "<b>Hello there 👋\t Welcome to HulumJobs! </b>\n\n"
        "Let’s get started, Please click the button below to register.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Register", callback_data='register')]
        ]),
        parse_mode='HTML'
    )
    # Verify the correct state is returned
    # assert result == "REGISTER"
    assert result == 0  # state "REGISTER" is 0 in the range function


# @pytest.mark.asyncio
# async def test_start_user_not_registered(mock_update, mock_context, mock_get_user):
#     """Test the case where the user is not registered."""
#     # Arrange
#     mock_get_user.return_value = None

#     # Act
#     result = await start(mock_update, mock_context)

#     # Assert
#     mock_update.message.reply_text.assert_called_once_with(
#         "<b>Hello there 👋\t Welcome to HulumJobs! </b>\n\n"
#         "Let’s get started, Please click the button below to register.",
#         reply_markup=InlineKeyboardMarkup([
#             [mock_update.message.reply_text.call_args[1]["reply_markup"].inline_keyboard[0][0]]
#         ]),
#         parse_mode='HTML'
#     )
#     assert result == "REGISTER"


@pytest.mark.asyncio
async def test_start_user_registered_no_args(mock_update, mock_context, mock_get_user):
    """Test the case where the user is registered and no args are passed."""
    # Arrange
    mock_get_user.return_value = ["id", "username", "email", "Test User"]

    # Act
    await start(mock_update, mock_context)

    # Assert
    mock_update.message.reply_text.assert_called_once_with(
        text=(
            "<b>Hello Test 👋\t Welcome to HulumJobs!</b> \n\n"
            "<b>💼 \tBrowse Jobs</b>:\t find jobs that best fit your schedule \n\n"
            "<b>📌 \tSaved Jobs</b>:\t your saved jobs \n\n"
            "<b>👤 \tMy Profile</b>:\t manage your profile \n\n"
            "<b>📑 \tMy Applications</b>:\t view and track your applications \n\n"
            "<b>❓ \tHelp</b>:\t show help message \n\n"
        ),
        reply_markup=ReplyKeyboardMarkup([
            ["Browse Jobs", "Saved Jobs"],
            ["My Profile", "My Applications"],
            ["Help"]
        ], resize_keyboard=True),
        parse_mode='HTML'
    )


@pytest.mark.asyncio
async def test_start_user_registered_with_args(mock_update, mock_context, mock_get_user, mock_show_job):
    """Test the case where the user is registered and args are passed."""
    # Arrange
    mock_get_user.return_value = ["id", "username", "email", "Test User"]
    mock_context.args = ["apply_123"]

    # Act
    await start(mock_update, mock_context)

    # Assert
    mock_show_job.assert_awaited_once_with(mock_update, mock_context, "123")
