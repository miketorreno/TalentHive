import os
import logging
import psycopg2

from telegram import (
  Update,
  ReplyKeyboardRemove,
  InlineKeyboardButton,
  InlineKeyboardMarkup
)
from telegram.ext import (
  filters,
  Application,
  ContextTypes,
  MessageHandler,
  CommandHandler,
  ApplicationBuilder,
  ConversationHandler,
  CallbackQueryHandler
)

conn = psycopg2.connect(
  host="localhost",
  database="telegram_job_board",
  user="postgres",
  password="postgres",
  port="5432"
)
# cursor = conn.cursor()

logging.basicConfig(
  format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG  # level=logging.INFO
)
# logging.getLogger("httpx").setLevel(logging.WARNING)  # avoid all GET and POST requests being logged
logger = logging.getLogger(__name__)

ROLE, COMPLETE = range(2)
JOB_TITLE, JOB_DESCRIPTION, JOB_REQUIREMENTS, JOB_LOCATION, JOB_SALARY, JOB_CONFIRM = range(6)
COMPANY_NAME, COMPANY_DESCRIPTION, COMPANY_CONFIRM = range(3)
EDIT_COMPANY_ID, EDIT_FIELD, EDIT_VALUE = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  keyboard = [
    [InlineKeyboardButton("Register", callback_data="register")],
    [InlineKeyboardButton("Browse Jobs", callback_data="browse_jobs")],
    [InlineKeyboardButton("Post a Job", callback_data="post_job")],
    [InlineKeyboardButton("Create Company", callback_data="create_company")],
    [InlineKeyboardButton("My Companies", callback_data="my_companies")],
    [InlineKeyboardButton("Help", callback_data="help")]
  ]
  reply_markup = InlineKeyboardMarkup(keyboard)

  await update.message.reply_text("Welcome to the Job Listing Bot! Choose an option:", reply_markup=reply_markup)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
  user = update.message.from_user
  logger.info("User %s canceled the conversation.", user.first_name)
  await update.message.reply_text(
    "Bye! I hope we can talk again some day."
  )

  return ConversationHandler.END

# Handle Inline Button Callbacks
async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  await query.answer()  # Acknowledge the button press

  # Determine which button was pressed
  if query.data == "register":
    await register(update, context)  # Call the registration function
  elif query.data == "browse_jobs":
    await browse_jobs(update, context)
  # elif query.data == "post_job":
  #   await post_job(update, context)
  elif query.data == "help":
    await query.edit_message_text("Use the buttons to navigate the bot features.")

# Register Callback Handler
callback_handler = CallbackQueryHandler(handle_callbacks)

# Inline Registration
async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
  keyboard = [
    [InlineKeyboardButton("Employer", callback_data="register_employer")],
    [InlineKeyboardButton("Job Seeker", callback_data="register_jobseeker")],
    [InlineKeyboardButton("Admin", callback_data="register_admin")]
  ]
  reply_markup = InlineKeyboardMarkup(keyboard)

  if update.callback_query:
    query = update.callback_query
    await query.edit_message_text("Select your role:", reply_markup=reply_markup)
  else:
    await update.message.reply_text("Select your role:", reply_markup=reply_markup)

async def register_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  await query.answer()
  
  user_role = query.data.split("_")[1]  # Extract role from callback_data
  telegram_id = query.from_user.id
  username = query.from_user.username
  
  if user_role == "employer":
    role_id = 1
  elif user_role == "jobseeker":
    role_id = 2
  elif user_role == "admin":
    role_id = 3

  # Save user to the database
  cur = conn.cursor()
  cur.execute(
    "INSERT INTO users (telegram_id, role_id, name, username) VALUES (%s, %s, %s, %s)",
    (telegram_id, role_id, username, username)
  )
  conn.commit()
  
  await query.edit_message_text(f"Registration complete as {user_role.capitalize()}.")

async def post_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
  keyboard = [
    [InlineKeyboardButton("Create a Job", callback_data="create_job")],
    [InlineKeyboardButton("View My Jobs", callback_data="view_jobs")]
  ]
  reply_markup = InlineKeyboardMarkup(keyboard)

  if update.callback_query:
    query = update.callback_query
    await query.edit_message_text("What would you like to do?", reply_markup=reply_markup)
  else:
    await update.message.reply_text("What would you like to do?", reply_markup=reply_markup)

