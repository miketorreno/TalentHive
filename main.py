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
ROLE_DECISION, J_NAME, J_EMAIL, J_SKILLS, J_EXPERIENCE, J_LOCATION, J_CV, J_REGISTER, J_USERNAME, J_PREFERENCES, J_SUBSCRIBED_ALERTS, R_NAME = range(12)
# START, CANCEL, SELECT, ADD, DELETE, EDIT = range(6)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
  id = update.message.chat.id
  jobseeker = jobseekers.find_one({"id": id})
  recruiter = recruiters.find_one({"id": id})
  
  guestKeyboard = [
    [InlineKeyboardButton('Recruiter', callback_data='recruiter')],
    [InlineKeyboardButton('Job Seeker', callback_data='jobseeker')],
  ]
  
  jobseekerKeyboard = [
    [InlineKeyboardButton('My Profile', callback_data='my_profile')],
    [InlineKeyboardButton('My Applications', callback_data='my_applications')],
    [InlineKeyboardButton('Job Notifications', callback_data='my_applications')],
    [InlineKeyboardButton('Settings', callback_data='settings')],
    [InlineKeyboardButton('Help', callback_data='help')],
  ]
  
  recruiterKeyboard = [
    [InlineKeyboardButton('...', callback_data='...')],
  ]
  
  if jobseeker:
    await update.message.reply_html(
      text=f"<b>Hello {jobseeker.get('name')}, Welcome to Talent Hive Bot!</b>\n\n"
            "<b>My Profile</b>:  to register and update your profile\n\n"
            "<b>My Applications</b>:  track the status of all your applications\n\n"
            "<b>Job Notifications</b>:  to filter and get the jobs you want straight from the Bot\n\n"
            "<b>Settings</b>:  to customize your preferences\n\n"
            "<b>Help</b>:  get answers to your questions about Talent Hive\n\n",
      reply_markup=InlineKeyboardMarkup(jobseekerKeyboard),
    )
  elif recruiter:
    await update.message.reply_html(
      text=f"<b>Hello {recruiter.get('name')}, Welcome to Talent Hive Bot!</b>\n"
    )
  else:
    await update.message.reply_html(
      '<b>Hello, Welcome to Talent Bot!</b>\n\n'
      '<b>Are you a recruiter or a job seeker?</b>\n\n',
      reply_markup=InlineKeyboardMarkup(guestKeyboard),
    )
  
  return ROLE_DECISION

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await context.bot.send_message(
    chat_id=update.effective_chat.id,
    text="Help:\n\n"
        "/start - start the bot\n"
        "/help - show this help message\n"        
        "/ask your question - to ask your questions\n\n"
        "<b>My Profile</b>:  to register and update your profile\n"
        "<b>My Applications</b>:  track the status of all your applications\n"
        "<b>Job Notifications</b>:  to filter and get the jobs you want straight from the Bot\n"
        "<b>Settings</b>:  to customize your preferences\n"
        "<b>Help</b>:  get answers to your questions about Talent Hive\n",
    parse_mode="HTML",
  )

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
  await update.message.reply_html(
    f'<b>Hope to talk to you soon.</b>'
  )
  return ConversationHandler.END

async def role_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  await query.answer()
  decision = query.data
  
  if decision == 'jobseeker':
    await query.edit_message_text(
      text=f"<b>Registration</b>\n\n"
            "<b>Please enter your name: </b>",
      parse_mode="HTML"
    )
    return J_NAME
  elif decision == 'recruiter':
    await query.edit_message_text(
      text=f"<b>Registration</b>\n\n"
            "<b>Please enter your name: </b>",
      parse_mode="HTML"
    )
    return R_NAME
  else:
    await query.edit_message_text(
      text="<b>Invalid choice. Please try again.</b>"
    )
    return ROLE_DECISION

async def j_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
  context.user_data['j_id'] = update.message.chat.id
  context.user_data['j_name'] = update.message.text
  
  await update.message.reply_html(f"<b>Please enter your email: </b>")
  
  return J_EMAIL

async def j_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
  context.user_data['j_email'] = update.message.text
  
  await update.message.reply_html(f"<b>Please enter your skills (separate each by comma): </b>")
  
  return J_SKILLS

async def j_skills(update: Update, context: ContextTypes.DEFAULT_TYPE):
  context.user_data['j_skills'] = update.message.text
  
  await update.message.reply_html(f"<b>Please enter your experience: </b>")
  
  return J_EXPERIENCE

async def j_experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
  context.user_data['j_experience'] = update.message.text
  
  await update.message.reply_html(f"<b>Please enter your location: </b>")
  
  return J_LOCATION

async def j_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
  context.user_data['j_location'] = update.message.text
  
  # await update.message.reply_html(
  #   text=f"<b>Please upload your cv: </b>\n"
  #         "<b>or send /skip</b>",
  # )
  
  return J_REGISTER

# async def j_cv(update: Update, context: ContextTypes.DEFAULT_TYPE):
#   context.user_data['j_cv'] = update.message.text
  
#   await update.message.reply_html(
#     text=f"<b>CV uploaded</b>\n"
#   )
  
#   return J_REGISTER

# async def skip_cv_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):  
#   await update.message.reply_html(
#     text=f"<b>CV skipped</b>\n"
#   )
  
#   return J_REGISTER

async def j_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
  jobseekers.insert_one({
    "id": context.user_data['j_id'],
    "name": context.user_data['j_name'],
    "email": context.user_data['j_email'],
    "skills": context.user_data['j_skills'],
    "experience": context.user_data['j_experience'],
    "location": context.user_data['j_location'],
    "cv": "PLACEHOLDER",
    "username": "PLACEHOLDER",
    "preferences": "PLACEHOLDER",
    "subscribed_alerts": "PLACEHOLDER",
  })
  
  await update.message.reply_html(
    text=f"<b>Registered successfully 🎉</b>\n"
  )
  
  return ConversationHandler.END

async def r_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
  context.user_data['r_id'] = update.message.chat.id
  context.user_data['r_name'] = update.message.text
  
  await update.message.reply_html(f"<b>Please enter your email: </b>")
  
  # return R_EMAIL


def main() -> None:
  app = Application.builder().token(os.getenv('TOKEN')).build()
  
  conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start_command)],
    states={
      ROLE_DECISION: [CallbackQueryHandler(role_decision)],
      J_NAME: [MessageHandler(filters.TEXT & (~filters.COMMAND), j_name)],
      J_EMAIL: [MessageHandler(filters.TEXT & (~filters.COMMAND), j_email)],
      J_SKILLS: [MessageHandler(filters.TEXT & (~filters.COMMAND), j_skills)],
      J_EXPERIENCE: [MessageHandler(filters.TEXT & (~filters.COMMAND), j_experience)],
      J_LOCATION: [MessageHandler(filters.TEXT & (~filters.COMMAND), j_location)],
      J_REGISTER: [MessageHandler(filters.TEXT & (~filters.COMMAND), j_register)],
      # J_CV: [
      #   MessageHandler(filters.TEXT & (~filters.COMMAND), j_cv),
      #   CommandHandler('skip', skip_cv_upload)
      # ],
      
      R_NAME: [MessageHandler(filters.TEXT & (~filters.COMMAND), r_name)],
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
