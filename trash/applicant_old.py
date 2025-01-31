import os
# import redis
import logging
import psycopg2

from telegram import (
  Update,
  ReplyKeyboardMarkup,
  ReplyKeyboardRemove,
  InlineKeyboardButton,
  InlineKeyboardMarkup
)
from telegram.ext import (
  Updater,
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
  database="hulumjobs",
  user="postgres",
  password="postgres",
  port="5432"
)

logging.basicConfig(
  format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO  # level=logging.DEBUG, level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)  # avoid all GET and POST requests being logged
logger = logging.getLogger(__name__)



# Load environment variables
# DATABASE_URL = os.getenv("DATABASE_URL")
# REDIS_URL = os.getenv("REDIS_URL")

# Connect to PostgreSQL
# async def get_db_connection():
#     conn = psycopg2.connect(DATABASE_URL)
#     return conn

# Connect to Redis
# redis_client = redis.StrictRedis.from_url(REDIS_URL, decode_responses=True)


# Conversation states
NAME, GENDER, DOB, COUNTRY, CITY, PHONE, EMAIL, CONFIRM = range(8)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to the Applicant Bot! Let's start your registration.\n"
        "What is your full name?",
    )
    return NAME


async def collect_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    print("\n Name received: %s \n", name)
    # redis_client.hset(update.effective_user.id, "name", name)
    context.user_data["name"] = name
    await update.message.reply_text(
        "Great! Now, please select your gender:",
        reply_markup=ReplyKeyboardMarkup(
            [["Male", "Female"]], one_time_keyboard=True, resize_keyboard=True
        ),
    )
    print("\n Gender selection keyboard sent. \n")
    return GENDER


async def collect_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gender = update.message.text
    print("\n Received gender input: %s \n", gender)
    if gender not in ["Male", "Female"]:
        # await update.message.reply_text("Invalid selection. Please choose from Male or Female:")
        await update.message.reply_text(
            "Invalid selection. Please choose from Male, Female, or Other:",
            reply_markup=ReplyKeyboardMarkup(
                [["Male", "Female"]], one_time_keyboard=True, resize_keyboard=True
            )
        )
        return GENDER

    # redis_client.hset(update.effective_user.id, "gender", gender)
    context.user_data["gender"] = gender
    await update.message.reply_text("Please provide your date of birth (YYYY-MM-DD):")
    return DOB


async def collect_dob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dob = update.message.text
    try:
        # Simple validation
        from datetime import datetime
        datetime.strptime(dob, "%Y-%m-%d")
        # redis_client.hset(update.effective_user.id, "dob", dob)
        context.user_data["dob"] = dob
        await update.message.reply_text("Which country are you from?")
        return COUNTRY
    except ValueError:
        await update.message.reply_text("Invalid date format. Please use YYYY-MM-DD.")
        return DOB


async def collect_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    country = update.message.text
    # redis_client.hset(update.effective_user.id, "country", country)
    context.user_data["country"] = country
    await update.message.reply_text("Which city do you live in?")
    return CITY


async def collect_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = update.message.text
    # redis_client.hset(update.effective_user.id, "city", city)
    context.user_data["city"] = city
    await update.message.reply_text("Please provide your phone number:")
    return PHONE


async def collect_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text
    if not phone.isdigit() or len(phone) < 10:
        await update.message.reply_text("Invalid phone number. Please enter a valid number.")
        return PHONE

    # redis_client.hset(update.effective_user.id, "phone", phone)
    context.user_data["phone"] = phone
    await update.message.reply_text("Finally, provide your email address:")
    return EMAIL


async def collect_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text
    if "@" not in email or "." not in email:
        await update.message.reply_text("Invalid email address. Please enter a valid email.")
        return EMAIL

    # redis_client.hset(update.effective_user.id, "email", email)
    context.user_data["email"] = email
    # Display collected data for confirmation
    # user_data = redis_client.hgetall(update.effective_user.id)
    # user_data = context.user_data
    message = (
        "Please confirm your details:\n"
        f"Name: {context.user_data['name']}\n"
        f"Gender: {context.user_data['gender']}\n"
        f"DOB: {context.user_data['dob']}\n"
        f"Country: {context.user_data['country']}\n"
        f"City: {context.user_data['city']}\n"
        f"Phone: {context.user_data['phone']}\n"
        f"Email: {context.user_data['email']}\n"
        "Is this correct? (Yes/No)"
    )
    await update.message.reply_text(message, reply_markup=ReplyKeyboardMarkup([["Yes", "No"]], one_time_keyboard=True))
    return CONFIRM


async def confirm_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    confirmation = update.message.text
    if confirmation.lower() == "yes":
        telegram_id = update.effective_user.id
        username = update.effective_user.username
        role_id = 1  # Assuming role_id 1 is for job seekers

        # user_data = redis_client.hgetall(update.effective_user.id)
        # Save to database
        # conn = get_db_connection()
        # with conn.cursor() as cur:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO users (telegram_id, role_id, username, name, gender, dob, country, city, phone, email)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                telegram_id,
                role_id,
                username,
                context.user_data['name'],
                context.user_data['gender'],
                context.user_data['dob'],
                context.user_data['country'],
                context.user_data['city'],
                context.user_data['phone'],
                context.user_data['email'],
            ),
        )
        conn.commit()
        # conn.close()
        # redis_client.delete(update.effective_user.id)

        await update.message.reply_text("Thank you for registering! Your details have been saved.")
        return ConversationHandler.END

    else:
        await update.message.reply_text("Registration canceled. To start over, type /start.")
        # redis_client.delete(update.effective_user.id)
        return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Registration process has been canceled. Type /start to begin again.")
    # redis_client.delete(update.effective_user.id)
    return ConversationHandler.END


# Conversation handler
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_name)],
        GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_gender)],
        DOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_dob)],
        COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_country)],
        CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_city)],
        PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_phone)],
        EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_email)],
        CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_registration)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)


# Main function
def main():
    app = ApplicationBuilder().token(os.getenv('TOKEN')).build()
    
    app.add_handler(CommandHandler("start", start))
    
    app.add_handler(conv_handler)

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
