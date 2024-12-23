import os
import logging
import psycopg2
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters, ApplicationBuilder, ContextTypes


# Logging
logging.basicConfig(
  format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO  # level=logging.INFO | logging.DEBUG
)
logging.getLogger("httpx").setLevel(logging.WARNING)  # avoid all GET and POST requests being logged
logger = logging.getLogger(__name__)


# Connect to PostgreSQL
conn = psycopg2.connect(
  host="localhost",
  database="hulumjobs",
  user="postgres",
  password="postgres",
  port="5432"
)


# Define states
REGISTER, REGISTER_NAME, REGISTER_EMAIL, REGISTER_PHONE, REGISTER_GENDER, REGISTER_DOB, REGISTER_COUNTRY, REGISTER_CITY, CONFIRMATION = range(9)


# Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the onboarding process."""
    keyboard = [
        [InlineKeyboardButton("Register", callback_data='register')],
    ]
    await update.message.reply_text(
        "👋 Welcome to HulumJobs!\n\n"
        "Let’s get started.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return REGISTER


# Start onboarding
async def onboarding_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text=f"Please enter your full name",
        parse_mode='HTML'
    )
    return REGISTER_NAME


# Collect name
async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Please enter your email address")
    return REGISTER_EMAIL


# Collect email
async def register_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['email'] = update.message.text
    await update.message.reply_text("Please enter your phone number")
    return REGISTER_PHONE


# Collect phone number
async def register_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone'] = update.message.text
    keyboard = [
        [InlineKeyboardButton("Male", callback_data='male'), InlineKeyboardButton("Female", callback_data='female')],
        [InlineKeyboardButton("Skip", callback_data='skip')],
    ]
    await update.message.reply_text(
        "Please choose your gender", 
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return REGISTER_GENDER


# Collect gender
async def register_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    context.user_data['gender'] = query.data if query.data != 'skip' else None
    await query.edit_message_text("Please enter your date of birth OR age?")
    return REGISTER_DOB


# Collect date of birth
async def register_dob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        context.user_data['dob'] = update.message.text
    else:
        context.user_data['dob'] = None
    await update.message.reply_text("Please choose your country")
    return REGISTER_COUNTRY


# Collect country
async def register_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['country'] = update.message.text
    await update.message.reply_text("Please enter your city")
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
        f"<b>ACCOUNT INFORMATION</b>\n\n"
        f"<b>Name</b>: {user_data['name']}\n\n"
        f"<b>Email</b>: {user_data['email']}\n\n"
        f"<b>Phone</b>: {user_data['phone']}\n\n"
        f"<b>Gender</b>: {user_data.get('gender', '')}\n\n"
        f"<b>Date of Birth (Age)</b>: {user_data.get('dob', '')}\n\n"
        f"<b>Country</b>: {user_data['country']}\n\n"
        f"<b>City</b>: {user_data['city']}\n\n"
        f"</b>Do you confirm this information?</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    return CONFIRMATION


# Confirm and save to database
async def confirm_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    telegram_id = update.effective_user.id
    username = update.effective_user.username
    role_id = 1  # Assuming role_id is 1 for the applicant role
    
    if query.data == 'confirm':
        user_data = context.user_data
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (telegram_id, role_id, name, username, email, phone, gender, dob, country, city) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (telegram_id, role_id, user_data['name'], username, user_data['email'], user_data['phone'],
             user_data.get('gender'), user_data.get('dob'), user_data['country'], user_data['city'])
        )
        conn.commit()

        await query.edit_message_text("🎉 Registration complete! Welcome to HulumJobs!")
    elif query.data == 'restart':
        await query.edit_message_text("Let's start over. Use /start to begin again.")
    return ConversationHandler.END


# Cancel command
async def onboarding_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Registration canceled. Type /start to restart.")
    return ConversationHandler.END



onboarding_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(onboarding_start, 'register')],
    states={
        REGISTER: [CallbackQueryHandler(onboarding_start)],
        REGISTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)],
        REGISTER_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_email)],
        REGISTER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_phone)],
        REGISTER_GENDER: [CallbackQueryHandler(register_gender)],
        REGISTER_DOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_dob)],
        REGISTER_COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_country)],
        REGISTER_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_city)],
        CONFIRMATION: [CallbackQueryHandler(confirm_registration)],
    },
    fallbacks=[CommandHandler('cancel', onboarding_cancel)],
)


def main():
    app = ApplicationBuilder().token(os.getenv('TOKEN')).build()

    app.add_handler(CommandHandler('start', start))

    app.add_handler(onboarding_handler)
    
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
