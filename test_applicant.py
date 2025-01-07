import pytest
from datetime import datetime, date
from unittest.mock import AsyncMock, MagicMock
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ConversationHandler
from applicant import (
    get_user, get_job, format_date, format_date_for_db, is_valid_email, get_all_cities, CITIES,
    start, cancel, show_job, browse_jobs, next_job, saved_jobs,
    main_menu,
)

@pytest.fixture
def mock_update(mocker):
    """Fixture for mocking the update object."""
    update = mocker.MagicMock()
    update.message.text = ""
    # update.effective_user.id = 12345
    update.message.reply_text = AsyncMock()  # Mock async method
    return update

@pytest.fixture
def mock_context(mocker):
    """Fixture for mocking the context object."""
    context = mocker.MagicMock()
    context.args = []
    return context

@pytest.fixture
def mock_update_message(mocker):
    """Fixture to mock a message-based update."""
    update = MagicMock()
    update.message.reply_text = MagicMock()
    update.callback_query = None
    return update

@pytest.fixture
def mock_update_callback_query(mocker):
    """Fixture to mock a callback query-based update."""
    update = MagicMock()
    update.callback_query.answer = MagicMock()
    update.callback_query.edit_message_text = MagicMock()
    update.message = None
    return update

@pytest.fixture
def mock_conn(mocker):
    """Fixture to mock the psycopg2 connection and cursor."""
    conn = mocker.patch("applicant.conn")
    conn.cursor.return_value = mocker.MagicMock()
    return conn

@pytest.fixture
def mock_get_user(mocker):
    """Fixture for mocking the get_user function."""
    return mocker.patch("applicant.get_user")

@pytest.fixture
def mock_start(mocker):
    """Fixture for mocking the start function."""
    return mocker.patch("applicant.start", new=AsyncMock)

@pytest.fixture
def mock_show_job(mocker):
    """Fixture for mocking the show_job function."""
    return mocker.patch("applicant.show_job")

# @pytest.fixture
# def mock_browse_jobs(mocker):
#     """Fixture for mocking the browse_jobs function."""
#     return mocker.patch("applicant.browse_jobs", new=AsyncMock)

# @pytest.fixture
# def mock_saved_jobs(mocker):
#     """Fixture for mocking the saved_jobs function."""
#     return mocker.patch("applicant.saved_jobs", new=AsyncMock)

# @pytest.fixture
# def mock_my_profile(mocker):
#     """Fixture for mocking the my_profile function."""
#     return mocker.patch("applicant.my_profile", new=AsyncMock)

# @pytest.fixture
# def mock_my_applications(mocker):
#     """Fixture for mocking the my_applications function."""
#     return mocker.patch("applicant.my_applications", new=AsyncMock)

# @pytest.fixture
# def mock_job_notifications(mocker):
#     """Fixture for mocking the job_notifications function."""
#     return mocker.patch("applicant.job_notifications", new=AsyncMock)

# @pytest.fixture
# def mock_help(mocker):
#     """Fixture for mocking the help function."""
#     return mocker.patch("applicant.help", new=AsyncMock)



# ? HELPER FUNCTIONS
# TODO: Test get_user function
# ### Test: get_user ###
# def test_get_user(mock_conn, mock_update, mock_context):
#     """Test the get_user function."""
#     # Arrange
#     mock_cursor = mock_conn.cursor.return_value
#     mock_cursor.fetchone.return_value = ("id", "name", "email", "role_id")
#     mock_update.effective_user.id = 12345

#     # Act
#     user = get_user(mock_update, mock_context)

#     # Assert
#     mock_cursor.execute.assert_called_once_with(
#         "SELECT * FROM users WHERE telegram_id = %s AND role_id = 1", (12345,)
#     )
#     assert user == ("id", "name", "email", "role_id")


### Test: get_job ###
def test_get_job(mock_conn, mock_update, mock_context):
    """Test the get_job function."""
    # Arrange
    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.fetchone.return_value = ("job_id", "job_title", "job_description")
    job_id = 101

    # Act
    job = get_job(mock_update, mock_context, job_id)

    # Assert
    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM jobs WHERE job_id = %s", (101,)
    )
    assert job == ("job_id", "job_title", "job_description")


