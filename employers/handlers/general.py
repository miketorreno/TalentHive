from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes, ConversationHandler

from employers.states.all import REGISTER
from utils.helpers import get_employer


async def start_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int | None:
    """
    Handles the initial interaction with the user when they start the bot.

    Depending on the user's registration status, it either prompts them to
    register or provides options to post a job, view job posts, manage
    their profile, or track their applications.

    Args:
        update (Update): The update object from the Telegram API.
        context (ContextTypes.DEFAULT_TYPE): The context object from the
            Telegram API, containing the bot's data and state.

    Returns:
        REGISTER state if the user is not registered, otherwise no explicit
        return value as the function interacts with the user via messages.
    """

    employer = get_employer(update, context)

    if not employer:
        keyboard = [[InlineKeyboardButton("Register", callback_data="register")]]
        welcome_msg = (
            "<b>Hello there 👋\t Welcome to HulumJobs! </b>\n\n"
            "Let’s get started, Please click the button below to register."
        )

        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=welcome_msg,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML",
            )
        else:
            await update.message.reply_text(
                text=welcome_msg,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML",
            )
        return REGISTER

    keyboard = [
        ["Post a Job", "My Job Posts"],
        ["My Profile", "My Companies"],
        ["Help"],
        # ["My Companies", "Notifications"],
        # ["My Profile", "Help"],
    ]
    welcome_msg = (
        f"<b>Hello {(employer["name"].split()[0]).capitalize()} 👋\t Welcome to HulumJobs!</b> \n\n"
        "<b>🔊 \tPost a Job</b>:\t find the right candidates for you \n\n"
        "<b>📑 \tMy Job posts</b>:\t view & manage your job posts \n\n"
        "<b>🏢 \tMy Companies</b>:\t add & manage your companies \n\n"
        # "<b>🔔 \tNotifications</b>:\t customize notifications you wanna receive \n\n"
        "<b>👤 \tMy Profile</b>:\t manage your profile \n\n"
        "<b>❓ \tHelp</b>:\t show help message \n\n"
    )

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=welcome_msg,
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text(
            text=welcome_msg,
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
            parse_mode="HTML",
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Shows the help message when the user types /help or clicks the Help button.

    Args:
        update (Update): The update object from the Telegram API.
        context (ContextTypes.DEFAULT_TYPE): The context object from the Telegram API, containing the bot's data and state.
    """

    help_msg = (
        "<b>Help</b>\n\n"
        "<b>Post a Job</b> - find the right candidates for you \n\n"
        "<b>My Job posts</b> - view & manage your job posts \n\n"
        "<b>My Companies</b> - add & manage your companies \n\n"
        # "<b>Notifications</b> - customize notifications you wanna receive \n\n"
        "<b>My Profile</b> - manage your profile \n\n"
        "<b>Help</b> - show help message \n\n"
    )

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=help_msg,
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text(
            text=help_msg,
            parse_mode="HTML",
        )


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the /cancel command.

    Sends a message to the user indicating that the operation has been cancelled,
    and that they can start again by sending /start or /help.

    Args:
        update (Update): The update object from the Telegram API.
        context (ContextTypes.DEFAULT_TYPE): The context object from the Telegram API, containing the bot's data and state.

    Returns:
        int: The next state of the conversation, which is always ConversationHandler.END.
    """

    cancel_msg = (
        "Operation cancelled \n"
        "You can start again by sending /start or /help to see available commands."
    )

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=cancel_msg,
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text(
            text=cancel_msg,
            parse_mode="HTML",
        )
    return ConversationHandler.END
