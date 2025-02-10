import os
import re
import json
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
    update: Update,
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
    redis_client.delete(telegram_id)
    cached_applicant = redis_client.get(telegram_id)

    if not cached_applicant:
        print(" === \n Cache miss! \n ===")
        applicant = execute_query(
            # "SELECT user_id, telegram_id, role_id, first_name FROM users WHERE telegram_id = %s AND role_id = %s",
            "SELECT * FROM users WHERE telegram_id = %s AND role_id = %s",
            (telegram_id, ROLE_APPLICANT),
        )
        if isinstance(applicant) == list:
            redis_client.set(telegram_id, json.dumps(applicant[0]), ex=3600)
            applicant = applicant[0]
    else:
        print(" === \n Cache hit! \n ===")
        applicant = list(json.loads(cached_applicant))

    if not applicant:
        return None

    return applicant


# def register_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     tg_user = update.effective_user
#     last_name = update.effective_user.last_name if update._effective_user.last_name else None
#     username = update.effective_user.username if update._effective_user.username else None

#     return execute_query("INSERT INTO users (telegram_id, first_name, last_name, username) VALUES (%s, %s, %s, %s)", (tg_user.id, tg_user.first_name, last_name, username))


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
                callback_data=f"view_jobseeker_{user_data['telegram_id']}",
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


def is_valid_email(email):
    # regex pattern for validating an email
    """
    Validate an email address.

    The regex pattern used to validate the email is taken from
    https://emailregex.com/. It matches most common email address formats.

    Args:
        email (str): The email address to validate.

    Returns:
        bool: True if the email address is valid, False otherwise.
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))