### Test: format_date ###
def test_format_date():
    """Test the format_date function."""
    # Arrange
    date = datetime(2025, 1, 6)

    # Act
    formatted_date = format_date(date)

    # Assert
    assert formatted_date == "January 06, 2025"


### Test: format_date_for_db ###
def test_format_date_for_db():
    """Test the format_date_for_db function."""
    # Arrange
    date_str = "2025-01-06"

    # Act
    date = format_date_for_db(date_str)

    # Assert
    assert date == datetime(2025, 1, 6)


### Test: is_valid_email ###
@pytest.mark.parametrize("email,expected", [
    ("test@example.com", True),
    ("invalid-email", False),
    ("user@.com", False),
    ("user@domain.co", True)
])
def test_is_valid_email(email, expected):
    """Test the is_valid_email function."""
    # Act
    result = is_valid_email(email)

    # Assert
    assert result == expected


### Test: get_all_cities ###
def test_get_all_cities():
    """Test the get_all_cities function."""
    # Act
    keyboard_markup = get_all_cities()

    # Assert
    assert isinstance(keyboard_markup, InlineKeyboardMarkup)
    buttons = [
        button for row in keyboard_markup.inline_keyboard for button in row
    ]
    city_names = [button.text for button in buttons if button.text != "Others"]
    assert sorted(city_names) == CITIES
    assert buttons[-1].text == "Others"
    assert buttons[-1].callback_data == "Others"



# ? MAIN FUNCTIONS
### Test: show_job ###
@pytest.mark.asyncio
async def test_show_job_found_with_message(mock_conn, mock_update_message, mock_context):
    """Test showing a job when the job exists and the update is message-based."""
    # Arrange
    mock_cursor = mock_conn.cursor.return_value
    job_id = "101"
    mock_cursor.fetchone.return_value = (
        "101", "company", "position", "field", "Full-Time", "Software Engineer",
        "Exciting job description", "Few job requirements", "Addis Ababa", "Ethiopia", "5000 USD",
        datetime(2025, 1, 30)
    )

    # Mock the reply_text method
    mock_update_message.message.reply_text = AsyncMock()

    # Act
    await show_job(mock_update_message, mock_context, job_id)

    # Assert
    job_details = (
        "\nJob Title: <b>\tSoftware Engineer</b> \n\nJob Type: <b>\tFull-Time</b> \n\n"
        "Work Location: <b>\tAddis Ababa, Ethiopia</b> \n\nSalary: <b>\t5000 USD</b> \n\n"
        "Deadline: <b>\tJanuary 30, 2025</b> \n\n<b>Description</b>: \tExciting job description \n\n"
    )
    mock_update_message.message.reply_text.assert_called_once_with(
        text=job_details,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Apply", callback_data="apply_101")]]
        ),
        parse_mode="HTML",
    )


@pytest.mark.asyncio
async def test_show_job_found_with_callback_query(mock_conn, mock_update_callback_query, mock_context):
    """Test showing a job when the job exists and the update is callback query-based."""
    # Arrange
    mock_cursor = mock_conn.cursor.return_value
    job_id = "101"
    mock_cursor.fetchone.return_value = (
        "101", "company", "position", "field", "Full-Time", "Software Engineer",
        "Exciting job description", "2025-01-06", "Addis Ababa", "Ethiopia", "5000 USD",
        datetime(2025, 1, 30)
    )

    # Mock the edit_message_text method
    mock_update_callback_query.callback_query.edit_message_text = AsyncMock()

    # Act
    await show_job(mock_update_callback_query, mock_context, job_id)

    # Assert
    job_details = (
        "\nJob Title: <b>\tSoftware Engineer</b> \n\nJob Type: <b>\tFull-Time</b> \n\n"
        "Work Location: <b>\tAddis Ababa, Ethiopia</b> \n\nSalary: <b>\t5000 USD</b> \n\n"
        f"Deadline: <b>\tJanuary 30, 2025</b> \n\n<b>Description</b>: \tExciting job description \n\n"
    )
    mock_update_callback_query.callback_query.edit_message_text.assert_called_once_with(
        text=job_details,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Apply", callback_data="apply_101")]]
        ),
        parse_mode="HTML",
    )