async def create_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  await query.edit_message_text("Send me the job title:")

  # Next: Collect job details via a series of messages or buttons
  context.user_data["job_creation_step"] = "title"

async def browse_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
  # Fetch jobs from the database
  cur = conn.cursor()
  cur.execute("SELECT job_id, title FROM jobs ORDER BY created_at DESC LIMIT 5")
  jobs = cur.fetchall()
  print("jobs", jobs)

  # Create buttons for each job
  keyboard = [[InlineKeyboardButton(job[1], callback_data=f"view_job_{job[0]}")] for job in jobs]
  reply_markup = InlineKeyboardMarkup(keyboard)

  if update.callback_query:
    query = update.callback_query
    await query.edit_message_text("Available Jobs:", reply_markup=reply_markup)
  else:
    await update.message.reply_text("Available Jobs:", reply_markup=reply_markup)

async def view_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  job_id = int(query.data.split("_")[-1])

  # Fetch job details from the database
  cur = conn.cursor()
  cur.execute("SELECT title, description, location FROM jobs WHERE job_id = %s", (job_id,))
  job = cur.fetchone()

  message = f"**{job[0]}**\n\n{job[1]}\n\nLocation: {job[2]}"
  await query.edit_message_text(message, parse_mode="Markdown")

async def post_job_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if update.callback_query:
    query = update.callback_query
    await query.edit_message_text(
      "Let's post a job! Please enter the job title:"
    )
  else:
    await update.message.reply_text(
      "Let's post a job! Please enter the job title:",
      reply_markup=ReplyKeyboardRemove()  # Remove any existing keyboard
    )

  return JOB_TITLE

async def post_job_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
  context.user_data['job_title'] = update.message.text
  await update.message.reply_text("Great! Now, please provide a job description:")
  return JOB_DESCRIPTION

async def post_job_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
  context.user_data['job_description'] = update.message.text
  await update.message.reply_text("What are the qualifications or requirements for this job?")
  return JOB_REQUIREMENTS

async def post_job_requirements(update: Update, context: ContextTypes.DEFAULT_TYPE):
  context.user_data['job_requirements'] = update.message.text
  await update.message.reply_text("Where is this job located?")
  return JOB_LOCATION

async def post_job_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
  context.user_data['job_location'] = update.message.text
  await update.message.reply_text("What is the salary range for this job? (Optional, type 'skip' to leave it open)")
  return JOB_CONFIRM

async def post_job_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
  salary = update.message.text
  if salary.lower() != 'skip':
    context.user_data['job_salary'] = salary
  else:
    context.user_data['job_salary'] = "Not specified"

  job_title = context.user_data.get("job_title")
  job_description = context.user_data.get("job_description")
  job_requirements = context.user_data.get("job_requirements")
  job_location = context.user_data.get("job_location")
  job_salary = context.user_data.get("job_salary")

  # Inline keyboard for confirmation
  keyboard = [
    [
      InlineKeyboardButton("Confirm", callback_data="confirm_post_job"),
      InlineKeyboardButton("Cancel", callback_data="cancel_post_job"),
    ]
  ]
  reply_markup = InlineKeyboardMarkup(keyboard)

  await update.message.reply_text(
    f"You're about to post a job with the following details:\n\n"
    f"**Title:** {job_title}\n"
    f"**Description:** {job_description}\n"
    f"**Requirements:** {job_requirements}\n"
    f"**Location:** {job_location}\n"
    f"**Salary:** {job_salary}\n\n"
    "Do you confirm?",
    reply_markup=reply_markup,
    parse_mode="Markdown"
  )
  return JOB_CONFIRM

async def confirm_post_job_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
  # Get user data from the context
  user_id = update.effective_user.id
  job_title = context.user_data.get("job_title")
  job_description = context.user_data.get("job_description")
  job_salary = context.user_data.get("job_salary")

  # Save the job to the database
  cur = conn.cursor()
  cur.execute(
    "INSERT INTO jobs (company_id, title, description, salary) VALUES (%s, %s, %s, %s)",
    (2, job_title, job_description, job_salary),
  )
  conn.commit()

  # Notify user
  await update.callback_query.message.edit_text("✅ Job posted successfully!")
  return ConversationHandler.END

