from typing import Any

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import (
    filters,
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
)
from employers.states.all import (
    REGISTER,
    CONFIRMATION,
    REGISTER_CITY,
    REGISTER_DOB,
    REGISTER_EMAIL,
    REGISTER_FIRSTNAME,
    REGISTER_LASTNAME,
    REGISTER_PHONE,
    REGISTER_GENDER,
    REGISTER_COUNTRY,
)
from utils.constants import ROLE_EMPLOYER
from utils.db import execute_query
from utils.helpers import get_all_cities, is_valid_email


async def onboarding_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Starts the onboarding process.

    This function is called when the user starts the conversation.
    It will send a message asking the user to enter their first name.

    If an error occurs, it will reply to the user with an error message
    and end the conversation.

    Returns:
        int: The next state of the conversation, which is the state of
            entering the first name.
    """

    try:
        query = update.callback_query
        await query.answer()

        await query.edit_message_text(
            text="Please enter your first name", parse_mode="HTML"
        )

        return REGISTER_FIRSTNAME
    except Exception as e:
        await query.edit_message_text(
            "An error occurred registering. Please try again."
        )
        # Optionally log the error for debugging
        print(f"Error in onboarding_start: {e}")
        return ConversationHandler.END


async def register_firstname(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int | Any:
    """
    Registers the user's first name.

    This function is called after the user has entered their first name.
    It will check if the input is valid (only alphabetic characters).
    If the input is valid, it will save the first name to the user data and
    ask the user to enter their last name.
    If the input is invalid, it will reply to the user with an error message
    and ask them to enter their first name again.
    If an error occurs, it will reply to the user with an error message
    and end the conversation.

    Returns:
        int: The next state of the conversation, which is the state of
            entering the last name if the input is valid, or the state of
            entering the first name if the input is invalid.
    """

    try:
        firstname = update.message.text.strip()

        if not firstname.isalpha():
            await update.message.reply_text(
                "<i>* First name should only contain alphabetic characters.</i>\n\nPlease enter your first name",
                parse_mode="HTML",
            )
            return REGISTER_FIRSTNAME

        context.user_data["firstname"] = firstname
        await update.message.reply_text("Please enter your last name")
        return REGISTER_LASTNAME
    except Exception as e:
        await update.message.reply_text(
            "An error occurred while saving your first name. Please try again."
        )
        print(f"Error in register_firstname: {e}")
        return ConversationHandler.END


async def register_lastname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Registers the user's last name.

    This function is called after the user has entered their last name.
    It validates that the input contains only alphabetic characters. If valid,
    it saves the last name to the user data and prompts the user to enter their email
    address. If invalid, it replies with an error message and prompts the user to
    enter their last name again.

    If an error occurs during the process, it replies with an error message and
    ends the conversation.

    Returns:
        int: The next state of the conversation, which is entering the email
            address if the input is valid, or re-entering the last name if invalid.
    """

    try:
        lastname = update.message.text.strip()

        if not lastname.isalpha():
            await update.message.reply_text(
                "<i>* Last name should only contain alphabetic characters.</i>\n\nPlease enter your last name",
                parse_mode="HTML",
            )
            return REGISTER_LASTNAME

        context.user_data["lastname"] = lastname
        await update.message.reply_text("Please enter your email address")
        return REGISTER_EMAIL
    except Exception as e:
        await update.message.reply_text(
            "An error occurred while saving your last name. Please try again."
        )
        print(f"Error in register_lastname: {e}")
        return ConversationHandler.END