@pytest.mark.asyncio
async def test_show_job_not_found_with_message(mock_conn, mock_update_message, mock_context):
    """Test showing a job when the job does not exist and the update is message-based."""
    # Arrange
    mock_cursor = mock_conn.cursor.return_value
    job_id = "999"
    mock_cursor.fetchone.return_value = None

    # Mock the reply_text method
    mock_update_message.message.reply_text = AsyncMock()

    # Act
    await show_job(mock_update_message, mock_context, job_id)

    # Assert
    mock_update_message.message.reply_text.assert_called_once_with("Job not found.")


@pytest.mark.asyncio
async def test_show_job_not_found_with_callback_query(mock_conn, mock_update_callback_query, mock_context):
    """Test showing a job when the job does not exist and the update is callback query-based."""
    # Arrange
    mock_cursor = mock_conn.cursor.return_value
    job_id = "999"
    mock_cursor.fetchone.return_value = None

    # Mock the answer method
    mock_update_callback_query.callback_query.answer = AsyncMock()

    # Act
    await show_job(mock_update_callback_query, mock_context, job_id)

    # Assert
    mock_update_callback_query.callback_query.answer.assert_called_once_with("Job not found.")


@pytest.mark.asyncio
async def test_browse_jobs_with_jobs(mock_conn, mock_update_message, mock_context):
    """Test browse_jobs when jobs are available."""
    # Arrange
    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.fetchall.return_value = [
        (1, None, None, None, "Full-Time", "Software Engineer", "Exciting job description", "Some requirements",
         "Addis Ababa", "Ethiopia", "5000 USD", datetime(2025, 1, 30), None)
    ]
    
    global current_job_index, total_jobs
    current_job_index = 0  # Reset for test
    total_jobs = 0

    mock_update_message.message.reply_text = AsyncMock()

    # Act
    await browse_jobs(mock_update_message, mock_context)

    # Assert
    job_details = (
        "\nJob Title: <b>\tSoftware Engineer</b> \n\nJob Type: <b>\tFull-Time</b> \n\n"
        "Work Location: <b>\tAddis Ababa, Ethiopia</b> \n\nSalary: <b>\t5000 USD</b> \n\n"
        "Deadline: <b>\tJanuary 30, 2025</b> \n\n<b>Description</b>: \nExciting job description \n\n"
        "<b>Requirements</b>: \nSome requirements \n\n"
    )

    mock_update_message.message.reply_text.assert_called_once_with(
        text=job_details,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Next", callback_data="job_next")],
                [InlineKeyboardButton("Apply", callback_data="apply_1")]
            ]
        ),
        parse_mode="HTML"
    )


@pytest.mark.asyncio
async def test_browse_jobs_no_jobs(mock_conn, mock_update_message, mock_context):
    """Test browse_jobs when no jobs are available."""
    # Arrange
    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.fetchall.return_value = []  # No jobs

    mock_update_message.message.reply_text = AsyncMock()

    # Act
    await browse_jobs(mock_update_message, mock_context)

    # Assert
    mock_update_message.message.reply_text.assert_called_once_with("No jobs available at the moment.")


@pytest.mark.asyncio
async def test_next_job(mock_update_callback_query, mock_context, mocker):
    """Test next_job to navigate to the next or previous job."""
    # Arrange
    global current_job_index, total_jobs
    current_job_index = 0
    total_jobs = 2

    # Mock the answer method
    mock_update_callback_query.callback_query.answer = AsyncMock()

    mocker.patch("applicant.browse_jobs", new=AsyncMock())
    mock_update_callback_query.callback_query.data = "job_next"

    # Act
    await next_job(mock_update_callback_query, mock_context)

    # Assert
    assert current_job_index == 1
    browse_jobs.assert_awaited_once_with(mock_update_callback_query, mock_context)

    # Test previous navigation
    mock_update_callback_query.callback_query.data = "job_previous"
    await next_job(mock_update_callback_query, mock_context)

    # Assert
    assert current_job_index == 0  # Back to the first job


