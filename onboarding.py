import os
import logging
import psycopg2
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters, ApplicationBuilder, ContextTypes


# Logging
logging.basicConfig(
  format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG  # level=logging.INFO
)
# logging.getLogger("httpx").setLevel(logging.WARNING)  # avoid all GET and POST requests being logged
logger = logging.getLogger(__name__)

conn = psycopg2.connect(
  host="localhost",
  database="telegram_job_board",
  user="postgres",
  password="postgres",
  port="5432"
)

# Define states
CHOOSING_ROLE, REGISTER_NAME, REGISTER_EMAIL, REGISTER_PHONE, REGISTER_GENDER, \
REGISTER_DOB, REGISTER_COUNTRY, REGISTER_CITY, CONFIRMATION = range(9)

# Database connection
async def db_connect():
    return psycopg2.connect(
        dbname="telegram_job_board",
        user="postgres",
        password="postgres",
        host="localhost",
        port="5432"
    )

# Start onboarding
async def onboarding_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the onboarding process."""
    keyboard = [
        [InlineKeyboardButton("I'm a Job Seeker 🧑‍💼", callback_data='job_seeker')],
        [InlineKeyboardButton("I'm an Employer 🏢", callback_data='employer')],
    ]
    await update.message.reply_text(
        "👋 Welcome to HulumJobs!\n\n"
        "Let’s get started. Are you a job seeker or an employer?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CHOOSING_ROLE

# Handle role selection
async def choose_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['role'] = query.data
      
    if query.data == "employer":
        context.user_data['role_id'] = 1
    elif query.data == "job_seeker":
        context.user_data['role_id'] = 2
    elif query.data == "admin":
        context.user_data['role_id'] = 3
    # context.user_data['role_id'] = role_id
    
    await query.edit_message_text(
        f"Great! You've selected: *{'Job Seeker' if query.data == 'job_seeker' else 'Employer'}*\n\n"
        "Now, let's register your details. First, what's your name?",
        parse_mode='Markdown'
    )
    return REGISTER_NAME

# Collect user's name
async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Thanks! Now, please provide your email address.")
    return REGISTER_EMAIL

# Collect user's email
async def register_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['email'] = update.message.text
    await update.message.reply_text("Got it! What's your phone number?")
    return REGISTER_PHONE

# Collect user's phone number
async def register_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone'] = update.message.text
    keyboard = [
        [InlineKeyboardButton("Male", callback_data='male'), InlineKeyboardButton("Female", callback_data='female')],
        [InlineKeyboardButton("Skip", callback_data='skip')],
    ]
    await update.message.reply_text("What’s your gender? (Optional)", reply_markup=InlineKeyboardMarkup(keyboard))
    return REGISTER_GENDER

# Collect gender
async def register_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    context.user_data['gender'] = query.data if query.data != 'skip' else None
    await query.edit_message_text("Got it! What's your date of birth or age? (Optional)")
    return REGISTER_DOB

# Collect date of birth
async def register_dob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        context.user_data['dob'] = update.message.text
    else:
        context.user_data['dob'] = None
    await update.message.reply_text("What’s your country?")
    return REGISTER_COUNTRY

# Collect country
async def register_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['country'] = update.message.text
    await update.message.reply_text("And your city?")
    return REGISTER_CITY

# Collect city
async def register_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['city'] = update.message.text
    user_data = context.user_data
    keyboard = [
        [InlineKeyboardButton("Confirm ✅", callback_data='confirm')],
        [InlineKeyboardButton("Start Over 🔄", callback_data='restart')],
    ]
    await update.message.reply_text(
        f"🎉 Registration Summary:\n\n"
        f"Name: {user_data['name']}\n"
        f"Email: {user_data['email']}\n"
        f"Phone: {user_data['phone']}\n"
        f"Gender: {user_data.get('gender', 'Not Provided')}\n"
        f"Date of Birth/Age: {user_data.get('dob', 'Not Provided')}\n"
        f"Country: {user_data['country']}\n"
        f"City: {user_data['city']}\n\n"
        f"Do you confirm this information?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CONFIRMATION

# Confirm and save to database
async def confirm_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    telegram_id = update.effective_user.id
    username = update.effective_user.username
    
    if query.data == 'confirm':
        user_data = context.user_data
        # conn = db_connect()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (telegram_id, role_id, name, username, email, phone, gender, dob, country, city) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (telegram_id, user_data['role_id'], user_data['name'], username, user_data['email'], user_data['phone'],
             user_data.get('gender'), user_data.get('dob'), user_data['country'], user_data['city'])
        )
        conn.commit()
        # cur.close()
        # conn.close()
        await query.edit_message_text("🎉 Registration complete! Welcome to HulumJobs!")
    elif query.data == 'restart':
        await query.edit_message_text("Let's start over. Use /start to begin again.")
    return ConversationHandler.END

# Cancel command
async def onboarding_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Registration canceled. Type /start to restart.")
    return ConversationHandler.END

# Onboarding conversation handler
def get_onboarding_handler():
    return ConversationHandler(
        # entry_points=[CommandHandler('onboarding_start', onboarding_start)],
        entry_points=[CallbackQueryHandler(onboarding_start)],
        states={
            CHOOSING_ROLE: [CallbackQueryHandler(choose_role)],
            REGISTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)],
            REGISTER_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_email)],
            REGISTER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_phone)],
            REGISTER_GENDER: [CallbackQueryHandler(register_gender)],
            REGISTER_DOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_dob)],
            REGISTER_COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_country)],
            REGISTER_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_city)],
            CONFIRMATION: [CallbackQueryHandler(confirm_registration)],
        },
        fallbacks=[CommandHandler('onboarding_cancel', onboarding_cancel)],
    )

# Main function
# def main():
#     app = ApplicationBuilder().token(os.getenv('TOKEN')).build()

#     onboarding_handler = ConversationHandler(
#         entry_points=[CommandHandler('onboarding_start', onboarding_start)],
#         states={
#             CHOOSING_ROLE: [CallbackQueryHandler(choose_role)],
#             REGISTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)],
#             REGISTER_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_email)],
#             REGISTER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_phone)],
#             REGISTER_GENDER: [CallbackQueryHandler(register_gender)],
#             REGISTER_DOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_dob)],
#             REGISTER_COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_country)],
#             REGISTER_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_city)],
#             CONFIRMATION: [CallbackQueryHandler(confirm_registration)],
#         },
#         fallbacks=[CommandHandler('onboarding_cancel', onboarding_cancel)],
#     )

#     app.add_handler(onboarding_handler)
    
#     print("Bot is running...")
#     app.run_polling()

# if __name__ == '__main__':
#     main()
