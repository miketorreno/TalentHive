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

R_NAME, R_EMAIL, R_SKILLS, R_EXPERIENCE, R_LOCATION, R_CV, R_REGISTER, R_USERNAME, R_PREFERENCES = range(9)

async def r_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
  context.user_data['r_id'] = update.message.chat.id
  context.user_data['r_name'] = update.message.text
  
  await update.message.reply_html(f"<b>Please enter your email: </b>")
  
  return R_EMAIL

async def r_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
  context.user_data['r_email'] = update.message.text
  
  await update.message.reply_html(f"<b>Please enter your location: </b>")
  
  return R_LOCATION

async def r_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
  context.user_data['r_location'] = update.message.text
  print(context.user_data)
  
  return R_REGISTER

async def r_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
  print("registering...")
  
  summary = (f"<b>Profile \n\n</b>"
                    f"<b>ID: </b> {context.user_data['r_id']}\n"
                    f"<b>Name: </b> {context.user_data['r_name']}\n"
                    f"<b>Email: </b> {context.user_data['r_email']}\n"
                    f"<b>Location: </b> {context.user_data['r_location']}\n")

  await update.message.reply_html(
    # text=f"<b>Registered successfully 🎉</b>\n"
    summary
  )
  
  return ConversationHandler.END