async def register_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Registers the user's email address.

    This function is called after the user has entered their email address.
    It validates the email format using the `is_valid_email` function. If the email
    is valid, it saves the email to the user data and prompts the user to enter
    their phone number. If the email is invalid, it replies with an error message
    and prompts the user to re-enter their email address.

    If an error occurs during the process, it replies with an error message and
    ends the conversation.

    Returns:
        int: The next state of the conversation, which is entering the phone
            number if the email is valid, or re-entering the email if invalid.
    """

    try:
        email = update.message.text.strip()

        # if "@" not in email or "." not in email:
        if not is_valid_email(email):
            await update.message.reply_text(
                "<i>* Invalid email format.</i>\n\nPlease enter your email address",
                parse_mode="HTML",
            )
            return REGISTER_EMAIL

        context.user_data["email"] = email
        await update.message.reply_text("Please enter your phone number")
        return REGISTER_PHONE
    except Exception as e:
        await update.message.reply_text(
            "An error occurred while saving your email address. Please try again."
        )
        print(f"Error in register_email: {e}")
        return ConversationHandler.END


async def register_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Registers the user's phone number.

    This function is called after the user has entered their phone number.
    It validates that the phone number contains only digits and has a minimum
    length of 9 characters. If the phone number is valid, it saves the phone
    number to the user data and prompts the user to choose their gender. If the
    phone number is invalid, it replies with an error message and prompts the
    user to re-enter their phone number.

    If an error occurs during the process, it replies with an error message and
    ends the conversation.

    Returns:
        int: The next state of the conversation, which is entering the gender
            if the phone number is valid, or re-entering the phone number if
            invalid.
    """

    try:
        phone = update.message.text.strip()

        if not phone.isdigit() or len(phone) < 9:  # Basic validation for phone numbers
            await update.message.reply_text(
                "<i>* Invalid phone number.</i>\n\nPlease enter your phone number",
                parse_mode="HTML",
            )
            return REGISTER_PHONE

        context.user_data["phone"] = phone
        keyboard = [
            [
                InlineKeyboardButton("Male", callback_data="Male"),
                InlineKeyboardButton("Female", callback_data="Female"),
            ],
            [InlineKeyboardButton("Skip", callback_data="skip")],
        ]
        await update.message.reply_text(
            "Please choose your gender", reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return REGISTER_GENDER
    except Exception as e:
        await update.message.reply_text(
            "An error occurred while saving your phone number. Please try again."
        )
        print(f"Error in register_phone: {e}")
        return ConversationHandler.END


async def register_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Registers the user's gender.

    This function is called after the user has selected their gender.
    It will save the gender to the user data and ask the user to enter
    their age.

    If an error occurs during the process, it will reply with an error message
    and end the conversation.

    Returns:
        int: The next state of the conversation, which is entering the age
            if the input is valid, or the state of entering the gender
            if the input is invalid.
    """

    try:
        query = update.callback_query
        await query.answer()

        context.user_data["gender"] = query.data if query.data != "skip" else None
        await query.edit_message_text("Please enter your age between 10 and 100")
        return REGISTER_DOB
    except Exception as e:
        await query.edit_message_text(
            "An error occurred while saving your gender. Please try again."
        )
        print(f"Error in register_gender: {e}")
        return ConversationHandler.END


async def register_dob(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Registers the user's date of birth.

    This function is called after the user has entered their age.
    It validates that the input contains only numbers and is between 10 and 100.
    If valid, it saves the age to the user data and prompts the user to select
    their city. If invalid, it replies with an error message and prompts the user
    to enter their age again.

    If an error occurs during the process, it replies with an error message and
    ends the conversation.

    Returns:
        int: The next state of the conversation, which is selecting the city
            if the input is valid, or re-entering the age if invalid.
    """

    try:
        dob = update.message.text.strip()

        if dob.isdigit():
            # Check if the input is a number between 10 and 100
            age = int(dob)
            if 10 <= age <= 100:
                context.user_data["dob"] = age
            else:
                await update.message.reply_text(
                    "<i>* age out of range</i>\n\nPlease enter your age between 10 and 100",
                    parse_mode="HTML",
                )
                return REGISTER_DOB
        else:
            await update.message.reply_text(
                "<i>* invalid age</i>\n\nPlease enter your age between 10 and 100",
                parse_mode="HTML",
            )
            return REGISTER_DOB

        # keyboard = [
        #     [InlineKeyboardButton("Ethiopia", callback_data='Ethiopia')]
        # ]
        # await update.message.reply_text(
        #     "Please select your country",
        #     reply_markup=InlineKeyboardMarkup(keyboard)
        # )
        # return REGISTER_COUNTRY

        keyboard = get_all_cities()
        context.user_data["country"] = "Ethiopia"
        await update.message.reply_text(
            "Please select your city", reply_markup=keyboard
        )
        return REGISTER_CITY
    except Exception as e:
        await update.message.reply_text(
            "An error occurred while saving your age. Please try again."
        )
        print(f"Error in register_dob: {e}")
        return ConversationHandler.END


async def register_country(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Registers the user's country.

    This function is called after the user has selected their country.
    It saves the country to the user data and prompts the user to select
    their city. If an error occurs during the process, it replies with an error
    message and prompts the user to select their country again.

    Returns:
        int: The next state of the conversation, which is selecting the city if
            the input is valid, or re-selecting the country if invalid.
    """

    try:
        query = update.callback_query
        await query.answer()
        country = query.data

        keyboard = get_all_cities()
        context.user_data["country"] = country
        await query.edit_message_text("Please select your city", reply_markup=keyboard)
        return REGISTER_CITY
    except Exception as e:
        await query.edit_message_text(
            "An error occurred while saving your country. Please try again."
        )
        print(f"Error in register_country: {e}")
        return ConversationHandler.END


async def register_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Registers the user's city.

    This function is called after the user has selected their city.
    It saves the city to the user data, displays a summary of the user's
    information, and prompts the user to confirm their information. If an
    error occurs during the process, it replies with an error message and
    prompts the user to select their city again.

    Returns:
        int: The next state of the conversation, which is confirming the
            information if the input is valid, or re-selecting the city if
            invalid.
    """

    try:
        query = update.callback_query
        await query.answer()
        city = query.data

        context.user_data["city"] = city
        user_data = context.user_data
        keyboard = [
            [InlineKeyboardButton("Confirm ✅", callback_data="confirm")],
            [InlineKeyboardButton("Start Over", callback_data="restart")],
        ]
        await query.edit_message_text(
            f"<b>ACCOUNT INFORMATION</b>\n\n"
            f"<b>Name</b>: {(user_data['firstname']).capitalize()} {(user_data['lastname']).capitalize()}\n\n"
            f"<b>Email</b>: {user_data['email']}\n\n"
            f"<b>Phone</b>: {user_data['phone']}\n\n"
            f"<b>Gender</b>: {user_data.get('gender', '')}\n\n"
            f"<b>Age</b>: {user_data.get('dob', '')}\n\n"
            f"<b>Country</b>: {user_data['country']}\n\n"
            f"<b>City</b>: {user_data['city']}\n\n\n"
            f"<b>Do you confirm this information?</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return CONFIRMATION
    except Exception as e:
        await query.edit_message_text(
            "An error occurred while saving your city. Please try again."
        )
        print(f"Error in register_city: {e}")
        return ConversationHandler.END


async def confirm_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Confirms the user's registration information and saves it to the database.

    If the user confirms their information, it saves the information to the
    database and sends a welcome message with the available commands. If the user
    decides to restart, it displays a message prompting the user to start again.

    Args:
        update (Update): The update containing the callback query.
        context (ContextTypes.DEFAULT_TYPE): The context containing the user data.

    Returns:
        int: The next state of the conversation, which is either the end of the
            conversation if the input is valid, or re-selecting the city if
            invalid.
    """

    try:
        query = update.callback_query
        await query.answer()

        if query.data == "confirm":
            user_data = context.user_data
            user_data["telegram_id"] = update.effective_user.id
            username = update.effective_user.username

            response = execute_query(
                "INSERT INTO users (telegram_id, role_id, name, username, email, phone, gender, dob, country, city) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    user_data["telegram_id"],
                    ROLE_EMPLOYER,
                    f"{user_data['firstname']} {user_data['lastname']}",
                    username,
                    user_data["email"],
                    user_data["phone"],
                    user_data.get("gender"),
                    user_data.get("dob"),
                    user_data["country"],
                    user_data["city"],
                ),
            )

            if response:
                await query.edit_message_text(
                    "Registered successfully \t 🎉",
                    parse_mode="HTML",
                )

            # TODO: implement a better way to handle redirect to `start`
            # await start_command(update, context)

            keyboard = [
                ["Post a Job", "My Job Posts"],
                ["My Profile", "My Companies"],
                ["Help"],
                # ["My Companies", "Notifications"],
                # ["My Profile", "Help"],
            ]
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"<b>Hello {user_data['firstname'].capitalize()} 👋\t Welcome to HulumJobs!</b> \n\n"
                "<b>🔊 \tPost a Job</b>:\t find the right candidates for you \n\n"
                "<b>📑 \tMy Job posts</b>:\t view & manage your job posts \n\n"
                "<b>🏢 \tMy Companies</b>:\t add & manage your companies \n\n"
                # "<b>🔔 \tNotifications</b>:\t customize notifications you wanna receive \n\n"
                "<b>👤 \tMy Profile</b>:\t manage your profile \n\n"
                "<b>❓ \tHelp</b>:\t show help message \n\n",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
                parse_mode="HTML",
            )

            # Notify the group about the new registration
            # await notify_group_on_registration(update, context, user_data)

            # return REGISTER_COMPLETE
            # await update.message.reply_text("/start")

        elif query.data == "restart":
            await query.edit_message_text(
                "Let's start over. Use /start to begin again."
            )
        return ConversationHandler.END
    except Exception as e:
        await query.edit_message_text(
            "An error occurred during confirmation. Please try again."
        )
        print(f"Error in confirm_registration: {e}")
        return ConversationHandler.END


async def onboarding_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Cancels the onboarding process and sends a message to the user.

    Sends a message to the user with instructions on how to restart the
    onboarding process, and then ends the conversation.

    Args:
        update (Update): The update that triggered this function.

    Returns:
        int: The state to transition to, which is ConversationHandler.END.
    """

    await update.message.reply_text("Registration canceled. Type /start to restart.")
    return ConversationHandler.END


onboarding_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(onboarding_start, "register")],
    states={
        REGISTER: [CallbackQueryHandler(onboarding_start)],
        # REGISTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)],
        REGISTER_FIRSTNAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, register_firstname)
        ],
        REGISTER_LASTNAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, register_lastname)
        ],
        REGISTER_EMAIL: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, register_email)
        ],
        REGISTER_PHONE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, register_phone)
        ],
        REGISTER_GENDER: [CallbackQueryHandler(register_gender)],
        REGISTER_DOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_dob)],
        REGISTER_COUNTRY: [CallbackQueryHandler(register_country)],
        REGISTER_CITY: [CallbackQueryHandler(register_city)],
        CONFIRMATION: [CallbackQueryHandler(confirm_registration)],
    },
    fallbacks=[CommandHandler("cancel", onboarding_cancel)],
)
