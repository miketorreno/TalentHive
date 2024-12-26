import os
import logging
import psycopg2
from datetime import date, datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
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
REGISTER, REGISTER_NAME, REGISTER_EMAIL, REGISTER_PHONE, REGISTER_GENDER, REGISTER_DOB, REGISTER_COUNTRY, REGISTER_CITY, CONFIRMATION, CHOOSE_ACTION = range(10)


# Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE telegram_id = %s AND role_id = 2", (telegram_id,))
    user = cur.fetchone()
    
    if not user:
        keyboard = [
            [InlineKeyboardButton("Register", callback_data='register')],
        ]
        
        """Start the onboarding process."""
        await update.message.reply_text(
            "<b>Hello there 👋\t Welcome to HulumJobs! </b>\n\n"
            "Let’s get started, Please click the button below to register.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        return REGISTER
    else:
        keyboard = [
            ["Post a Job", "My Job Posts"],
            ["My Companies", "Notifications"],
            ["My Profile", "Help"]
        ]
        await update.message.reply_text(
            text=f"<b>Hello {user[3]} 👋\t Welcome to HulumJobs!</b> \n\n"
                "<b>🔊 \tPost a Job</b>:\t post job to find the right candidates for you \n\n"
                "<b>📑 \tMy Job posts</b>:\t view & manage your job posts \n\n"
                "<b>🏢 \tMy Companies</b>:\t add & manage your companies \n\n"
                "<b>🔔 \tNotifications</b>:\t customize notifications you wanna receive \n\n"
                "<b>👤 \tMy Profile</b>:\t manage your profile \n\n"
                "<b>❓ \tHelp</b>:\t show help message \n\n",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
            parse_mode='HTML'
        )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "I hope we can talk again soon."
    )
    return ConversationHandler.END


async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    choice = choice.lower()

    if choice == "post a job":
        await update.message.reply_text("Post a job")
        # await post_a_job(update, context)
    elif choice == "my job posts":
        await update.message.reply_text("My Job Posts")
        # await my_job_posts(update, context)
    elif choice == "my companies":
        await my_companies(update, context)
    elif choice == "notifications":
        await update.message.reply_text("Notifications")
    elif choice == "my profile":
        await my_profile(update, context)
    elif choice == "help":
        await help(update, context)
    else:
        await update.message.reply_text("Please use the buttons below to navigate.")


# Company management



async def my_companies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all companies owned by the user."""
    user = get_user(update, context)
    
    # Fetch companies
    cur = conn.cursor()
    cur.execute("SELECT * FROM companies WHERE user_id = %s", (user[0],))
    companies = cur.fetchall()

    if not companies:
        await update.message.reply_text("You haven't created any companies yet.")
        return

    # Format the list of companies
    message = "**Your Companies:**\n"
    for company in companies:
        message += f"- **ID:** {company[0]}\n  **Name:** {company[2]}\n  **Description:** {company[3]}\n  **Approval status:** {company[4]}\n\n"

    await update.message.reply_text(message, parse_mode="Markdown")


async def my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update, context)
    
    await update.message.reply_text(
        text=f"<b>My Profile</b> \n\n"
            f"<b>👤 \tName</b>: \t{user[3]} \n\n"
            f"<b>👤 \tUsername</b>: \t{user[4]} \n\n"
            f"<b>👤 \tGender</b>: \t{user[5]} \n\n"
            f"<b>🎂 \tDate of Birth</b>: \t{user[6]} \n\n"
            f"<b>🌐 \tCountry</b>: \t{user[9]} \n\n"
            f"<b>🏙️ \tCity</b>: \t{user[10]} \n\n"
            f"<b>📧 \tEmail</b>: \t{user[7]} \n\n"
            f"<b>📞 \tPhone</b>: \t{user[8]} \n\n",
        parse_mode='HTML'
    )
    return


# TODO: postponed
async def job_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Job Notifications")


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        text=f"<b>Help</b>\n\n"
            "<b>Post a Job</b> - post job to find the right candidates for you \n\n"
            "<b>My Job posts</b> - view & manage your job posts \n\n"
            "<b>My Companies</b> - add & manage your companies \n\n"
            "<b>Notifications</b> - customize notifications you wanna receive \n\n"
            "<b>My Profile</b> - manage your profile \n\n"
            "<b>Help</b> - show help message \n\n",
        parse_mode="HTML",
    )
    return


# Onboarding
async def onboarding_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text=f"Please enter your full name",
        parse_mode='HTML'
    )
    return REGISTER_NAME


async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Please enter your email address")
    return REGISTER_EMAIL


async def register_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['email'] = update.message.text
    await update.message.reply_text("Please enter your phone number")
    return REGISTER_PHONE


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


async def register_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    context.user_data['gender'] = query.data if query.data != 'skip' else None
    await query.edit_message_text("Please enter your date of birth OR age?")
    return REGISTER_DOB


async def register_dob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        context.user_data['dob'] = update.message.text
    else:
        context.user_data['dob'] = None
    await update.message.reply_text("Please choose your country")
    return REGISTER_COUNTRY


async def register_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['country'] = update.message.text
    await update.message.reply_text("Please enter your city")
    return REGISTER_CITY


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
        f"<b>Do you confirm this information?</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    return CONFIRMATION


async def confirm_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    telegram_id = update.effective_user.id
    username = update.effective_user.username
    role_id = 2  # Assuming role_id is @ for the employer role
    
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


async def onboarding_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Registration canceled. Type /start to restart.")
    return ConversationHandler.END



# Helpers
def get_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE telegram_id = %s AND role_id = 2", (telegram_id,))
    user = cur.fetchone()
    return user


def format_date(date):
    return date.strftime("%B %d, %Y")



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
    
    app.add_handler(onboarding_handler)

    # main menu handler (general)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu))

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('cancel', cancel))
    
    print("Bot is running...")
    app.run_polling(timeout=60)


if __name__ == '__main__':
    main()