async def cancel_post_job_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.callback_query.message.edit_text("❌ Job posting canceled.")
  return ConversationHandler.END

async def post_job_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.message.reply_text("Job posting process has been canceled.", reply_markup=ReplyKeyboardRemove())
  return ConversationHandler.END

async def create_company_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  """Start the company creation process."""
  user_id = update.effective_user.id

  # Check if user is registered
  cur = conn.cursor()
  cur.execute("SELECT user_id FROM users WHERE telegram_id = %s", (user_id,))
  result = cur.fetchone()

  if not result:
    if update.callback_query:
      query = update.callback_query
      await query.edit_message_text("You need to register first!")
    else:
      await update.message.reply_text("You need to register first!", reply_markup=ReplyKeyboardRemove())  # Remove any existing keyboard
    return ConversationHandler.END

  # Save user ID in context for later use
  context.user_data['user_id'] = result[0]

  # await update.message.reply_text("Please enter the name of the company:")
  if update.callback_query:
    query = update.callback_query
    await query.edit_message_text(
      "Please enter the name of the company:"
    )
  else:
    await update.message.reply_text(
      "Please enter the name of the company:",
      reply_markup=ReplyKeyboardRemove()  # Remove any existing keyboard
    )

  return COMPANY_NAME

async def create_company_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
  """Save the company name and ask for a description."""
  context.user_data['company_name'] = update.message.text
  await update.message.reply_text("Please enter a description for the company:")
  return COMPANY_CONFIRM

async def create_company_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
  """Save the description and show confirmation."""
  context.user_data['company_description'] = update.message.text
  
  company_name = context.user_data.get("company_name")
  company_description = context.user_data.get("company_description")

  # Inline keyboard for confirmation
  keyboard = [
    [
      InlineKeyboardButton("Confirm", callback_data="confirm_create_company"),
      InlineKeyboardButton("Cancel", callback_data="cancel_create_company"),
    ]
  ]
  reply_markup = InlineKeyboardMarkup(keyboard)

  await update.message.reply_text(
    f"You're about to create a company with the following details:\n\n"
    f"**Name:** {company_name}\n"
    f"**Description:** {company_description}\n\n"
    "Do you confirm?",
    reply_markup=reply_markup,
    parse_mode="Markdown"
  )
  return COMPANY_CONFIRM

async def confirm_create_company_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
  # Get user data from the context
  user_id = update.effective_user.id
  company_name = context.user_data.get("company_name")
  company_description = context.user_data.get("company_description")

  # Check if user is registered
  cur = conn.cursor()
  cur.execute("SELECT user_id FROM users WHERE telegram_id = %s", (user_id,))
  result = cur.fetchone()

  if not result:
    if update.callback_query:
      query = update.callback_query
      await query.edit_message_text("You need to register as a user first!")
    else:
      await update.message.reply_text("You need to register as a user first!")
    return

  user_id = result[0]

  # Save the company to the database
  cur.execute(
    "INSERT INTO companies (name, description, user_id) VALUES (%s, %s, %s)",
    (company_name, company_description, user_id),
  )
  conn.commit()

  # Notify user
  await update.callback_query.message.edit_text("✅ Company created successfully!")
  return ConversationHandler.END

async def cancel_create_company_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.callback_query.message.edit_text("❌ Company creation canceled.")
  return ConversationHandler.END

async def create_company_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
  """Cancel the company creation process."""
  await update.message.reply_text("Company creation process has been canceled.")
  return ConversationHandler.END

async def list_companies(update: Update, context: ContextTypes.DEFAULT_TYPE):
  """List all companies owned by the user."""
  user_id = update.effective_user.id

  # Check if user is registered
  cur = conn.cursor()
  cur.execute("SELECT user_id FROM users WHERE telegram_id = %s", (user_id,))
  result = cur.fetchone()

  if not result:
    if update.callback_query:
      query = update.callback_query
      await query.edit_message_text("You need to register as a user first!")
    else:
      await update.message.reply_text("You need to register as a user first!")
    return

  user_id = result[0]

  # Fetch companies
  cur.execute("SELECT company_id, name, description FROM companies WHERE user_id = %s", (user_id,))
  companies = cur.fetchall()

  if not companies:
    if update.callback_query:
      query = update.callback_query
      await query.edit_message_text("You haven't created any companies yet.")
    else:
      await update.message.reply_text("You haven't created any companies yet.")
    return

  # Format the list of companies
  message = "**Your Companies:**\n"
  for company in companies:
    message += f"- **ID:** {company[0]}\n  **Name:** {company[1]}\n  **Description:** {company[2]}\n\n"

  if update.callback_query:
    query = update.callback_query
    await query.edit_message_text(message, parse_mode="Markdown")
  else:
    await update.message.reply_text(message, parse_mode="Markdown")

