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
  ApplicationBuilder,
  ContextTypes,
  CommandHandler,
  MessageHandler,
  ConversationHandler,
  CallbackQueryHandler,
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
  format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

ROLE, COMPLETE = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  keyboard = [
    [InlineKeyboardButton("Register", callback_data="register")],
    [InlineKeyboardButton("Browse Jobs", callback_data="browse_jobs")],
    [InlineKeyboardButton("Post a Job", callback_data="post_job")],
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
  elif query.data == "post_job":
    await post_job(update, context)
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

  # Feature-Specific Handlers
  app.add_handler(CallbackQueryHandler(register_role, pattern="register_.*"))
  app.add_handler(CallbackQueryHandler(create_job, pattern="create_job"))
  app.add_handler(CallbackQueryHandler(view_job, pattern="view_job_.*"))

  # Callback Query Handlers
  app.add_handler(callback_handler)

  print("Bot is running...")
  app.run_polling()


if __name__ == "__main__":
  main()
