import os
import logging

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
from pymongo import MongoClient

# MongoDB setup
# sudo service mongod start
client = MongoClient("localhost", 27017)
db = client['TalentHiveBot']
jobseekers = db['jobseekers']
recruiters = db['recruiters']
companies = db['companies']

# Enable logging
logging.basicConfig(
  format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# States
# START, CANCEL, SELECT, ADD, DELETE, EDIT = range(6)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
  id = update.message.chat.id
  user = jobseekers.find_one({"user_id": id})
  
  keyboard = [
    [InlineKeyboardButton('Recruiter', callback_data='recruiter')],
    [InlineKeyboardButton('Job Seeker', callback_data='jobseeker')],
  ]
  
  if user:
    await update.message.reply_html(
      text=f"<b>Hello {user.get('user_name')}, Welcome to Talent Hive Bot!</b>\n"
    )
#   elif recruiter:
#     await update.message.reply_html(
#       text=f"<b>Hello {user.get('user_name')} from {recruiter.get('company_name')}, Welcome to Talent Bot!</b>\n"
#     )
  else:
    await update.message.reply_html(
      'Hello, Welcome to Talent Bot!\n\n'
      'Are you a recruiter or a job seeker?\n\n',
      reply_markup=InlineKeyboardMarkup(keyboard),
    )  

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await context.bot.send_message(
    chat_id=update.effective_chat.id,
    text="Commands:\n\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
  )

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
  await update.message.reply_text('Hope to talk to you soon.', reply_markup=ReplyKeyboardRemove())
  return ConversationHandler.END


def main() -> None:
  app = Application.builder().token(os.getenv('TOKEN')).build()
  
  conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start_command)],
    states={
    },
    fallbacks=[CommandHandler("cancel", cancel_command)],
  )

  app.add_handler(conv_handler)
  app.add_handler(CommandHandler("start", start_command))
  app.add_handler(CommandHandler("help", help_command))
  app.add_handler(CommandHandler("cancel", cancel_command))
  
  
  app.run_polling()

if __name__ == "__main__":
  main()