async def edit_company_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  """Start the edit company process by showing inline buttons for the user's companies."""
  user_id = update.effective_user.id

  # Check if user is registered
  cur = conn.cursor()
  cur.execute("SELECT user_id FROM users WHERE telegram_id = %s", (user_id,))
  result = cur.fetchone()

  if not result:
    await update.message.reply_text("You need to register as a user first!")
    return ConversationHandler.END

  user_id = result[0]

  # Fetch user's companies
  cur.execute("SELECT company_id, name FROM companies WHERE user_id = %s", (user_id,))
  companies = cur.fetchall()

  if not companies:
    await update.message.reply_text("You haven't created any companies yet.")
    return ConversationHandler.END

  # Create inline buttons for companies
  keyboard = [
    [InlineKeyboardButton(company[1], callback_data=f"edit_company_{company[0]}")]
    for company in companies
  ]
  reply_markup = InlineKeyboardMarkup(keyboard)

  await update.message.reply_text("Select the company you want to edit:", reply_markup=reply_markup)
  return EDIT_COMPANY_ID

async def edit_company_id_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
  """Handle company selection via callback and prompt for editing field."""
  query = update.callback_query
  await query.answer()

  # Extract company ID from callback data
  callback_data = query.data
  company_id = int(callback_data.replace("edit_company_", ""))

  # Fetch company details
  cur = conn.cursor()
  cur.execute("SELECT name, description FROM companies WHERE company_id = %s", (company_id,))
  company = cur.fetchone()

  if not company:
    await query.edit_message_text("Selected company does not exist.")
    return ConversationHandler.END

  # Save company details in context
  context.user_data['company_id'] = company_id
  context.user_data['company_name'] = company[0]
  context.user_data['company_description'] = company[1]

  # Display current details and buttons for editing options
  keyboard = [
    [
      InlineKeyboardButton("Edit Name", callback_data="edit_field_name"),
      InlineKeyboardButton("Edit Description", callback_data="edit_field_description"),
    ]
  ]
  reply_markup = InlineKeyboardMarkup(keyboard)

  await query.edit_message_text(
    f"Current details:\n\n**Name:** {company[0]}\n**Description:** {company[1]}\n\n"
    "What would you like to edit?",
    reply_markup=reply_markup
  )
  return EDIT_FIELD

async def edit_company_field_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
  """Handle the field selection and ask for the new value."""
  query = update.callback_query
  await query.answer()

  # Extract the field from callback data
  callback_data = query.data
  if callback_data == "edit_field_name":
    context.user_data['edit_field'] = "name"
    await query.edit_message_text("Please enter the new name for the company:")
  elif callback_data == "edit_field_description":
    context.user_data['edit_field'] = "description"
    await query.edit_message_text("Please enter the new description for the company:")
  else:
    await query.edit_message_text("Invalid selection.")
    return ConversationHandler.END

  return EDIT_VALUE

async def edit_company_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
  """Ask for confirmation before saving the updated field."""
  new_value = update.message.text
  edit_field = context.user_data['edit_field']

  # Save the new value in context
  context.user_data['new_value'] = new_value

  # Ask for confirmation with inline buttons
  keyboard = [
    [
      InlineKeyboardButton("Confirm", callback_data="confirm_save"),
      InlineKeyboardButton("Cancel", callback_data="cancel_save"),
    ]
  ]
  reply_markup = InlineKeyboardMarkup(keyboard)

  await update.message.reply_text(
    f"You are about to update the **{edit_field.capitalize()}** to:\n\n{new_value}\n\nDo you confirm?",
    reply_markup=reply_markup
  )
  return EDIT_VALUE

