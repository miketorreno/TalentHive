import os
import logging
import psycopg2
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters, ApplicationBuilder, ContextTypes


# Logging
logging.basicConfig(
  format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG  # level=logging.INFO | logging.DEBUG
)
# logging.getLogger("httpx").setLevel(logging.WARNING)  # avoid all GET and POST requests being logged
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
CHOOSE_ACTION = range(10)

# Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE telegram_id = %s", (telegram_id,))
    user = cur.fetchone()
    
    if not user:
        keyboard = [
            [InlineKeyboardButton("Register", callback_data='register')],
        ]
        
        """Start the onboarding process."""
        await update.message.reply_text(
            "👋 Welcome to HulumJobs!\n\n"
            "Let’s get started.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return REGISTER
    else:
        keyboard = [
            ["My Profile", "My Applications"],
            ["Job Notifications", "Help"]
        ]
        await update.message.reply_text(
            text=f"<b>Hello {user[3]} 👋\t Welcome to HulumJobs!</b> \n\n"
                "<b>👤 \tMy Profile</b>:\t manage your profile \n\n"
                "<b>📑 \tMy Applications</b>:\t view and track your applications \n\n"
                "<b>🔔 \tJob Notifications</b>:\t customize notifications you wanna receive \n\n"
                "<b>❓ \tHelp</b>:\t show help message \n\n",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
            parse_mode='HTML'
        )


async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    choice = choice.lower()

    telegram_id = update.effective_user.id
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE telegram_id = %s", (telegram_id,))
    user = cur.fetchone()
    
    print(f"\n CHOICE: {choice} \n")
    
    if choice == "my profile":
        await update.message.reply_text(
            text=f"<b>My Profile</b> \n\n"
                f"<b>👤 \tName</b>: \t{user[3]} \n\n"
                f"<b>👤 \t Username</b>: \t{user[4]} \n\n"
                f"<b>👤 \t Gender</b>: \t{user[5]} \n\n"
                f"<b>🎂 \tDate of Birth</b>: \t{user[6]} \n\n"
                f"<b>🌐 \tCountry</b>: \t{user[9]} \n\n"
                f"<b>🏙️ \tCity</b>: \t{user[10]} \n\n"
                f"<b>📧 \tEmail</b>: \t{user[7]} \n\n"
                f"<b>📞 \tPhone</b>: \t{user[8]} \n\n",
            parse_mode='HTML'
        )
        return CHOOSE_ACTION
    elif choice == "my applications":
        await my_applications(update, context)
    elif choice == "job notifications":
        await update.message.reply_text("Job Notifications")
    elif choice == "help":
        await update.message.reply_text(
            text=f"<b>Help</b>\n\n"
                "<b>My Profile</b> - manage your profile \n\n"
                "<b>My Applications</b> - view and track your applications \n\n"
                "<b>Job Notifications</b> - customize notifications you wanna receive \n\n"
                "<b>Help</b> - show help message \n\n",
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text("Invalid choice. Please try again.")


#     await query.edit_message_text("Use the buttons to navigate the bot features.")


async def my_applications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE telegram_id = %s", (telegram_id,))
    user = cur.fetchone()

    cur.execute(
        "SELECT j.title, a.created_at, a.note FROM applications a JOIN jobs j ON a.job_id = j.job_id WHERE a.user_id = %s", (user[0],),
    )
    applications = cur.fetchall()

    if not applications:
        await update.message.reply_text("You haven't applied for any jobs yet.")
        return

    application_list = "\n\n".join(
        [f"**Job Title:** {app[0]}\n**Applied at:** {app[1]}\n**Note:** {app[2] or 'None'}" for app in applications]
    )
  
    await update.message.reply_text(
        f"**Your Applications:**\n\n{application_list}", 
        parse_mode="Markdown"
    )






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

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu))
    app.add_handler(onboarding_handler)
    
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
