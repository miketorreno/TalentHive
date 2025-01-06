from telegram import Update
from telegram.ext import CallbackContext

def start_command(update: Update, context: CallbackContext):
    """Send a welcome message when the /start command is issued."""
    update.message.reply_text("Welcome to the bot!")
