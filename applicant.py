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
REGISTER, REGISTER_NAME, REGISTER_EMAIL, REGISTER_PHONE, REGISTER_GENDER, REGISTER_DOB, REGISTER_COUNTRY, REGISTER_CITY, CONFIRMATION, CHOOSE_ACTION, COVER_LETTER, NEW_CV, CONFIRM_APPLY = range(13)

current_job_index = 0
current_saved_job_index = 0


# Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update, context)
    
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
        args = context.args
        if args and args[0].startswith("apply_"):
            job_id = args[0].split("_")[1]
            await show_job(update, context, job_id)
        else:
            keyboard = [
                ["Browse Jobs", "Saved Jobs"],
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


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hope we can talk again soon."
    )
    return ConversationHandler.END


async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    choice = choice.lower()

    if choice == "browse jobs":
        await browse_jobs(update, context)
    elif choice == "saved jobs":
        await saved_jobs(update, context)
    elif choice == "my profile":
        await my_profile(update, context)
    elif choice == "my applications":
        await my_applications(update, context)
    elif choice == "job notifications":
        await job_notifications(update, context)
    elif choice == "help":
        await help(update, context)
    else:
        await update.message.reply_text("Please use the buttons below to navigate.")


async def show_job(update: Update, context: ContextTypes.DEFAULT_TYPE, job_id: str):
    cur = conn.cursor()
    cur.execute("SELECT * FROM jobs WHERE job_id = %s", (job_id,))
    job = cur.fetchone()
    
    if not job:
        await update.message.reply_text("Job not found.")
        return
    
    job_details = f"\nJob Title: <b>\t{job[5]}</b> \n\nJob Type: <b>\t{job[4]}</b> \n\nWork Location: <b>\t{job[8]}, {job[9]}</b> \n\nSalary: <b>\t{job[10]}</b> \n\nDeadline: <b>\t{format_date(job[11])}</b> \n\n<b>Description</b>: \t{job[6]} \n\n"

    keyboard = [
        [InlineKeyboardButton("Apply", callback_data=f'apply_{job[0]}')]
    ]

    await update.message.reply_text(
        text=job_details,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def browse_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cur = conn.cursor()
    cur.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT 25")
    jobs = cur.fetchall()
    
    if not jobs:
        await update.message.reply_text("No jobs available at the moment.")
        return

    job_list = [job for job in jobs]
    global current_job_index
    job = job_list[current_job_index]
    # current_job_index = 0  # Reset index when starting
    
    job_details = f"\nJob Title: <b>\t{job[5]}</b> \n\nJob Type: <b>\t{job[4]}</b> \n\nWork Location: <b>\t{job[8]}, {job[9]}</b> \n\nSalary: <b>\t{job[10]}</b> \n\nDeadline: <b>\t{format_date(job[11])}</b> \n\n<b>Description</b>: \t{job[6]} \n\n"

    # keyboard = []
    # if current_job_index > 0:
    #     keyboard.append([InlineKeyboardButton("Previous", callback_data='job_previous')])
    # if current_job_index < len(job_list) - 1:
    #     keyboard.append([InlineKeyboardButton("Next", callback_data='job_next')])

    if current_job_index > 0:
        keyboard = [
            [
                InlineKeyboardButton("Previous", callback_data='job_previous'),
                InlineKeyboardButton("Next", callback_data='job_next'),
            ],
            [InlineKeyboardButton("Apply", callback_data=f'apply_{job[0]}')]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("Next", callback_data='job_next')],
            [InlineKeyboardButton("Apply", callback_data=f'apply_{job[0]}')]
        ]

    await update.message.reply_text(
        text=job_details,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def next_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_job_index
    query = update.callback_query
    await query.answer()  # Acknowledge the callback

    if query.data == 'job_next':
        current_job_index += 1
    elif query.data == 'job_previous':
        current_job_index -= 1

    await browse_jobs(query, context)


async def next_saved_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_saved_job_index
    query = update.callback_query
    await query.answer()  # Acknowledge the callback

    if query.data == 'saved_job_next':
        current_saved_job_index += 1
    elif query.data == 'saved_job_previous':
        current_saved_job_index -= 1

    await my_applications(update, context)



# APPLYING FOR JOBS
async def apply_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['job_id'] = int(query.data.split("_")[-1])
    keyboard = [
        [InlineKeyboardButton("Skip", callback_data='skip_cover_letter')],
    ]
    
    await query.edit_message_text(
        "Please enter your cover letter or click skip",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return COVER_LETTER


async def cover_letter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['cover_letter'] = update.message.text
    keyboard = [
        [InlineKeyboardButton("Skip", callback_data='skip_new_cv')],
    ]
    
    await update.message.reply_text(
        "Would you like to submit a new CV",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return NEW_CV


async def skip_cover_letter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['cover_letter'] = None
    keyboard = [
        [InlineKeyboardButton("Skip", callback_data='skip_new_cv')],
    ]
    
    await query.edit_message_text(
        "Would you like to submit a new CV",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return NEW_CV


async def new_cv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_cv'] = update.message.text
    keyboard = [
        [InlineKeyboardButton("Confirm", callback_data='confirm_apply')],
        [InlineKeyboardButton("Cancel", callback_data='cancel_apply')],
    ]
    
    await update.message.reply_text(
        f"<b>Cover Letter</b>: {context.user_data['cover_letter']}\n\n"
        f"<b>CV</b>: {context.user_data['new_cv']}\n\n"
        f"<b>Apply for the job?</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    return CONFIRM_APPLY


async def skip_new_cv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['new_cv'] = None
    keyboard = [
        [InlineKeyboardButton("Confirm", callback_data='confirm_apply')],
        [InlineKeyboardButton("Cancel", callback_data='cancel_apply')],
    ]
    
    await query.edit_message_text(
        f"<b>Cover Letter</b>: {context.user_data['cover_letter']}\n\n"
        f"<b>CV</b>: {context.user_data['new_cv']}\n\n"
        f"<b>Apply for the job?</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    return CONFIRM_APPLY


async def confirm_apply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    telegram_id = update.effective_user.id
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM users WHERE telegram_id = %s AND role_id = 1", (telegram_id,))
    user = cur.fetchone()
    
    # checking duplicate
    cur.execute("SELECT * FROM applications WHERE job_id = %s AND user_id = %s", (context.user_data['job_id'], user[0]))
    duplicate = cur.fetchone()
    if duplicate:
        await query.edit_message_text("You have already applied for this job.")
        return ConversationHandler.END
    
    cur.execute(
        "INSERT INTO applications (job_id, user_id, cover_letter, cv) VALUES (%s, %s, %s, %s)",
        (context.user_data['job_id'], user[0], context.user_data['cover_letter'], context.user_data['new_cv']),
    )
    conn.commit()

    # # Fetch job poster's details
    # cur.execute("SELECT user_id, title FROM jobs WHERE job_id = %s", (job_id,))
    # job_poster_id, job_title = cur.fetchone()

    # cur.execute("SELECT telegram_id, name FROM users WHERE user_id = %s", (job_poster_id,))
    # job_poster_telegram_id, job_poster_name = cur.fetchone()


    # # Notify job poster
    # await context.bot.send_message(
    #     chat_id=job_poster_telegram_id,
    #     text=f"📢 A new application has been submitted for your job:\n\n"
    #     f"<b>Job Title:</b> {job_title}\n"
    #     f"<b>Applicant:</b> {update.effective_user.first_name}\n"
    #     f"<b>Note:</b> {job_note or 'None'}",
    #     parse_mode="HTML",
    # )

    await query.edit_message_text("Application submitted successfully!")
    return ConversationHandler.END


async def cancel_apply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        query = update.callback_query
        await query.edit_message_text("Application canceled.")
    else:
        await update.message.reply_text("Application canceled.")
    return ConversationHandler.END



async def saved_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Saved Jobs")


async def my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE telegram_id = %s AND role_id = 1", (telegram_id,))
    user = cur.fetchone()
    
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


async def my_applications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        telegram_id = update.callback_query.from_user.id
    else:
        telegram_id = update.effective_user.id
        
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE telegram_id = %s AND role_id = 1", (telegram_id,))
    user = cur.fetchone()

    cur.execute(
        "SELECT j.*, a.* FROM applications a JOIN jobs j ON a.job_id = j.job_id WHERE a.user_id = %s ORDER BY a.created_at DESC LIMIT 25", (user[0],),
    )
    applications = cur.fetchall()

    if not applications:
        if update.callback_query:
            await update.callback_query.edit_message_text("You haven't applied for any jobs yet.")
        else:
            await update.message.reply_text("You haven't applied for any jobs yet.")
        return

    application_list = [job for job in applications]
    global current_saved_job_index
    application = application_list[current_saved_job_index]
    # current_saved_job_index = 0  # Reset index when starting
    
    application_details = f"\nJob Title: <b>\t{application[5]}</b> \n\nJob Type: <b>\t{application[4]}</b> \n\nWork Location: <b>\t{application[8]}, {application[9]}</b> \n\nSalary: <b>\t{application[10]}</b> \n\nDeadline: <b>\t{format_date(application[11])}</b> \n\n<b>Description</b>: \t{application[6]} \n\n<b>__________________</b>\n\n<b>Applied at</b>: \t{format_date(application[24])} \n\n<b>Application Status</b>: \t{application[23].upper()} \n\n"

    # keyboard = []
    # if current_saved_job_index > 0:
    #     keyboard.append([InlineKeyboardButton("Previous", callback_data='job_previous')])
    # if current_saved_job_index < len(job_list) - 1:
    #     keyboard.append([InlineKeyboardButton("Next", callback_data='job_next')])

    if current_saved_job_index > 0:
        keyboard = [
            [
                InlineKeyboardButton("Previous", callback_data='saved_job_previous'),
                InlineKeyboardButton("Next", callback_data='saved_job_next'),
            ],
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("Next", callback_data='saved_job_next')],
        ]

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=application_details,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            text=application_details,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    return


# TODO: postponed
async def job_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Job Notifications")


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        text=f"<b>Help</b>\n\n"
            "<b>My Profile</b> - manage your profile \n\n"
            "<b>My Applications</b> - view and track your applications \n\n"
            "<b>Job Notifications</b> - customize notifications you wanna receive \n\n"
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



# Helpers
def get_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE telegram_id = %s AND role_id = 1", (telegram_id,))
    user = cur.fetchone()
    return user


def format_date(date):
    return date.strftime("%B %d, %Y")



# Conversation handlers
apply_job_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(apply_start, "apply"), CommandHandler("apply", apply_start)],
    states={
        COVER_LETTER: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, cover_letter),
            CallbackQueryHandler(skip_cover_letter, pattern="skip_cover_letter")
        ],
        NEW_CV: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, new_cv),
            CallbackQueryHandler(skip_new_cv, pattern="skip_new_cv")
        ],
        CONFIRM_APPLY: [
            CallbackQueryHandler(confirm_apply, pattern="confirm_apply"),
            CallbackQueryHandler(cancel_apply, pattern="cancel_apply"),
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel_apply)],
)


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
    
    app.add_handler(CallbackQueryHandler(next_job, pattern="^job_.*"))
    app.add_handler(CallbackQueryHandler(next_saved_job, pattern="^saved_job_.*"))

    app.add_handler(apply_job_handler)
    app.add_handler(onboarding_handler)

    # main menu handler (general)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu))

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('cancel', cancel))
    
    print("Bot is running...")
    app.run_polling(timeout=60)


if __name__ == '__main__':
    main()
