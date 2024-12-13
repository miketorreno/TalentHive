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
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

ROLE_DECISION, J_NAME, J_EMAIL, J_LOCATION, J_REGISTER, R_NAME, R_EMAIL, R_LOCATION, R_REGISTER, R_PROFILE, BUSINESS_TYPE_CHOICE, MY_COMPANIES, COMPANIES, ADD_COMPANY_STEP_ONE, ADD_COMPANY_STEP_TWO, ADD_COMPANY_STEP_THREE, ADD_COMPANY_STEP_FOUR, ADD_COMPANY_STEP_FIVE, STARTUPS = range(19)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
  id = update.message.chat.id
  cursor.execute("SELECT * FROM users WHERE telegram_id = %s", (id,))
  user = cursor.fetchone()
  
  guestKeyboard = [
    [InlineKeyboardButton('Recruiter', callback_data='recruiter')],
    [InlineKeyboardButton('Job Seeker', callback_data='jobseeker')],
  ]

  jobseekerKeyboard = [
    [InlineKeyboardButton('Profile', callback_data='j_profile')],
    [InlineKeyboardButton('My Applications', callback_data='my_applications')],
    [InlineKeyboardButton('Job Notifications', callback_data='job_notifications')],
    [InlineKeyboardButton('Settings', callback_data='j_settings')],
    [InlineKeyboardButton('Help', callback_data='j_help')],
  ]

  recruiterKeyboard = [
    [InlineKeyboardButton('My Profile', callback_data='r_profile')],
    [InlineKeyboardButton('My Companies/Startups', callback_data='my_companies')],
    [InlineKeyboardButton('My Job Posts', callback_data='my_job_posts')],
    [InlineKeyboardButton('Post a Job', callback_data='post_Job')],
    [InlineKeyboardButton('Settings', callback_data='r_settings')],
    [InlineKeyboardButton('Help', callback_data='r_help')],
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
    return ConversationHandler.END
  elif user[2] == 2:
    await update.message.reply_html(
      text=f"<b>Hello {user[3]} 👋 \t welcome back!</b>\n\n"
            "<b>My Profile</b> \t-\t view and update your profile\n\n"
            "<b>My Companies/Startups</b> \t-\t add & manage your companies and startups\n\n"
            "<b>My Job Posts</b> \t-\t view & manage your job posts\n\n"
            "<b>Post a job</b> \t-\t find the perfect talent\n\n"
            "<b>Settings</b> \t-\t customize your experience\n\n"
            "<b>Help</b> \t-\t get answers to your questions about\n\n",
      reply_markup=InlineKeyboardMarkup(recruiterKeyboard),
    )
    return ConversationHandler.END
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
  
  return ConversationHandler.END
  return J_REGISTER

async def j_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
  print("registering...")

async def j_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
  # id = update.effective_chat.id
  id = update.effective_user.id
  cursor.execute("SELECT * FROM users WHERE telegram_id = %s", (id,))
  user = cursor.fetchone()
  
  await context.bot.send_message(
    chat_id=id,
    text=f"<b>Name</b>: {user[3]} \n<b>Email</b>: {user[4]} \n<b>Location</b>: {user[9]}",
    parse_mode="HTML",
  )



# RECRUITER RELATED
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
  
  return ConversationHandler.END
  return R_REGISTER

async def r_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
  print("registering...")


async def r_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
  # id = update.effective_chat.id
  id = update.effective_user.id
  cursor.execute("SELECT * FROM users WHERE telegram_id = %s", (id,))
  user = cursor.fetchone()
  
  await context.bot.send_message(
    chat_id=id,
    text=f"<b>Name</b>: {user[3]} \n<b>Email</b>: {user[4]} \n<b>Location</b>: {user[9]}",
    parse_mode="HTML",
  )

async def my_companies(update: Update, context: ContextTypes.DEFAULT_TYPE):
  businessTypeKeyboard = [
    [InlineKeyboardButton('Company', callback_data='company')],
    [InlineKeyboardButton('Startup', callback_data='startup')],
  ]

  await context.bot.send_message(
    chat_id=update.effective_chat.id,
    text=f"Which represents your business better?\n\n"
          "<b>Company</b>: a classically built business in any mature, pre-existing and strong industry\n\n"
          "<b>Startup</b>: a new comer to the industry that is agile, fast-growing and has a technologically innovative approach\n\n",
    reply_markup=InlineKeyboardMarkup(businessTypeKeyboard),
    parse_mode="HTML",
  )

  return BUSINESS_TYPE_CHOICE

async def business_type_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  await query.answer()
  choice = query.data

  companiesKeyboard = [
    [
      InlineKeyboardButton('My Companies', callback_data='registered_companies'),
      InlineKeyboardButton('Add Company', callback_data='add_company')
    ],
    [InlineKeyboardButton('Back', callback_data='back_to_my_companies')],
  ]

  if choice == 'company':
    await query.edit_message_text(
      text=f"<b>My Companies:</b> view and manage companies you have already registered\n\n"
            "<b>Add Company:</b> register a new company\n\n",
      reply_markup=InlineKeyboardMarkup(companiesKeyboard),
      parse_mode="HTML",
    )
    return COMPANIES
  elif choice == 'startup':
    await query.edit_message_text(
      text=f"<b>My Startups:</b> view and manage startups you have already registered\n\n"
            "<b>Add Startup:</b> register a new startup\n\n",
      parse_mode="HTML"
    )
    return STARTUPS
  else:
    await query.edit_message_text(
      text="<b>Invalid choice. Please try again.</b>"
    )
    return BUSINESS_TYPE_CHOICE

async def companies(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  await query.answer()
  
  if query.data == 'back_to_my_companies':
    return MY_COMPANIES
  elif query.data == 'registered_companies':
    print("registered companies")
  elif query.data == 'add_company':
    return ADD_COMPANY_STEP_ONE
  else:
    await query.edit_message_text(
      text="<b>Invalid choice. Please try again.</b>"
    )
    return COMPANIES

  await update.message.reply_html(
    text=f"...coming soon...",
  )
  
  return BUSINESS_TYPE_CHOICE

async def add_company_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.message.reply_html(
    text=f"",
    reply_markup=InlineKeyboardMarkup(backOrCancelKeyboard),
    parse_mode="HTML",
  )
  return ADD_COMPANY_STEP_FIVE
  pass

async def add_company_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):  
  await update.message.reply_html(
    text=f"",
    reply_markup=InlineKeyboardMarkup(backOrCancelKeyboard),
    parse_mode="HTML",
  )
  return ADD_COMPANY_STEP_FIVE
  pass

async def add_company_step_one(update: Update, context: ContextTypes.DEFAULT_TYPE):
  recruiterTypeKeyboard = [
    [
      InlineKeyboardButton('General Manager', callback_data='general_manager'),
      InlineKeyboardButton('Recruiter', callback_data='recruiter')
    ],
    [InlineKeyboardButton('Back', callback_data='back_to_business_type_choice')],
  ]

  await update.message.reply_html(
    text=f"Please choose how you would like to register. \n\n"
          "<b>General manager</b> (the person on the Trade license) \n"
          "\t- General Manager ID photo/pdf \n"
          "\t- Trade license photo/pdf \n\n"

          "<b>Recruiter</b> (a person who works for the company) \n"
          "\t- Recruiter ID photo/pdf \n"
          "\t- Letter of authorization to register and recruit on behalf of the company (with the company stamp) photo/pdf \n"
          "\t- Trade license photo/pdf \n\n"
          
          "<i>* files can be pdf or photo</i>",
    reply_markup=InlineKeyboardMarkup(recruiterTypeKeyboard),
    parse_mode="HTML"
  )
  
  return ADD_COMPANY_STEP_TWO

async def add_company_step_two(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  await query.answer()
  
  backOrCancelKeyboard = [
    [
      InlineKeyboardButton('Back', callback_data='back_one_step'),
      InlineKeyboardButton('Cancel', callback_data='cancel')
    ],
  ]
  
  if query.data == 'back_to_business_type_choice':
    return ADD_COMPANY_STEP_ONE
  elif query.data == 'general_manager':
    await query.edit_message_text(
      text=f"[1/3] <b>Please enter the name of your company</b>\n\n"
            "<i>* The name of the company should match the name on the trade license</i>",
      reply_markup=InlineKeyboardMarkup(backOrCancelKeyboard),
      parse_mode="HTML",
    )
    return ADD_COMPANY_STEP_THREE
  elif query.data == 'recruiter':
    await query.edit_message_text(
      text=f"[1/4] <b>Please enter the name of your company</b>\n\n"
            "<i>* The name of the company should match the name on the trade license</i>",
      reply_markup=InlineKeyboardMarkup(backOrCancelKeyboard),
      parse_mode="HTML",
    )
    return ADD_COMPANY_STEP_THREE
  else:
    await query.edit_message_text(
      text="<b>Invalid choice. Please try again.</b>"
    )
    return ADD_COMPANY_STEP_TWO

async def add_company_step_three(update: Update, context: ContextTypes.DEFAULT_TYPE):
  context.user_data['company_name'] = update.message.text
  
  backOrCancelKeyboard = [
    [
      InlineKeyboardButton('Back', callback_data='back_one_step'),
      InlineKeyboardButton('Cancel', callback_data='cancel')
    ],
  ]
  
  await update.message.reply_html(
    text=f"[2/3] <b>Please upload your trade license as a photo/pdf</b>\n\n"
          "<i>* file can be pdf or photo \n\n</i>"
          "<i>* This information will ONLY be used to verify that your company is a legitimate business and will NOT be made public.</i>",
    reply_markup=InlineKeyboardMarkup(backOrCancelKeyboard),
    parse_mode="HTML",
  )
  return ADD_COMPANY_STEP_FOUR

async def add_company_step_four(update: Update, context: ContextTypes.DEFAULT_TYPE):
  license_file = await update.message.photo[-1].get_file()
  context.user_data['company_license'] = license_file.file_id
  
  backOrCancelKeyboard = [
    [
      InlineKeyboardButton('Back', callback_data='back_one_step'),
      InlineKeyboardButton('Cancel', callback_data='cancel')
    ],
  ]
  
  await update.message.reply_html(
    text=f"[3/3] <b>Please upload the general manager’s ID as a photo/pdf</b>\n\n"
          "<i>Note: The general manager is the person that is on the trade license. \n\n</i>"
          "<i>* ID can be driver’s license, passport, company ID or residence/kebele ID \n\n</i>"
          "<i>* file can be pdf or photo \n\n</i>"
          "<i>* This information will ONLY be used to verify that your company is a legitimate business and will NOT be made public.</i>",
    reply_markup=InlineKeyboardMarkup(backOrCancelKeyboard),
    parse_mode="HTML",
  )
  return ADD_COMPANY_STEP_FIVE

async def add_company_step_five(update: Update, context: ContextTypes.DEFAULT_TYPE):
  pass


async def startups(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.message.reply_html(
    text=f"...coming soon..."
  )
  
  return BUSINESS_TYPE_CHOICE



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
      R_REGISTER: [MessageHandler(filters.TEXT & (~filters.COMMAND), r_register)],
    },
    fallbacks=[CommandHandler("cancel", cancel_command)],
  )
  
  company_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(my_companies, '^my_companies$')],
    states={
      BUSINESS_TYPE_CHOICE: [CallbackQueryHandler(business_type_choice)],
      MY_COMPANIES: [MessageHandler(filters.TEXT & (~filters.COMMAND), my_companies)],
      COMPANIES: [MessageHandler(filters.TEXT & (~filters.COMMAND), companies)],
      ADD_COMPANY_STEP_ONE: [MessageHandler(filters.TEXT & (~filters.COMMAND), add_company_step_one)],
      ADD_COMPANY_STEP_TWO: [MessageHandler(filters.TEXT & (~filters.COMMAND), add_company_step_two)],
      ADD_COMPANY_STEP_THREE: [MessageHandler(filters.TEXT & (~filters.COMMAND), add_company_step_three)],
      ADD_COMPANY_STEP_FOUR: [MessageHandler(filters.TEXT & (~filters.COMMAND), add_company_step_four)],
      ADD_COMPANY_STEP_FIVE: [MessageHandler(filters.TEXT & (~filters.COMMAND), add_company_step_five)],
      
      STARTUPS: [MessageHandler(filters.TEXT & (~filters.COMMAND), startups)],
    },
    fallbacks=[CommandHandler("cancel", cancel_command)],
  )

  app.add_handler(conv_handler)
  app.add_handler(company_conv_handler)
  app.add_handler(CommandHandler("start", start_command))
  app.add_handler(CommandHandler("help", help_command))
  app.add_handler(CommandHandler("cancel", cancel_command))
  
  app.add_handler(CallbackQueryHandler(r_profile, '^r_profile$'))
  # app.add_handler(CallbackQueryHandler(my_companies, '^my_companies$'))
  
  app.run_polling()

if __name__ == "__main__":
  main()
