import os
import logging
import psycopg2

from telegram import (
  Update,
  InlineKeyboardButton,
  InlineKeyboardMarkup,
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

conn = psycopg2.connect(
  host="localhost",
  database="talenthive",
  user="postgres",
  password="postgres",
  port="5432"
)
cursor = conn.cursor()

logging.basicConfig(
  format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

ROLE_DECISION, J_NAME, J_EMAIL, J_LOCATION, J_REGISTER, R_NAME, R_EMAIL, R_LOCATION, R_REGISTER = range(9)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
  id = update.message.chat.id
  cursor.execute("SELECT * FROM users WHERE telegram_id = %s", (id,))
  user = cursor.fetchone()
  
  guestKeyboard = [
    [InlineKeyboardButton('Recruiter', callback_data='recruiter')],
    [InlineKeyboardButton('Job Seeker', callback_data='jobseeker')],
  ]
  
  jobseekerKeyboard = [
    [InlineKeyboardButton('Profile', callback_data='my_profile')],
    [InlineKeyboardButton('My Applications', callback_data='my_applications')],
    [InlineKeyboardButton('Job Notifications', callback_data='job_notifications')],
    [InlineKeyboardButton('Settings', callback_data='settings')],
    [InlineKeyboardButton('Help', callback_data='help')],
  ]
  
  recruiterKeyboard = [
    [InlineKeyboardButton('Profile', callback_data='my_profile')],
    [InlineKeyboardButton('My Companies', callback_data='my_applications')],
    [InlineKeyboardButton('Job Notifications', callback_data='job_notifications')],
    [InlineKeyboardButton('Settings', callback_data='settings')],
    [InlineKeyboardButton('Help', callback_data='help')],
  ]

  if not user:
    await update.message.reply_html(
      '<b>Hello, Welcome to Talent Bot!</b>\n\n'
      '<b>Are you a recruiter or a job seeker?</b>\n\n',
      reply_markup=InlineKeyboardMarkup(guestKeyboard),
    )
    return ROLE_DECISION
  elif user[2] == 1:
    await update.message.reply_html(
      text=f"<b>Hello {user[3]}, Welcome to Talent Hive Bot!</b>\n\n"
            "<b>My Profile</b>:  to register and update your profile\n\n"
            "<b>My Applications</b>:  track the status of all your applications\n\n"
            "<b>Job Notifications</b>:  to filter and get the jobs you want straight from the Bot\n\n"
            "<b>Settings</b>:  to customize your preferences\n\n"
            "<b>Help</b>:  get answers to your questions about Talent Hive\n\n",
      reply_markup=InlineKeyboardMarkup(jobseekerKeyboard),
    )
  elif user[2] == 2:
    await update.message.reply_html(
      text=f"<b>Hello {user[3]}, Welcome to Talent Hive Bot!</b>\n\n"
            "<b>My Profile</b>:  to register and update your profile\n\n"
            "<b>My Applications</b>:  track the status of all your applications\n\n"
            "<b>Job Notifications</b>:  to filter and get the jobs you want straight from the Bot\n\n"
            "<b>Settings</b>:  to customize your preferences\n\n"
            "<b>Help</b>:  get answers to your questions about Talent Hive\n\n",
      reply_markup=InlineKeyboardMarkup(recruiterKeyboard),
    )
  else:
    await update.message.reply_html(
      '<b>Who the fuck are ya?</b>\n\n'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await context.bot.send_message(
    chat_id=update.effective_chat.id,
    text="Help:\n\n"
        "/start - start the bot\n"
        "/help - show this help message\n"        
        "/cancel - to exit the current conversation\n"
        "/ask your question - to ask your questions\n\n"
        "<b>My Profile</b>:  to register and update your profile\n"
        "<b>My Applications</b>:  track the status of all your applications\n"
        "<b>Job Notifications</b>:  to filter and get the jobs you want straight from the Bot\n"
        "<b>Settings</b>:  to customize your preferences\n"
        "<b>Help</b>:  get answers to your questions about Talent Hive\n",
    parse_mode="HTML",
  )

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
      text=f"<b>Job Seeker Registration</b>\n\n"
            "<b>Please enter your name: </b>",
      parse_mode="HTML"
    )
    return J_NAME
  elif decision == 'recruiter':
    await query.edit_message_text(
      text=f"<b>Recruiter Registration</b>\n\n"
            "<b>Please enter your name: </b>",
      parse_mode="HTML"
    )
    return R_NAME
  else:
    await query.edit_message_text(
      text="<b>Invalid choice. Please try again.</b>"
    )
    return ROLE_DECISION


# JOB SEEKER RELATED
async def j_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
  context.user_data['j_id'] = update.message.chat.id
  context.user_data['j_name'] = update.message.text
  
  await update.message.reply_html(f"<b>Please enter your email: </b>")
  
  return J_EMAIL

async def j_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
  context.user_data['j_email'] = update.message.text
  
  await update.message.reply_html(f"<b>Please enter your skills (separate each by comma): </b>")
  
  return J_LOCATION

async def j_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
  context.user_data['j_location'] = update.message.text

  cursor.execute("INSERT INTO users (telegram_id, role_id, name, email, location) VALUES (%s, %s, %s, %s, %s)", (context.user_data['j_id'], 1, context.user_data['j_name'], context.user_data['j_email'], context.user_data['j_location']))
  conn.commit()
  # conn.close()

  await update.message.reply_html(
    f"<b>Registered successfully 🎉</b>\n\n"
  )
  
  return J_REGISTER

async def j_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
  print("registering...")


# JOB SEEKER RELATED
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
  
  cursor.execute("INSERT INTO users (telegram_id, role_id, name, email, location) VALUES (%s, %s, %s, %s, %s)", (context.user_data['r_id'], 2, context.user_data['r_name'], context.user_data['r_email'], context.user_data['r_location']))
  conn.commit()
  # conn.close()

  await update.message.reply_html(
    f"<b>Registered successfully 🎉</b>\n\n"
  )
  
  return R_REGISTER

async def r_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
  print("registering...")



def main() -> None:
  app = Application.builder().token(os.getenv('TOKEN')).build()
  
  conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start_command)],
    states={
      ROLE_DECISION: [CallbackQueryHandler(role_decision)],
      J_NAME: [MessageHandler(filters.TEXT & (~filters.COMMAND), j_name)],
      J_EMAIL: [MessageHandler(filters.TEXT & (~filters.COMMAND), j_email)],
      J_LOCATION: [MessageHandler(filters.TEXT & (~filters.COMMAND), j_location)],
      J_REGISTER: [MessageHandler(filters.TEXT & (~filters.COMMAND), j_register)],
      R_NAME: [MessageHandler(filters.TEXT & (~filters.COMMAND), r_name)],
      R_EMAIL: [MessageHandler(filters.TEXT & (~filters.COMMAND), r_email)],
      R_LOCATION: [MessageHandler(filters.TEXT & (~filters.COMMAND), r_location)],
      R_REGISTER: [MessageHandler(filters.TEXT & (~filters.COMMAND), j_register)],
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
