from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes, ConversationHandler

# from applicants.handlers.job import show_job
from applicants.states.all import REGISTER
from utils.helpers import get_applicant, show_job


async def start_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int | None:
    """
    Handles the initial interaction with the user when they start the bot.

    Depending on the user's registration status, it either prompts them to
    register or provides options to browse jobs, view saved jobs, manage
    their profile, or track their applications.

    Args:
        update (Update): The update object from the Telegram API.
        context (ContextTypes.DEFAULT_TYPE): The context object from the
            Telegram API, containing the bot's data and state.

    Returns:
        REGISTER state if the user is not registered, otherwise no explicit
        return value as the function interacts with the user via messages.
    """

    applicant = get_applicant(update, context)

    if not applicant:
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

    args = context.args
    if args and args[0].startswith("apply_"):
        # job_id = args[0].split("_")[1]
        job_id = int(args[0].split("_")[1])
        await show_job(update, context, job_id)
    else:
        keyboard = [
            ["Browse Jobs", "Saved Jobs"],
            ["My Profile", "My Applications"],
            # ["Job Notifications", "Help"]
            ["Help"],
        ]
        welcome_msg = (
            f"<b>Hello {(applicant['name'].split()[0]).capitalize()} 👋\t Welcome to HulumJobs!</b> \n\n"
            "<b>💼 \tBrowse Jobs</b>:\t find jobs that best fit your schedule \n\n"
            "<b>📌 \tSaved Jobs</b>:\t your saved jobs \n\n"
            "<b>👤 \tMy Profile</b>:\t manage your profile \n\n"
            "<b>📑 \tMy Applications</b>:\t view and track your applications \n\n"
            # "<b>🔔 \tJob Notifications</b>:\t customize notifications you wanna receive \n\n"
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
    Shows the help message for the bot.

    Args:
        update (Update): The update object from the Telegram API.
        context (ContextTypes.DEFAULT_TYPE): The context object from the
            Telegram API, containing the bot's data and state.

    Returns:
        None
    """

    help_msg = (
        "<b>Help</b>\n\n"
        "<b>Browse Jobs</b> - find jobs that best fit your schedule \n\n"
        "<b>Saved Jobs</b> - your saved jobs \n\n"
        "<b>My Profile</b> - manage your profile \n\n"
        "<b>My Applications</b> - view and track your applications \n\n"
        # "<b>Job Notifications</b> - customize notifications you wanna receive \n\n"
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
    Cancel the conversation and sends a goodbye message.
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