async def confirm_save_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
  """Save the updated field to the database after confirmation."""
  query = update.callback_query
  await query.answer()

  # Retrieve data from context
  company_id = context.user_data['company_id']
  edit_field = context.user_data['edit_field']
  new_value = context.user_data['new_value']

  # Update the database
  cur = conn.cursor()
  cur.execute(f"UPDATE companies SET {edit_field} = %s WHERE company_id = %s", (new_value, company_id))
  conn.commit()

  await query.edit_message_text(f"Company {edit_field.capitalize()} updated successfully!")
  return ConversationHandler.END


async def cancel_save_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
  """Cancel the save process."""
  query = update.callback_query
  await query.answer()

  await query.edit_message_text("The update has been canceled.")
  return ConversationHandler.END


async def edit_company_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
  """Cancel the edit process."""
  await update.message.reply_text("Editing process has been canceled.")
  return ConversationHandler.END



create_company_handler = ConversationHandler(
  entry_points=[CallbackQueryHandler(create_company_start, "create_company"), CommandHandler("create_company", create_company_start)],
  states={
    COMPANY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_company_name)],
    # COMPANY_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_company_description)],
    COMPANY_CONFIRM: [
      MessageHandler(filters.TEXT & ~filters.COMMAND, create_company_confirm),
      CallbackQueryHandler(confirm_create_company_callback, pattern="^confirm_create_company$"),
      CallbackQueryHandler(cancel_create_company_callback, pattern="^cancel_create_company$"),
    ],
  },
  fallbacks=[CommandHandler("cancel", create_company_cancel)],
)

edit_company_handler = ConversationHandler(
  entry_points=[CallbackQueryHandler(edit_company_start, "edit_company"), CommandHandler("edit_company", edit_company_start)],
  states={
    EDIT_COMPANY_ID: [CallbackQueryHandler(edit_company_id_callback, pattern="^edit_company_")],
    EDIT_FIELD: [CallbackQueryHandler(edit_company_field_callback, pattern="^edit_field_")],
    EDIT_VALUE: [
      MessageHandler(filters.TEXT & ~filters.COMMAND, edit_company_value),
      CallbackQueryHandler(confirm_save_callback, pattern="^confirm_save$"),
      CallbackQueryHandler(cancel_save_callback, pattern="^cancel_save$"),
    ],
  },
  fallbacks=[CommandHandler("cancel", edit_company_cancel)],
)

post_job_handler = ConversationHandler(
  entry_points=[CallbackQueryHandler(post_job_start, "post_job"), CommandHandler("post_job", post_job_start)],
  states={
    JOB_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, post_job_title)],
    JOB_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, post_job_description)],
    JOB_REQUIREMENTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, post_job_requirements)],
    JOB_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, post_job_location)],
    # JOB_SALARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, post_job_salary)],
    JOB_CONFIRM: [
      MessageHandler(filters.TEXT & ~filters.COMMAND, post_job_confirm),
      CallbackQueryHandler(confirm_post_job_callback, pattern="^confirm_post_job$"),
      CallbackQueryHandler(cancel_post_job_callback, pattern="^cancel_post_job$"),
    ],
  },
  fallbacks=[CommandHandler("cancel", post_job_cancel)],
)

# registration_handler = ConversationHandler(
#   entry_points=[CommandHandler("register", register)],
#   states={
#     ROLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, role_choice)],
#   },
#   fallbacks=[]
# )

def main():
  app = ApplicationBuilder().token(os.getenv('TOKEN')).build()

  # Command Handlers
  app.add_handler(CommandHandler("start", start))
  app.add_handler(CommandHandler("cancel", cancel))
  
  # Conversation Handlers
  app.add_handler(post_job_handler)  # Add the job posting conversation handler
  app.add_handler(create_company_handler)
  app.add_handler(edit_company_handler)

  # Feature-Specific Handlers
  app.add_handler(CallbackQueryHandler(register_role, pattern="register_.*"))
  # app.add_handler(CallbackQueryHandler(create_job, pattern="create_job"))
  app.add_handler(CallbackQueryHandler(view_job, pattern="view_job_.*"))
  app.add_handler(CallbackQueryHandler(list_companies, pattern="my_companies"))

  # General Callback Query Handlers (last to be invoked)
  app.add_handler(callback_handler)

  print("Bot is running...")
  app.run_polling()


if __name__ == "__main__":
  main()