@pytest.mark.asyncio
async def test_saved_jobs_with_saved_jobs(mock_conn, mock_update_message, mock_context, mocker):
    """Test saved_jobs when saved jobs are available."""
    # Arrange
    user_mock = (1, "Test User", "testuser@example.com", None)  # Mock user
    mocker.patch("applicant.get_user", return_value=user_mock)

    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.fetchall.return_value = [
        (1, "Job Title 1", None, None, "Full-Time", "Software Engineer", "Job description", "Requirements", 
         "Addis Ababa", "Ethiopia", "5000 USD", None, None),
        (2, "Job Title 2", None, None, "Part-Time", "Web Developer", "Another job description", "Other requirements", 
         "Bahir Dar", "Ethiopia", "2000 USD", None, None)
    ]

    mock_update_message.message.reply_text = AsyncMock()

    # Act
    await saved_jobs(mock_update_message, mock_context)

    # Assert
    assert mock_cursor.execute.called_with(
        "SELECT j.*, sj.* FROM saved_jobs sj JOIN jobs j ON sj.job_id = j.job_id WHERE sj.user_id = %s ORDER BY sj.created_at DESC LIMIT 50",
        (1,)
    )
    assert mock_update_message.message.reply_text.called


@pytest.mark.asyncio
async def test_saved_jobs_no_saved_jobs(mock_conn, mock_update_message, mock_context, mocker):
    """Test saved_jobs when no saved jobs are available."""
    # Arrange
    user_mock = (1, "Test User", "testuser@example.com", None)  # Mock user
    mocker.patch("applicant.get_user", return_value=user_mock)

    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.fetchall.return_value = []  # No saved jobs

    mock_update_message.message.reply_text = AsyncMock()

    # Act
    await saved_jobs(mock_update_message, mock_context)

    # Assert
    assert mock_cursor.execute.called_with(
        "SELECT j.*, sj.* FROM saved_jobs sj JOIN jobs j ON sj.job_id = j.job_id WHERE sj.user_id = %s ORDER BY sj.created_at DESC LIMIT 50",
        (1,)
    )
    mock_update_message.message.reply_text.assert_called_once_with("You haven't saved any job.")



# TODO: CHANGE THE ORDER
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


@pytest.mark.asyncio
async def test_cancel(mock_update, mock_context):
    """Test the cancel function."""
    # Act
    result = await cancel(mock_update, mock_context)

    # Assert
    # Verify the reply_text method is called with the expected message
    mock_update.message.reply_text.assert_called_once_with("Hope we can talk again soon.")
    
    # Verify the function returns ConversationHandler.END
    assert result == ConversationHandler.END


# @pytest.mark.asyncio
# async def test_main_menu_no_user(mock_update, mock_context, mock_get_user, mock_start):
#     """Test the main menu when the user is not registered."""
#     # Arrange
#     mock_get_user.return_value = None

#     # Act
#     await main_menu(mock_update, mock_context)

#     # Assert
#     mock_start.assert_awaited_once_with(mock_update, mock_context)
#     mock_update.message.reply_text.assert_not_called()


# @pytest.mark.asyncio
# async def test_main_menu_browse_jobs(mock_update, mock_context, mock_get_user, mock_browse_jobs):
#     """Test the main menu with 'Browse Jobs' choice."""
#     # Arrange
#     mock_get_user.return_value = ["id", "username", "email", "Test User"]
#     mock_update.message.text = "Browse Jobs"

#     # Act
#     await main_menu(mock_update, mock_context)

#     # Assert
#     mock_browse_jobs.assert_awaited_once_with(mock_update, mock_context)
#     mock_update.message.reply_text.assert_not_called()


# @pytest.mark.asyncio
# async def test_main_menu_invalid_choice(mock_update, mock_context, mock_get_user):
#     """Test the main menu with an invalid choice."""
#     # Arrange
#     mock_get_user.return_value = ["id", "username", "email", "Test User"]
#     mock_update.message.text = "Invalid Choice"

#     # Act
#     await main_menu(mock_update, mock_context)

#     # Assert
#     mock_update.message.reply_text.assert_called_once_with(
#         "Please use the buttons below to navigate."
#     )
