from psycopg2 import DatabaseError
from requests.exceptions import ConnectionError as RequestsConnectionError
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    filters,
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
)

from applicants.handlers.general import start_command
from applicants.states.all import (
    CHOOSE_FIELD,
    EDIT_CITY,
    EDIT_COUNTRY,
    EDIT_DOB,
    EDIT_EMAIL,
    EDIT_GENDER,
    EDIT_NAME,
    EDIT_PHONE,
    EDIT_USERNAME,
)
from utils.db import execute_query, redis_client
from utils.helpers import get_all_cities, get_applicant, is_valid_email


async def applicant_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Display the applicant's profile information and provide an inline button to edit it.
    If the message is a callback query, edit the message with the applicant's profile.
    Otherwise, send a new message with the applicant's profile.
    If the applicant is not found, start the conversation with the start handler.
    """
    applicant = get_applicant(update)

    if not applicant:
        await start_command(update, context)
        return

    keyboard = [[InlineKeyboardButton("Edit Profile", callback_data="edit_profile")]]
    profile_info = (
        f"<b>My Profile</b> \n\n"
        f"<b>👤 \tName</b>: \t{(applicant["name"].split()[0]).capitalize()} {(applicant["name"].split()[1]).capitalize() if len(applicant["name"].split()) > 1 else ''} \n\n"
        f"<b>\t&#64; \t\tUsername</b>: \t{applicant["username"]} \n\n"
        f"<b>👫 \tGender</b>: \t{applicant["gender"]} \n\n"
        f"<b>🎂 \tAge</b>: \t{applicant["dob"]} \n\n"
        f"<b>🌐 \tCountry</b>: \t{applicant["country"]} \n\n"
        f"<b>🏙️ \tCity</b>: \t{applicant["city"]} \n\n"
        f"<b>📧 \tEmail</b>: \t{applicant["email"]} \n\n"
        f"<b>📞 \tPhone</b>: \t{applicant["phone"]} \n\n"
    )

    if update.callback_query:
        query = update.callback_query
        await query.edit_message_text(
            text=profile_info,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text(
            text=profile_info,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )


async def edit_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the 'Edit Profile' button and displays inline buttons to edit each profile field.
    When the user clicks on the 'Edit Profile' button, this function is called, and it edits the message with the inline buttons.
    """

    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton("Edit Name", callback_data="edit_name"),
            InlineKeyboardButton("Update Username", callback_data="update_username"),
        ],
        [
            InlineKeyboardButton("Edit Gender", callback_data="edit_gender"),
            InlineKeyboardButton("Edit Age", callback_data="edit_dob"),
        ],
        [
            InlineKeyboardButton("Edit Country", callback_data="edit_country"),
            InlineKeyboardButton("Edit City", callback_data="edit_city"),
        ],
        [
            InlineKeyboardButton("Edit Email", callback_data="edit_email"),
            InlineKeyboardButton("Edit Phone", callback_data="edit_phone"),
        ],
        [InlineKeyboardButton("Done", callback_data="done_profile")],
    ]

    await query.edit_message_reply_markup(
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def done_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the completion of the profile editing process.

    This function is triggered when the user indicates they are done editing their profile.
    It updates the message to display an inline button that allows the user to return to the
    profile editing interface if they wish to make further changes.

    Args:
        update (Update): The update object that contains the user's callback query.
    """

    query = update.callback_query
    await query.answer()

    keyboard = [[InlineKeyboardButton("Edit Profile", callback_data="edit_profile")]]

    await query.edit_message_reply_markup(
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def cancel_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles user cancellation of the profile editing process.

    This function is triggered when the user wants to stop editing their profile.
    It sends a message to the user to indicate that the profile update has been canceled
    and provides an inline button to return to the profile editing interface if they wish to make further changes.

    Args:
        update (Update): The update object that contains the user's message.

    Returns:
        Constant: A constant representing the next state of the conversation, which is the end of the conversation.
    """

    keyboard = [
        [InlineKeyboardButton("Back to Profile", callback_data="applicant_profile")]
    ]

    await update.message.reply_text(
        "Profile update canceled",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return ConversationHandler.END


async def choose_field(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles user selection for editing different profile fields via callback data.

    Depending on the user's choice, sends a prompt message to the user to update the selected field.
    Options include editing name, username, gender, age, country, city, email, or phone number.
    Displays appropriate instructions or options for the user to proceed with the update.

    Args:
        update (Update): The update object that contains the user's callback query.
        context (ContextTypes.DEFAULT_TYPE): The context object for storing user data during the conversation.

    Returns:
        Constant: A constant representing the next state of the conversation, specific to the chosen field.
    """

    query = update.callback_query
    await query.answer()
    choice = query.data

    next_state = None

    if choice == "edit_name":
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="Please enter your new name (First and Last) \n\n<i>* Type /cancel to abort editing</i>",
            parse_mode="HTML",
        )
        next_state = EDIT_NAME
    elif choice == "edit_username":
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="<i>* Updating your username...</i>",
            parse_mode="HTML",
        )
        next_state = EDIT_USERNAME
        # return edit_username(update, context)
    elif choice == "edit_gender":
        keyboard = [
            [
                InlineKeyboardButton("Male", callback_data="Male"),
                InlineKeyboardButton("Female", callback_data="Female"),
            ],
        ]

        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="Please choose your gender \n\n<i>* Type /cancel to abort editing</i>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        next_state = EDIT_GENDER
    elif choice == "edit_dob":
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="Please enter your age between 10 and 100 \n\n<i>* Type /cancel to abort editing</i>",
            parse_mode="HTML",
        )
        next_state = EDIT_DOB
    elif choice == "edit_country":
        keyboard = [[InlineKeyboardButton("Ethiopia", callback_data="Ethiopia")]]

        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="Please select your country \n\n<i>* Type /cancel to abort editing</i>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        next_state = EDIT_COUNTRY
    elif choice == "edit_city":
        keyboard = get_all_cities()

        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="Please select your city \n\n<i>* Type /cancel to abort editing</i>",
            reply_markup=keyboard,
            parse_mode="HTML",
        )
        next_state = EDIT_CITY
    elif choice == "edit_email":
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="Please enter your email address \n\n<i>* Type /cancel to abort editing</i>",
            parse_mode="HTML",
        )
        next_state = EDIT_EMAIL
    elif choice == "edit_phone":
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="Please enter your phone number \n\n<i>* Type /cancel to abort editing</i>",
            parse_mode="HTML",
        )
        next_state = EDIT_PHONE
    else:
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="Invalid choice, please select again",
            parse_mode="HTML",
        )
        next_state = CHOOSE_FIELD

    return next_state


async def edit_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Updates the user's name in the database based on the input provided in the update message.

    Args:
        update (Update): Incoming update instance containing the message and user details.

    Returns:
        int: The constant END from ConversationHandler to indicate that the conversation should end.

    The function strips the text from the update message to get the new name, retrieves the user's telegram ID,
    and updates the user's name in the database where the telegram ID and role ID match.
    It then sends a confirmation message to the user with an inline button to return to the profile.
    """

    name = update.message.text.strip()
    telegram_id = update.effective_user.id

    response = execute_query(
        "UPDATE users SET name = %s WHERE telegram_id = %s AND role_id = 1",
        (name, telegram_id),
    )
    redis_client.delete(f"applicant:{telegram_id}")
    print(f"\n === \n response : {response} \n === \n")

    keyboard = [
        [InlineKeyboardButton("Back to Profile", callback_data="applicant_profile")]
    ]

    await update.message.reply_text(
        text="Name updated successfully!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )
    return ConversationHandler.END


async def update_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Updates the user's username in the database based on the input provided in the update message.

    Args:
        update (Update): Incoming update instance containing the message and user details.
        context (ContextTypes.DEFAULT_TYPE): The context object for the conversation.

    Returns:
        int: The constant END from ConversationHandler to indicate that the conversation should end.

    The function retrieves the user's telegram ID and username, updates the user's username in the database
    where the telegram ID and role ID match, and sends a confirmation message to the user with an inline button
    to return to the profile.
    """

    telegram_id = update.effective_user.id
    username = update.effective_user.username
    query = update.callback_query
    await query.answer()

    response = execute_query(
        "UPDATE users SET username = %s WHERE telegram_id = %s AND role_id = 1",
        (username, telegram_id),
    )
    redis_client.delete(f"applicant:{telegram_id}")
    print(f"\n === \n response : {response} \n === \n")

    keyboard = [
        [InlineKeyboardButton("Back to Profile", callback_data="applicant_profile")]
    ]

    await context.bot.send_message(
        chat_id=query.from_user.id,
        text="Username updated successfully!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )
    return ConversationHandler.END


async def edit_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Updates the user's gender in the database based on the callback data provided in the update object.

    Args:
        update (Update): Incoming update instance containing the callback query and user details.

    Returns:
        int: The constant END from ConversationHandler to indicate that the conversation should end.

    The function retrieves the user's telegram ID and gender from the callback data, updates the user's gender in the database
    where the telegram ID and role ID match, and sends a confirmation message to the user with an inline button
    to return to the profile.
    """

    try:
        query = update.callback_query
        await query.answer()
        telegram_id = update.effective_user.id

        response = execute_query(
            "UPDATE users SET gender = %s WHERE telegram_id = %s AND role_id = 1",
            (query.data, telegram_id),
        )
        redis_client.delete(f"applicant:{telegram_id}")
        print(f"\n === \n response : {response} \n === \n")

        keyboard = [
            [InlineKeyboardButton("Back to Profile", callback_data="applicant_profile")]
        ]

        await query.edit_message_text(
            text="Gender updated successfully!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return ConversationHandler.END
    except DatabaseError as e:
        await query.edit_message_text(
            "An error occurred while updating your gender. Please try again."
        )
        print(f"Error in edit_gender: {e}")
        return ConversationHandler.END
    except RequestsConnectionError as e:
        await query.edit_message_text(
            "A network error occurred while updating your gender. Please try again."
        )
        print(f"Error in edit_gender: {e}")
        return ConversationHandler.END
    except Exception as e:
        await query.edit_message_text(
            "An error occurred while updating your gender. Please try again."
        )
        print(f"Error in edit_gender: {e}")
        return ConversationHandler.END


async def edit_dob(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Updates the user's date of birth (age) in the database based on the input provided in the update message.

    The function checks if the input is a valid age between 10 and 100. If valid, it updates the user's age
    in the database and sends a confirmation message. If the age is out of range or invalid, it prompts the
    user to enter a valid age.

    Args:
        update (Update): Incoming update instance containing the message and user details.

    Returns:
        int: The next state of the conversation, either ConversationHandler.END or EDIT_DOB for retry.
    """

    try:
        dob = update.message.text.strip()

        if dob.isdigit():
            # Check if the input is a number between 10 and 100
            age = int(dob)
            if 10 <= age <= 100:
                keyboard = [
                    [
                        InlineKeyboardButton(
                            "Back to Profile", callback_data="applicant_profile"
                        )
                    ]
                ]

                telegram_id = update.effective_user.id

                response = execute_query(
                    "UPDATE users SET dob = %s WHERE telegram_id = %s AND role_id = 1",
                    (dob, telegram_id),
                )
                redis_client.delete(f"applicant:{telegram_id}")
                print(f"\n === \n response : {response} \n === \n")

                await update.message.reply_text(
                    text="Age updated successfully!",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="HTML",
                )
                return ConversationHandler.END
            else:
                await update.message.reply_text(
                    "<i>* Age out of range</i>\n\nPlease enter your age between 10 and 100 \n\n<i>* Type /cancel to abort editing</i>",
                    parse_mode="HTML",
                )
                return EDIT_DOB
        else:
            await update.message.reply_text(
                "<i>* Invalid age.</i>\n\nPlease enter your age between 10 and 100 \n\n<i>* Type /cancel to abort editing</i>",
                parse_mode="HTML",
            )
            return EDIT_DOB
    except Exception as e:
        await update.message.reply_text(
            "An error occurred while updating your age. Please try again."
        )
        print(f"Error in edit_dob: {e}")
        return ConversationHandler.END


async def edit_country(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Updates the user's country in the database based on the callback data provided in the update object.

    Args:
        update (Update): Incoming update instance containing the callback query and user details.

    Returns:
        int: The constant END from ConversationHandler to indicate that the conversation should end.

    The function retrieves the user's telegram ID and country from the callback data, updates the user's country in the database
    where the telegram ID and role ID match, and sends a confirmation message to the user with an inline button
    to return to the profile.
    """

    try:
        query = update.callback_query
        await query.answer()
        telegram_id = update.effective_user.id

        response = execute_query(
            "UPDATE users SET country = %s WHERE telegram_id = %s AND role_id = 1",
            (query.data, telegram_id),
        )
        redis_client.delete(f"applicant:{telegram_id}")
        print(f"\n === \n response : {response} \n === \n")

        keyboard = [
            [InlineKeyboardButton("Back to Profile", callback_data="applicant_profile")]
        ]

        await query.edit_message_text(
            text="Country updated successfully!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return ConversationHandler.END
    except Exception as e:
        await query.edit_message_text(
            "An error occurred while updating your country. Please try again."
        )
        print(f"Error in edit_country: {e}")
        return ConversationHandler.END


async def edit_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Updates the user's city in the database based on the callback data provided in the update object.

    Args:
        update (Update): Incoming update instance containing the callback query and user details.

    Returns:
        int: The constant END from ConversationHandler to indicate that the conversation should end.

    The function retrieves the user's telegram ID and city from the callback data, updates the user's city in the database
    where the telegram ID and role ID match, and sends a confirmation message to the user with an inline button
    to return to the profile.
    """

    try:
        query = update.callback_query
        await query.answer()
        telegram_id = update.effective_user.id

        response = execute_query(
            "UPDATE users SET city = %s WHERE telegram_id = %s AND role_id = 1",
            (query.data, telegram_id),
        )
        redis_client.delete(f"applicant:{telegram_id}")
        print(f"\n === \n response : {response} \n === \n")

        keyboard = [
            [InlineKeyboardButton("Back to Profile", callback_data="applicant_profile")]
        ]

        await query.edit_message_text(
            text="City updated successfully!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return ConversationHandler.END
    except Exception as e:
        await query.edit_message_text(
            "An error occurred while saving your city. Please try again."
        )
        print(f"Error in edit_city: {e}")
        return ConversationHandler.END


async def edit_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Updates the user's email in the database based on the input provided in the update message.

    Args:
        update (Update): Incoming update instance containing the message and user details.

    Returns:
        int: The constant END from ConversationHandler to indicate that the conversation should end.

    The function validates the email format, retrieves the user's telegram ID, and updates the user's email in the database
    where the telegram ID and role ID match. If the email format is invalid, prompts the user to enter a valid email.
    Sends a confirmation message to the user with an inline button to return to the profile.
    Handles and logs exceptions that may occur during the update process.
    """

    try:
        email = update.message.text.strip()
        telegram_id = update.effective_user.id

        if not is_valid_email(email):
            await update.message.reply_text(
                "<i>* Invalid email format.</i>\n\nPlease enter your email address \n\n<i>* Type /cancel to abort editing</i>",
                parse_mode="HTML",
            )
            return EDIT_EMAIL

        response = execute_query(
            "UPDATE users SET email = %s WHERE telegram_id = %s AND role_id = 1",
            (email, telegram_id),
        )
        redis_client.delete(f"applicant:{telegram_id}")
        print(f"\n === \n response : {response} \n === \n")

        keyboard = [
            [InlineKeyboardButton("Back to Profile", callback_data="applicant_profile")]
        ]

        await update.message.reply_text(
            text="Email updated successfully!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(
            "An error occurred while updating your email address. Please try again."
        )
        print(f"Error in edit_email: {e}")
        return ConversationHandler.END


async def edit_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Updates the user's phone number in the database based on the input provided in the update message.

    Args:
        update (Update): Incoming update instance containing the message and user details.

    Returns:
        int: The next state of the conversation, either ConversationHandler.END or EDIT_PHONE for retry.

    The function strips the text from the update message to get the new phone number, retrieves the user's telegram ID,
    and updates the user's phone number in the database where the telegram ID and role ID match. It sends a confirmation
    message to the user with an inline button to return to the profile. If the phone number is invalid, it prompts
    the user to enter a valid phone number. Handles and logs exceptions that may occur during the update process.
    """

    try:
        phone = update.message.text.strip()
        telegram_id = update.effective_user.id

        if not phone.isdigit() or len(phone) < 9:  # Basic validation for phone numbers
            await update.message.reply_text(
                "<i>* Invalid phone number.</i>\n\nPlease enter your phone number \n\n<i>* Type /cancel to abort editing</i>",
                parse_mode="HTML",
            )
            return EDIT_PHONE

        response = execute_query(
            "UPDATE users SET phone = %s WHERE telegram_id = %s AND role_id = 1",
            (phone, telegram_id),
        )
        redis_client.delete(f"applicant:{telegram_id}")
        print(f"\n === \n response : {response} \n === \n")

        keyboard = [
            [InlineKeyboardButton("Back to Profile", callback_data="applicant_profile")]
        ]

        await update.message.reply_text(
            text="Email updated successfully!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(
            "An error occurred while updating your phone number. Please try again."
        )
        print(f"Error in edit_phone: {e}")
        return ConversationHandler.END


profile_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(choose_field, pattern="^edit_.*")],
    states={
        CHOOSE_FIELD: [CallbackQueryHandler(choose_field, pattern="^edit_.*")],
        EDIT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_name)],
        EDIT_USERNAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, update_username)
        ],
        EDIT_GENDER: [CallbackQueryHandler(edit_gender)],
        EDIT_DOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_dob)],
        EDIT_COUNTRY: [CallbackQueryHandler(edit_country)],
        EDIT_CITY: [CallbackQueryHandler(edit_city)],
        EDIT_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_email)],
        EDIT_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_phone)],
    },
    fallbacks=[CommandHandler("cancel", cancel_profile)],
)
