from telegram import (
  Update,
  InlineKeyboardButton,
  InlineKeyboardMarkup,
  ReplyKeyboardMarkup,
  ReplyKeyboardRemove,
)
from telegram.ext import (
  filters,
  Application,
  ContextTypes,
  CommandHandler,
  MessageHandler,
  ConversationHandler,
  CallbackQueryHandler,
)

J_WELCOME = range(1)

async def j_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
  jobseekerKeyboard = [
    [InlineKeyboardButton('My Profile', callback_data='my_profile')],
    [InlineKeyboardButton('My Applications', callback_data='my_applications')],
    [InlineKeyboardButton('Job Notifications', callback_data='my_applications')],
    [InlineKeyboardButton('Settings', callback_data='settings')],
    [InlineKeyboardButton('Help', callback_data='help')],
  ]
  
  await update.message.reply_html(
    text=f"<b>Hello [NAME HERE], Welcome to Talent Hive Bot!</b>\n\n"
          "<b>My Profile</b>:  to register and update your profile\n\n"
          "<b>My Applications</b>:  track the status of all your applications\n\n"
          "<b>Job Notifications</b>:  to filter and get the jobs you want straight from the Bot\n\n"
          "<b>Settings</b>:  to customize your preferences\n\n"
          "<b>Help</b>:  get answers to your questions about Talent Hive\n\n",
    reply_markup=InlineKeyboardMarkup(jobseekerKeyboard),
  )

