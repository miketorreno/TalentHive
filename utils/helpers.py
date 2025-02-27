import logging
import os
import re
import json
import datetime
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ContextTypes,
)
from utils.constants import (
    CITIES,
    GROUP_TOPIC_NEW_EMPLOYER_REGISTRATION_ID,
    ROLE_APPLICANT,
    GROUP_TOPIC_NEW_APPLICANT_REGISTRATION_ID,
    ROLE_EMPLOYER,
)
from utils.db import execute_query, redis_client

logger = logging.getLogger(__name__)


def get_applicant(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> tuple[Any, ...] | list[tuple[Any, ...]] | list[Any] | None:
    """
    Retrieve an applicant's information based on their Telegram ID. The function first attempts
    to get the applicant's data from the cache. If not found in the cache (cache miss), it queries
    the database for the user details and caches the result. The cached data is set with an
    expiration time of one hour. Returns a tuple or list containing the user's details, or None
    if the user is not found.

    Args:
        update (Update): The update object containing the effective user details.

    Returns:
        tuple[Any, ...] | list[tuple[Any, ...]] | list[Any] | None: The user's details or None
        if the user does not exist in the database.
    """

    telegram_id = update.effective_user.id
    # redis_client.delete(f"applicant:{telegram_id}")
    cached_applicant = redis_client.get(f"applicant:{telegram_id}")

    if not cached_applicant:
        logger.info("cache miss - applicant")
        applicant = execute_query(
            "SELECT user_id, telegram_id, role_id, name, username, email, phone, gender, dob, country, city, education, experience, cv, skills, portfolios, subscribed_alerts, preferences FROM users WHERE telegram_id = %s AND role_id = %s",
            (telegram_id, ROLE_APPLICANT),
        )
        if isinstance(applicant, list) and len(applicant) > 0:
            applicant = applicant[0]
            redis_client.set(f"applicant:{telegram_id}", json.dumps(applicant), ex=3600)
    else:
        logger.info("cache hit - applicant")
        applicant = json.loads(cached_applicant)

    if not applicant:
        return None

    return applicant


def get_employer(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> tuple[Any, ...] | list[tuple[Any, ...]] | list[Any] | None:
    """
    Retrieve an employer's information based on their Telegram ID. The function first attempts
    to get the employer's data from the cache. If not found in the cache (cache miss), it queries
    the database for the user details and caches the result. The cached data is set with an
    expiration time of one hour. Returns a tuple or list containing the user's details, or None
    if the user is not found.

    Args:
        update (Update): The update object containing the effective user details.

    Returns:
        tuple[Any, ...] | list[tuple[Any, ...]] | list[Any] | None: The user's details or None
        if the user does not exist in the database.
    """

    telegram_id = update.effective_user.id
    # redis_client.delete(f"applicant:{telegram_id}")
    cached_employer = redis_client.get(f"employer:{telegram_id}")

    if not cached_employer:
        logger.info("cache miss - employer")
        employer = execute_query(
            "SELECT user_id, telegram_id, role_id, name, username, email, phone, gender, dob, country, city, education, experience, cv, skills, portfolios, subscribed_alerts, preferences FROM users WHERE telegram_id = %s AND role_id = %s",
            (telegram_id, ROLE_EMPLOYER),
        )
        if isinstance(employer, list) and len(employer) > 0:
            employer = employer[0]
            redis_client.set(f"employer:{telegram_id}", json.dumps(employer), ex=3600)
    else:
        logger.info("cache hit - employer")
        employer = json.loads(cached_employer)

    if not employer:
        return None

    return employer


# def register_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     tg_user = update.effective_user
#     last_name = update.effective_user.last_name if update._effective_user.last_name else None
#     username = update.effective_user.username if update._effective_user.username else None

#     return execute_query("INSERT INTO users (telegram_id, first_name, last_name, username) VALUES (%s, %s, %s, %s)", (tg_user.id, tg_user.first_name, last_name, username))


def get_telegram_id(user_id):
    """
    Retrieve a user's Telegram ID from the database using their user ID.

    Args:
        user_id (int): The ID of the user whose Telegram ID is to be retrieved.

    Returns:
        str | None: The Telegram ID of the user, or None if the user does not exist in the database.
    """

    telegram_id = execute_query(
        "SELECT telegram_id FROM users WHERE user_id = %s", (user_id,)
    )

    if not telegram_id:
        return None

    return telegram_id[0]["telegram_id"]


def get_user(telegram_id, role_id):
    """
    Retrieves a user's details from the database using their Telegram ID and role ID.

    Args:
        telegram_id (int): The Telegram ID of the user to retrieve.
        role_id (int): The role ID of the user to retrieve.

    Returns:
        int | None: The user's ID or None if the user does not exist in the database.
    """

    user = execute_query(
        "SELECT * FROM users WHERE telegram_id = %s AND role_id = %s",
        (telegram_id, role_id),
    )

    if not user:
        return None

    return user[0]


def get_job(job_id) -> list[tuple[Any, ...]] | None:
    """
    Retrieves a job from the database by its job_id.

    Args:
        job_id (int): The ID of the job to retrieve.

    Returns:
        tuple[Any, ...] | list[tuple[Any, ...]] | list[Any] | None: The job's details or None
        if the job does not exist in the database.
    """

    job = execute_query("SELECT * FROM jobs WHERE job_id = %s", (job_id,))

    if not job:
        return None

    return job[0]


async def show_job(
    update: Update, context: ContextTypes.DEFAULT_TYPE, job_id: str
) -> None:
    """
    Shows a job with a given job_id.

    Args:
        update (Update): The Telegram update.
        context (ContextTypes.DEFAULT_TYPE): The context of the Telegram conversation.
        job_id (str): The job ID to show.

    Returns:
        None
    """

    job = get_job(job_id)

    if not job:
        if update.callback_query:
            await update.callback_query.answer("Job not found.")
        else:
            await update.message.reply_text("Job not found.")
        return

    job_details = (
        f"Job Title: <b>\t{job["job_title"]}</b> \n\n"
        f"Job Type: <b>\t{job["job_site"]} - {job["job_type"]}</b> \n\n"
        f"Work Location: <b>\t{job["job_city"]}, {job["job_country"]}</b> \n\n"
        f"Applicants Needed: <b>\t{job["gender_preference"]}</b> \n\n"
        f"Salary: <b>\t{job["salary_amount"]} {job["salary_currency"]}, {job["salary_type"]}</b> \n\n"
        f"Deadline: <b>\t{format_date(job["job_deadline"])}</b> \n\n"
        f"<b>Description</b>: \t{job["job_description"]} \n\n"
        f"<b>Requirements</b>: \t{job["job_requirements"]} \n\n"
    )

    keyboard = [
        [
            InlineKeyboardButton("Save", callback_data=f"save_{job["job_id"]}"),
            InlineKeyboardButton("Apply", callback_data=f"apply_{job["job_id"]}"),
        ],
    ]

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=job_details,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text(
            text=job_details,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )


def get_companies(user_id):
    """
    Retrieves a list of companies from the database belonging to the user with the given user_id.

    Args:
        user_id (int): The ID of the user whose companies are to be retrieved.

    Returns:
        list[tuple[Any, ...]] | None: A list of tuples containing the company details, or None
        if the user does not have any companies.
    """

    companies = execute_query("SELECT * FROM companies WHERE user_id = %s", (user_id,))

    if not companies:
        return None

    return companies


def get_jobs(user_id):
    jobs = execute_query("SELECT * FROM jobs WHERE user_id = %s", (user_id,))

    if not jobs:
        return None

    return jobs


def get_categories():
    """
    Retrieves all categories from the database.

    Returns:
        list[tuple[int, str]] | None: A list of tuples containing the category_id and name of each category, or None
        if no categories are found in the database.
    """

    categories = execute_query("SELECT * FROM categories")

    if not categories:
        return None

    return categories


def get_all_cities():
    """
    Returns an InlineKeyboardMarkup containing all cities in the CITIES tuple.
    The cities are organized into 2-column rows, with the last row containing an
    "Others" button.
    """

    buttons = [InlineKeyboardButton(city, callback_data=f"{city}") for city in CITIES]

    # Organize buttons into 2-column rows
    keyboard = [
        buttons[i : i + 2] for i in range(0, len(buttons), 2)
    ]  # Group buttons into rows
    keyboard.append([InlineKeyboardButton("Others", callback_data="Others")])

    return InlineKeyboardMarkup(keyboard)


async def notify_group():
    pass


async def notify_group_on_registration(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_data,
    topic_id=GROUP_TOPIC_NEW_APPLICANT_REGISTRATION_ID,
):
    view_keyboard = [
        [
            InlineKeyboardButton(
                "View Profile",
                callback_data=f"view_applicant_{user_data['telegram_id']}",
            )
        ]
    ]
    message = (
        f"\n🎉 <b>New User Registered!</b>\n\n"
        f"<b>Name</b>: {(user_data['firstname']).capitalize()} {(user_data['lastname']).capitalize() if len(user_data['lastname']) > 0 else ''}\n\n"
        f"<b>Email</b>: {user_data['email']}\n\n"
        f"<b>City</b>: {user_data['city']}\n\n"
    )

    await context.bot.send_message(
        chat_id=os.getenv("HULUMJOBS_GROUP_ID"),
        text=message,
        reply_markup=InlineKeyboardMarkup(view_keyboard),
        parse_mode="HTML",
        message_thread_id=topic_id,
    )
    return


async def view_applicant_profile(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    topic_id=GROUP_TOPIC_NEW_APPLICANT_REGISTRATION_ID,
):
    """
    Handle the 'View Profile' button and display user details on the group.
    """

    query = update.callback_query
    await query.answer()
    telegram_id = int(query.data.split("_")[-1])
    user = get_user(telegram_id, ROLE_APPLICANT)

    if not user:
        await context.bot.send_message(
            chat_id=os.getenv("HULUMJOBS_GROUP_ID"),
            text="User not found.",
            parse_mode="HTML",
        )
    else:
        await context.bot.send_message(
            chat_id=os.getenv("HULUMJOBS_GROUP_ID"),
            text="<b>User Profile</b>\n\n"
            f"<b>Job Seeker</b>\n\n"
            f"<b>👤 \tName</b>: \t{(user["name"].split()[0]).capitalize()} {(user["name"].split()[1]).capitalize() if len(user["name"].split()) > 1 else ''} \n\n"
            f"<b>\t&#64; \t\tUsername</b>: \t{user["username"]} \n\n"
            f"<b>👫 \tGender</b>: \t{user["gender"]} \n\n"
            f"<b>🎂 \tAge</b>: \t{user["dob"]} \n\n"
            f"<b>🌐 \tCountry</b>: \t{user["country"]} \n\n"
            f"<b>🏙️ \tCity</b>: \t{user["city"]} \n\n"
            f"<b>📧 \tEmail</b>: \t{user["email"]} \n\n"
            f"<b>📞 \tPhone</b>: \t{user["phone"]} \n\n",
            parse_mode="HTML",
            message_thread_id=topic_id,
        )


async def view_employer_profile(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    topic_id=GROUP_TOPIC_NEW_EMPLOYER_REGISTRATION_ID,
):
    """
    Handle the 'View Profile' button and display user details on the group.
    """

    query = update.callback_query
    await query.answer()
    telegram_id = int(query.data.split("_")[-1])
    user = get_user(telegram_id, ROLE_EMPLOYER)

    if not user:
        await context.bot.send_message(
            chat_id=os.getenv("HULUMJOBS_GROUP_ID"),
            text="User not found.",
            parse_mode="HTML",
        )
    else:
        await context.bot.send_message(
            chat_id=os.getenv("HULUMJOBS_GROUP_ID"),
            text="<b>User Profile</b>\n\n"
            f"<b>Employer</b>\n\n"
            f"<b>👤 \tName</b>: \t{(user["name"].split()[0]).capitalize()} {(user["name"].split()[1]).capitalize() if len(user["name"].split()) > 1 else ''} \n\n"
            f"<b>\t&#64; \t\tUsername</b>: \t{user["username"]} \n\n"
            f"<b>👫 \tGender</b>: \t{user["gender"]} \n\n"
            f"<b>🎂 \tAge</b>: \t{user["dob"]} \n\n"
            f"<b>🌐 \tCountry</b>: \t{user["country"]} \n\n"
            f"<b>🏙️ \tCity</b>: \t{user["city"]} \n\n"
            f"<b>📧 \tEmail</b>: \t{user["email"]} \n\n"
            f"<b>📞 \tPhone</b>: \t{user["phone"]} \n\n",
            parse_mode="HTML",
            message_thread_id=topic_id,
        )


def is_valid_email(email):
    """
    Validate an email address.

    Args:
        email (str): The email address to validate.

    Returns:
        bool: True if the email address is valid, False otherwise.
    """

    # regex pattern for validating an email
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def format_date(date):
    """
    Format a date object into a human-readable string.

    Args:
        date (datetime.date): The date object to format.

    Returns:
        str: The formatted date string in the format "Month Day, Year" (e.g., "January 01, 2023").
    """

    return date.strftime("%B %d, %Y")


def convert_datetime(obj):
    """
    Convert a datetime object to its ISO 8601 string representation.

    Args:
        obj (Any): The object to convert. Expected to be of type `datetime.datetime`.

    Returns:
        str: The ISO 8601 formatted string if the object is a datetime instance.

    Raises:
        TypeError: If the object is not of type `datetime.datetime`.
    """

    if isinstance(obj, datetime.datetime):
        return obj.isoformat()  # or obj.strftime('%Y-%m-%d %H:%M:%S') for a d/t format
    raise TypeError("Type not serializable")


def is_isalnum_w_space(s):
    """
    Check if a given string contains only alphanumeric characters and spaces.

    Args:
        s (str): The string to check.

    Returns:
        bool: True if the string contains only alphanumeric characters and spaces, False otherwise.
    """

    if not s:
        return False

    return all(char.isalnum() or char.isspace() for char in s)


def is_valid_date_format(date_string):
    # Regular expression pattern for YYYY-M-D or YYYY-MM-DD
    pattern = r"^\d{4}-(\d{1,2})-(\d{1,2})$"

    # Check if the date string matches the pattern
    match = re.match(pattern, date_string)
    if not match:
        return False

    # Extract month and day from the match
    month = int(match.group(1))
    day = int(match.group(2))

    # Check if month is valid
    if month < 1 or month > 12:
        return False

    # Check if day is valid based on the month
    if day < 1 or day > 31:
        return False

    # Check for months with specific day limits
    if month in {4, 6, 9, 11} and day > 30:
        return False
    if month == 2:
        # Check for leap year
        year = int(date_string[:4])
        if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
            if day > 29:  # Leap year
                return False
        else:
            if day > 28:  # Non-leap year
                return False

    return True
