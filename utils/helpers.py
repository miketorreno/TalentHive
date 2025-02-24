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
    ROLE_APPLICANT,
    GROUP_TOPIC_NEW_APPLICANT_REGISTRATION_ID,
)
from utils.db import execute_query, redis_client


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
        print("\n === \n Cache miss! \n === \n")
        applicant = execute_query(
            "SELECT user_id, telegram_id, role_id, name, username, email, phone, gender, dob, country, city, education, experience, cv, skills, portfolios, subscribed_alerts, preferences FROM users WHERE telegram_id = %s AND role_id = %s",
            (telegram_id, ROLE_APPLICANT),
        )
        print(f" === \n response : {applicant} \n ===")
        if isinstance(applicant, list) and len(applicant) > 0:
            applicant = applicant[0]
            redis_client.set(f"applicant:{telegram_id}", json.dumps(applicant), ex=3600)
    else:
        print("\n === \n Cache hit! \n === \n")
        applicant = json.loads(cached_applicant)

    if not applicant:
        return None

    return applicant


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
    return job[0]


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
            text=f"<b>User Profile</b>\n\n"
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
