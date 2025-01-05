import os
import re
import sys
import json
import signal
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

def shutdown_handler(signal_received, frame):
    if conn:
        conn.close()
        print("Database connection closed.")
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown_handler)


# Define states
REGISTER, REGISTER_NAME, REGISTER_FIRSTNAME, REGISTER_LASTNAME, REGISTER_EMAIL, REGISTER_PHONE, REGISTER_GENDER, REGISTER_DOB, REGISTER_COUNTRY, REGISTER_CITY, CONFIRMATION, CHOOSE_ACTION, COVER_LETTER, NEW_CV, PORTFOLIO, CONFIRM_APPLY = range(16)

# List of cities sorted alphabetically
CITIES = sorted([
    "Addis Ababa", "Adama", "Adigrat", "Adwa", "Agaro", "Alaba Kulito", "Alamata", "Aleta Wendo",
    "Ambo", "Arba Minch", "Areka", "Arsi Negele", "Assosa", "Awassa", "Axum", "Bahir Dar",
    "Bale Robe", "Bedessa", "Bishoftu", "Boditi", "Bonga", "Burayu", "Batu", "Butajira",
    "Chiro", "Dambacha", "Dangila", "Debre Birhan", "Debre Mark'os", "Debre Tabor", "Dessie",
    "Dembi Dolo", "Dilla", "Dire Dawa", "Durame", "Fiche", "Finote Selam", "Gambela",
    "Goba", "Gode", "Gimbi", "Gonder", "Haramaya", "Harar", "Hosaena", "Jimma", "Jijiga",
    "Jinka", "Kobo", "Kombolcha", "Mekelle", "Meki", "Metu", "Mizan Teferi", "Mojo",
    "Mota", "Nekemte", "Negele Borana", "Sawla", "Sebeta", "Shashamane", "Shire", "Sodo",
    "Tepi", "Waliso", "Weldiya", "Welkite", "Wukro", "Yirgalem", "Ziway"
])

# Page size for the inline buttons
PAGE_SIZE = 14  # 7 rows × 2 columns

current_job_index = 0
total_jobs = 0
current_saved_job_index = 0
total_saved_jobs = 0


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
                # ["Job Notifications", "Help"]
                ["Help"]
            ]
            await update.message.reply_text(
                text=f"<b>Hello {(user[3].split()[0]).capitalize()} 👋\t Welcome to HulumJobs!</b> \n\n"
                    "<b>💼 \tBrowse Jobs</b>:\t find jobs that best fit your schedule \n\n"
                    "<b>📌 \tSaved Jobs</b>:\t your saved jobs \n\n"
                    "<b>👤 \tMy Profile</b>:\t manage your profile \n\n"
                    "<b>📑 \tMy Applications</b>:\t view and track your applications \n\n"
                    # "<b>🔔 \tJob Notifications</b>:\t customize notifications you wanna receive \n\n"
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
    user = get_user(update, context)
    
    if not user:
        await start(update, context)
        return

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
        if update.callback_query:
            await update.callback_query.answer("Job not found.")
        else:
            await update.message.reply_text("Job not found.")
        return
    
    job_details = f"\nJob Title: <b>\t{job[5]}</b> \n\nJob Type: <b>\t{job[4]}</b> \n\nWork Location: <b>\t{job[8]}, {job[9]}</b> \n\nSalary: <b>\t{job[10]}</b> \n\nDeadline: <b>\t{format_date(job[11])}</b> \n\n<b>Description</b>: \t{job[6]} \n\n"

    keyboard = [
        [InlineKeyboardButton("Apply", callback_data=f'apply_{job[0]}')]
    ]

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=job_details,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            text=job_details,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )


async def browse_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cur = conn.cursor()
    cur.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT 50")
    jobs = cur.fetchall()
    
    if not jobs:
        if update.callback_query:
            await update.callback_query.edit_message_text("No jobs available at the moment.")
        else:
            await update.message.reply_text("No jobs available at the moment.")
        return

    job_list = [job for job in jobs]
    global current_job_index
    job = job_list[current_job_index]
    global total_jobs
    total_jobs = len(job_list)
    # current_job_index = 0  # Reset index when starting
    
    # job_details = f"\nJob Title: <b>\t{job[5]}</b> \n\nJob Type: <b>\t{job[4]}</b> \n\nWork Location: <b>\t{job[8]}, {job[9]}</b> \n\nSalary: <b>\t{job[10]}</b> \n\nDeadline: <b>\t{format_date(job[11])}</b> \n\n<b>Description</b>: \t{job[6]} \n\n"
    
    job_details = f"\nJob Title: <b>\t{job[5]}</b> \n\nJob Type: <b>\t{job[4]}</b> \n\nWork Location: <b>\t{job[8]}, {job[9]}</b> \n\nSalary: <b>\t{job[10]}</b> \n\nDeadline: <b>\t{format_date(job[11])}</b> \n\n<b>Description</b>: \n{job[6]} \n\n<b>Requirements</b>: \n{job[7]} \n\n"
    

    # keyboard = []
    # if current_job_index > 0:
    #     keyboard.append([InlineKeyboardButton("Previous", callback_data='job_previous')])
    # if current_job_index < len(job_list) - 1:
    #     keyboard.append([InlineKeyboardButton("Next", callback_data='job_next')])
    
    if total_jobs > 1:
        if current_job_index > 0:
            keyboard = [
                [
                    InlineKeyboardButton("Previous", callback_data='job_previous'),
                    InlineKeyboardButton("Next", callback_data='job_next'),
                ],
                [InlineKeyboardButton("Apply", callback_data=f'apply_{job[0]}')]
            ]
            if total_jobs == current_job_index + 1:
                keyboard = [
                    [InlineKeyboardButton("Previous", callback_data='job_previous')],
                    [InlineKeyboardButton("Apply", callback_data=f'apply_{job[0]}')]
                ]
        else:
            keyboard = [
                [InlineKeyboardButton("Next", callback_data='job_next')],
                [InlineKeyboardButton("Apply", callback_data=f'apply_{job[0]}')]
            ]
    else:
        keyboard = []

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=job_details,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            text=job_details,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    return


async def next_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_job_index
    query = update.callback_query
    await query.answer()  # Acknowledge the callback

    if query.data == 'job_next':
        current_job_index += 1
    elif query.data == 'job_previous':
        current_job_index -= 1

    await browse_jobs(update, context)


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
    keyboard = [[InlineKeyboardButton("Skip", callback_data='skip_cover_letter')]]
    
    await query.edit_message_text(
        "Please write cover letter or click skip \n\n<i>*enter less than 500 characters</i>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    return COVER_LETTER


async def cover_letter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['cover_letter'] = update.message.text
    
    keyboard = [[InlineKeyboardButton("Skip", callback_data='skip_new_cv')]]
    await update.message.reply_text(
        "Would you like to submit a new CV \n\n<i>*please upload pdf or word document</i>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    return NEW_CV
    # # cur = conn.cursor()
    # # cur.execute("SELECT * FROM jobs WHERE job_id = %s", (context.user_data['job_id'],))
    # # job = cur.fetchone()
    # job = get_job(update, context, context.user_data['job_id'])

    # job_details = f"\nJob Title: <b>\t{job[5]}</b> \n\nJob Type: <b>\t{job[4]}</b> \n\nWork Location: <b>\t{job[8]}, {job[9]}</b> \n\nSalary: <b>\t{job[10]}</b> \n\nDeadline: <b>\t{format_date(job[11])}</b> \n\n<b>Description</b>: \n{job[6]} \n\n<b>Requirements</b>: \n{job[7]} \n\n"
    
    # keyboard = [
    #     [InlineKeyboardButton("Confirm", callback_data='confirm_apply')],
    #     [InlineKeyboardButton("Cancel", callback_data='cancel_apply')],
    # ]
    
    # await update.message.reply_text(
    #     f"{job_details}"
    #     f"<b>__________________</b>\n\n"
    #     f"<b>Cover Letter</b> \n{context.user_data['cover_letter']}\n\n\n"
    #     f"<b>Apply for the job?</b>",
    #     reply_markup=InlineKeyboardMarkup(keyboard),
    #     parse_mode='HTML'
    # )
    # return CONFIRM_APPLY


async def skip_cover_letter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['cover_letter'] = None
    
    keyboard = [[InlineKeyboardButton("Skip", callback_data='skip_new_cv')]]
    await query.edit_message_text(
        "Would you like to submit a new CV \n\n<i>*please upload pdf or word document</i>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    return NEW_CV
    # # cur = conn.cursor()
    # # cur.execute("SELECT * FROM jobs WHERE job_id = %s", (context.user_data['job_id'],))
    # # job = cur.fetchone()
    # job = get_job(update, context, context.user_data['job_id'])
    
    # job_details = f"\nJob Title: <b>\t{job[5]}</b> \n\nJob Type: <b>\t{job[4]}</b> \n\nWork Location: <b>\t{job[8]}, {job[9]}</b> \n\nSalary: <b>\t{job[10]}</b> \n\nDeadline: <b>\t{format_date(job[11])}</b> \n\n<b>Description</b>: \n{job[6]} \n\n<b>Requirements</b>: \n{job[7]} \n\n"
    
    # keyboard = [
    #     [InlineKeyboardButton("Confirm", callback_data='confirm_apply')],
    #     [InlineKeyboardButton("Cancel", callback_data='cancel_apply')],
    # ]
    
    # await query.edit_message_text(
    #     f"{job_details}"
    #     f"<b>__________________</b>\n\n"
    #     f"<b>Cover Letter</b> \n{context.user_data['cover_letter']}\n\n\n"
    #     f"<b>Apply for the job?</b>",
    #     reply_markup=InlineKeyboardMarkup(keyboard),
    #     parse_mode='HTML'
    # )
    # return CONFIRM_APPLY


async def new_cv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.document:
        # Validate the file type
        file_name = update.message.document.file_name
        if not file_name.endswith(('.pdf', '.doc', '.docx')):
            await update.message.reply_text("Invalid file type. Please upload a PDF or Word document.")
            return NEW_CV

        # Save the file ID
        context.user_data['new_cv'] = update.message.document.file_id
        
        keyboard = [[InlineKeyboardButton("Skip", callback_data='skip_portfolio')]]
        await update.message.reply_text(
            "Please provide portfolio links (separated by commas)",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        return PORTFOLIO
    else:
        await update.message.reply_text("Please upload a valid document.")
        return NEW_CV

    # context.user_data['new_cv'] = update.message.text
    
    # keyboard = [
    #     [InlineKeyboardButton("Confirm", callback_data='confirm_apply')],
    #     [InlineKeyboardButton("Cancel", callback_data='cancel_apply')],
    # ]
    # await update.message.reply_text(
    #     f"<b>Cover Letter</b>: {context.user_data['cover_letter']}\n\n"
    #     f"<b>CV</b>: {context.user_data['new_cv']}\n\n"
    #     f"<b>Apply for the job?</b>",
    #     reply_markup=InlineKeyboardMarkup(keyboard),
    #     parse_mode='HTML'
    # )
    # return CONFIRM_APPLY


async def skip_new_cv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['new_cv'] = None
        
    keyboard = [[InlineKeyboardButton("Skip", callback_data='skip_portfolio')]]
    await query.edit_message_text(
        "Please provide portfolio links (separated by commas)",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    return PORTFOLIO
    
    # keyboard = [
    #     [InlineKeyboardButton("Confirm", callback_data='confirm_apply')],
    #     [InlineKeyboardButton("Cancel", callback_data='cancel_apply')],
    # ]
    # await query.edit_message_text(
    #     f"<b>Cover Letter</b>: {context.user_data['cover_letter']}\n\n"
    #     f"<b>CV</b>: {context.user_data['new_cv']}\n\n"
    #     f"<b>Apply for the job?</b>",
    #     reply_markup=InlineKeyboardMarkup(keyboard),
    #     parse_mode='HTML'
    # )
    # return CONFIRM_APPLY


async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['portfolio'] = update.message.text.split(',') if update.message.text else []

    job = get_job(update, context, context.user_data['job_id'])
    
    job_details = f"\nJob Title: <b>\t{job[5]}</b> \n\nJob Type: <b>\t{job[4]}</b> \n\nWork Location: <b>\t{job[8]}, {job[9]}</b> \n\nSalary: <b>\t{job[10]}</b> \n\nDeadline: <b>\t{format_date(job[11])}</b> \n\n<b>Description</b>: \n{job[6]} \n\n<b>Requirements</b>: \n{job[7]} \n\n"
    
    # if context.user_data['new_cv']:
    #     file = await context.bot.get_file(context.user_data['new_cv'])
        
    keyboard = [
        [InlineKeyboardButton("Confirm", callback_data='confirm_apply')],
        [InlineKeyboardButton("Cancel", callback_data='cancel_apply')],
    ]
    await update.message.reply_text(
        f"{job_details}"
        f"<b>__________________</b>\n\n"
        f"<b>Cover Letter</b> \n{context.user_data['cover_letter']}\n\n"
        f"<b>CV</b> \n✅\n\n"
        # f"<b>CV</b> \n{file.file_path}\n\n"
        # f"<b>CV</b> \n{context.user_data['new_cv']}\n\n"
        f"<b>Portfolio(s)</b> \n{context.user_data['portfolio']}\n\n\n"
        f"<b>Apply for the job?</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    return CONFIRM_APPLY
    
    # keyboard = [
    #     [InlineKeyboardButton("Confirm", callback_data='confirm_apply')],
    #     [InlineKeyboardButton("Cancel", callback_data='cancel_apply')],
    # ]
    # await update.message.reply_text(
    #     f"<b>Cover Letter</b>: {context.user_data['cover_letter']}\n\n"
    #     f"<b>CV</b>: {context.user_data['new_cv']}\n\n"
    #     f"<b>Portfolio</b>: {context.user_data['portfolio']}\n\n"
    #     f"<b>Apply for the job?</b>",
    #     reply_markup=InlineKeyboardMarkup(keyboard),
    #     parse_mode='HTML'
    # )
    # return CONFIRM_APPLY
    
    # await update.message.reply_text("Submitting your application...")
    # await submit_application(update, context)
    # return ConversationHandler.END


async def skip_portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['portfolio'] = []

    job = get_job(update, context, context.user_data['job_id'])
    
    job_details = f"\nJob Title: <b>\t{job[5]}</b> \n\nJob Type: <b>\t{job[4]}</b> \n\nWork Location: <b>\t{job[8]}, {job[9]}</b> \n\nSalary: <b>\t{job[10]}</b> \n\nDeadline: <b>\t{format_date(job[11])}</b> \n\n<b>Description</b>: \n{job[6]} \n\n<b>Requirements</b>: \n{job[7]} \n\n"
    
    # if context.user_data['new_cv']:
    #     file = await context.bot.get_file(context.user_data['new_cv'])
        
    keyboard = [
        [InlineKeyboardButton("Confirm", callback_data='confirm_apply')],
        [InlineKeyboardButton("Cancel", callback_data='cancel_apply')],
    ]
    await query.edit_message_text(
        f"{job_details}"
        f"<b>__________________</b>\n\n"
        f"<b>Cover Letter</b> \n{context.user_data['cover_letter']}\n\n"
        f"<b>CV</b> \n✅\n\n"
        # f"<b>CV</b> \n{file.file_path}\n\n"
        # f"<b>CV</b> \n{context.user_data['new_cv']}\n\n"
        f"<b>Portfolio(s)</b> \n{context.user_data['portfolio']}\n\n\n"
        f"<b>Apply for the job?</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    return CONFIRM_APPLY
    
    # keyboard = [
    #     [InlineKeyboardButton("Confirm", callback_data='confirm_apply')],
    #     [InlineKeyboardButton("Cancel", callback_data='cancel_apply')],
    # ]
    # await query.edit_message_text(
    #     f"<b>Cover Letter</b>: {context.user_data['cover_letter']}\n\n"
    #     f"<b>CV</b>: {context.user_data['new_cv']}\n\n"
    #     f"<b>Portfolio</b>: {context.user_data['portfolio']}\n\n"
    #     f"<b>Apply for the job?</b>",
    #     reply_markup=InlineKeyboardMarkup(keyboard),
    #     parse_mode='HTML'
    # )
    # return CONFIRM_APPLY
    
    # await query.edit_message_text("Submitting your application...")
    # await submit_application(update, context)
    # return ConversationHandler.END


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
        await query.edit_message_text("You've already applied for this job.")
        return ConversationHandler.END
    
    cur.execute(
        "INSERT INTO applications (job_id, user_id, cover_letter, cv, portfolio) VALUES (%s, %s, %s, %s, %s)",
        (context.user_data['job_id'], user[0], context.user_data['cover_letter'], context.user_data['new_cv'], json.dumps(context.user_data.get('portfolio', []))),
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
    if update.callback_query:
        telegram_id = update.callback_query.from_user.id
    else:
        telegram_id = update.effective_user.id
        
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE telegram_id = %s AND role_id = 1", (telegram_id,))
    user = cur.fetchone()

    cur.execute(
        "SELECT j.*, sj.* FROM saved_jobs sj JOIN jobs j ON sj.job_id = j.job_id WHERE sj.user_id = %s ORDER BY sj.created_at DESC LIMIT 50", (user[0],),
    )
    applications = cur.fetchall()
    
    if not applications:
        if update.callback_query:
            await update.callback_query.edit_message_text("You haven't saved any job.")
        else:
            await update.message.reply_text("You haven't saved any job.")
        return
    return


async def my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE telegram_id = %s AND role_id = 1", (telegram_id,))
    user = cur.fetchone()
    
    await update.message.reply_text(
        text=f"<b>My Profile</b> \n\n"
            f"<b>👤 \tName</b>: \t{(user[3].split()[0]).capitalize()} {(user[3].split()[1]).capitalize()} \n\n"
            f"<b>\t&#64; \t\tUsername</b>: \t{user[4]} \n\n"
            f"<b>👫 \tGender</b>: \t{user[5]} \n\n"
            f"<b>🎂 \tAge</b>: \t{user[6]} \n\n"
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
        "SELECT j.*, a.* FROM applications a JOIN jobs j ON a.job_id = j.job_id WHERE a.user_id = %s ORDER BY a.created_at DESC LIMIT 50", (user[0],),
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
    global total_saved_jobs
    total_saved_jobs = len(application_list)
    # current_saved_job_index = 0  # Reset index when starting
    
    application_details = f"\nJob Title: <b>\t{application[5]}</b> \n\nJob Type: <b>\t{application[4]}</b> \n\nWork Location: <b>\t{application[8]}, {application[9]}</b> \n\nSalary: <b>\t{application[10]}</b> \n\nDeadline: <b>\t{format_date(application[11])}</b> \n\n<b>Description</b>: \n{application[6]} \n\n<b>Requirements</b>: \n{application[7]} \n\n<b>__________________</b>\n\n<b>Applied at</b>: \t{format_date(application[24])} \n\n<b>Application Status</b>: \t{application[23].upper()} \n\n"

    # keyboard = []
    # if current_saved_job_index > 0:
    #     keyboard.append([InlineKeyboardButton("Previous", callback_data='job_previous')])
    # if current_saved_job_index < len(job_list) - 1:
    #     keyboard.append([InlineKeyboardButton("Next", callback_data='job_next')])

    if total_saved_jobs > 1:
        if current_saved_job_index > 0:
            keyboard = [
                [
                    InlineKeyboardButton("Previous", callback_data='saved_job_previous'),
                    InlineKeyboardButton("Next", callback_data='saved_job_next'),
                ],
            ]
            if total_saved_jobs == current_saved_job_index + 1:
                keyboard = [
                    [
                        InlineKeyboardButton("Previous", callback_data='saved_job_previous'),
                    ],
                ]
        else:
            keyboard = [
                [InlineKeyboardButton("Next", callback_data='saved_job_next')],
            ]
    else:
        keyboard = []

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
            "<b>Browse Jobs</b> - find jobs that best fit your schedule \n\n"
            "<b>Saved Jobs</b> - your saved jobs \n\n"
            "<b>My Profile</b> - manage your profile \n\n"
            "<b>My Applications</b> - view and track your applications \n\n"
            # "<b>Job Notifications</b> - customize notifications you wanna receive \n\n"
            "<b>Help</b> - show help message \n\n",
        parse_mode="HTML",
    )
    return



# Onboarding
async def onboarding_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text(text=f"Please enter your first name")
        return REGISTER_FIRSTNAME
    except Exception as e:
        await update.effective_message.reply_text(
            "An error occurred registering. Please try again."
        )
        # Optionally log the error for debugging
        print(f"Error in onboarding_start: {e}")
        return ConversationHandler.END


async def register_firstname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        firstname = update.message.text.strip()

        if not firstname.isalpha():
            await update.message.reply_text(
                "<i>* First name should only contain alphabetic characters.</i>\n\nPlease enter your first name",
                parse_mode='HTML'
            )
            return REGISTER_FIRSTNAME

        context.user_data['firstname'] = firstname
        await update.message.reply_text("Please enter your last name")
        return REGISTER_LASTNAME
    except Exception as e:
        await update.message.reply_text(
            "An error occurred while saving your first name. Please try again."
        )
        print(f"Error in register_firstname: {e}")
        return ConversationHandler.END


async def register_lastname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        lastname = update.message.text.strip()

        if not lastname.isalpha():
            await update.message.reply_text(
                "<i>* Last name should only contain alphabetic characters.</i>\n\nPlease enter your last name",
                parse_mode='HTML'
            )
            return REGISTER_LASTNAME

        context.user_data['lastname'] = lastname
        await update.message.reply_text("Please enter your email address")
        return REGISTER_EMAIL
    except Exception as e:
        await update.message.reply_text(
            "An error occurred while saving your last name. Please try again."
        )
        print(f"Error in register_lastname: {e}")
        return ConversationHandler.END


async def register_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        email = update.message.text.strip()

        # if "@" not in email or "." not in email:
        if not is_valid_email(email):
            await update.message.reply_text(
                "<i>* Invalid email format.</i>\n\nPlease enter your email address",
                parse_mode='HTML'
            )
            return REGISTER_EMAIL
        
        context.user_data['email'] = email
        await update.message.reply_text("Please enter your phone number")
        return REGISTER_PHONE
    except Exception as e:
        await update.message.reply_text(
            "An error occurred while saving your email address. Please try again."
        )
        print(f"Error in register_email: {e}")
        return ConversationHandler.END


async def register_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        phone = update.message.text.strip()
        
        if not phone.isdigit() or len(phone) < 9:  # Basic validation for phone numbers
            await update.message.reply_text(
                "<i>* Invalid phone number.</i>\n\nPlease enter your phone number",
                parse_mode='HTML'
            )
            return REGISTER_PHONE
        
        context.user_data['phone'] = phone
        keyboard = [
            [InlineKeyboardButton("Male", callback_data='Male'), InlineKeyboardButton("Female", callback_data='Female')],
            [InlineKeyboardButton("Skip", callback_data='skip')],
        ]
        await update.message.reply_text(
            "Please choose your gender",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return REGISTER_GENDER
    except Exception as e:
        await update.message.reply_text("An error occurred while saving your phone number. Please try again.")
        print(f"Error in register_phone: {e}")
        return ConversationHandler.END


async def register_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        
        context.user_data['gender'] = query.data if query.data != 'skip' else None
        await query.edit_message_text("Please enter your age between 10 and 100")
        return REGISTER_DOB
    except Exception as e:
        await update.effective_message.reply_text("An error occurred while saving your gender. Please try again.")
        print(f"Error in register_gender: {e}")
        return ConversationHandler.END


# async def register_dob_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     try:
#         dob_age = update.message.text.strip()
#         if dob_age.isdigit():
#             context.user_data['dob'] = None
#             context.user_data['age'] = int(dob_age)
#         else:
#             context.user_data['age'] = None
#             context.user_data['dob'] = dob_age
#         await update.message.reply_text("Please choose your country")
#         return REGISTER_COUNTRY
#     except Exception as e:
#         await update.message.reply_text("An error occurred while saving your date of birth or age. Please try again.")
#         print(f"Error in register_dob_age: {e}")
#         return ConversationHandler.END


async def register_dob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        dob = update.message.text.strip()
        
        if dob.isdigit():
            # Check if the input is a number between 10 and 100
            age = int(dob)
            if 10 <= age <= 100:
                context.user_data['dob'] = age
            else:
                await update.message.reply_text(
                    "<i>* Age out of range</i>\n\nPlease enter your age between 10 and 100",
                    parse_mode='HTML'
                )
                return REGISTER_DOB
        else:
            await update.message.reply_text(
                "<i>* Invalid age.</i>\n\nPlease enter your age between 10 and 100",
                parse_mode='HTML'
            )
            return REGISTER_DOB

        keyboard = [
            [InlineKeyboardButton("Ethiopia", callback_data='Ethiopia')],
        ]
        await update.message.reply_text(
            "Please choose your country",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return REGISTER_COUNTRY
    except Exception as e:
        await update.message.reply_text("An error occurred while saving your age. Please try again.")
        print(f"Error in register_dob: {e}")
        return ConversationHandler.END


# async def register_dob_old(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     try:
#         dob = update.message.text.strip()
#         date_pattern = r"^\d{1,2}/\d{1,2}/\d{4}$"
        
#         if re.match(date_pattern, dob):
#             try:
#                 datetime.strptime(dob, "%d/%m/%Y")
#                 # context.user_data['dob'] = format_date_for_db(dob)
#                 print(f"\n context.user_data - pattern : {context.user_data['dob']} \n")
#             except ValueError:
#                 await update.message.reply_text(
#                     "<i>* Invalid date.</i>\n\nPlease enter your date of birth, in DD/MM/YYYY format OR age",
#                     parse_mode='HTML'
#                 )
#                 return REGISTER_DOB
#         elif dob.isdigit():
#             # Check if the input is a number between 10 and 100
#             age = int(dob)
#             if 10 <= age <= 100:
#                 context.user_data['dob'] = age
#                 print(f"\n context.user_data - age : {context.user_data['dob']} \n")
#             else:
#                 await update.message.reply_text(
#                     "<i>* Age out of range</i>\n\nPlease enter your date of birth, in DD/MM/YYYY format OR age",
#                     parse_mode='HTML'
#                 )
#                 return REGISTER_DOB
#         else:
#             await update.message.reply_text(
#                 "<i>* Invalid input.</i>\n\nPlease enter your date of birth, in DD/MM/YYYY format OR age",
#                 parse_mode='HTML'
#             )
#             return REGISTER_DOB

#         keyboard = [
#             [InlineKeyboardButton("Ethiopia", callback_data='Ethiopia')],
#         ]
#         await update.message.reply_text(
#             "Please choose your country",
#             reply_markup=InlineKeyboardMarkup(keyboard)
#         )
#         return REGISTER_COUNTRY
#     except Exception as e:
#         await update.message.reply_text("An error occurred while saving your date of birth. Please try again.")
#         print(f"Error in register_dob: {e}")
#         return ConversationHandler.END


async def register_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        country = query.data
        
        # if not country.isalpha():
        #     await query.edit_message_text("Invalid country name.")
        #     return REGISTER_COUNTRY
        
        keyboard = get_all_cities()
        context.user_data['country'] = country
        await query.edit_message_text(
            "Please enter your city",
            reply_markup=keyboard
        )
        return REGISTER_CITY
    except Exception as e:
        await update.effective_message.reply_text("An error occurred while saving your country. Please try again.")
        print(f"Error in register_country: {e}")
        return ConversationHandler.END


async def register_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        city = query.data
        
        # if not re.match(r'^[A-Za-z\s]+$', city):
        # if not city.isalpha():
        #     await query.edit_message_text("Invalid city name.")
        #     return REGISTER_CITY
        
        context.user_data['city'] = city
        user_data = context.user_data
        keyboard = [
            [InlineKeyboardButton("Confirm ✅", callback_data='confirm')],
            [InlineKeyboardButton("Start Over 🔄", callback_data='restart')],
        ]
        await query.edit_message_text(
            f"<b>ACCOUNT INFORMATION</b>\n\n"
            f"<b>Name</b>: {(user_data['firstname']).capitalize()} {(user_data['lastname']).capitalize()}\n\n"
            f"<b>Email</b>: {user_data['email']}\n\n"
            f"<b>Phone</b>: {user_data['phone']}\n\n"
            f"<b>Gender</b>: {user_data.get('gender', '')}\n\n"
            f"<b>Age</b>: {user_data.get('dob', '')}\n\n"
            f"<b>Country</b>: {user_data['country']}\n\n"
            f"<b>City</b>: {user_data['city']}\n\n\n"
            f"<b>Do you confirm this information?</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        return CONFIRMATION
    except Exception as e:
        await update.effective_message.reply_text("An error occurred while saving your city. Please try again.")
        print(f"Error in register_city: {e}")
        return ConversationHandler.END


async def confirm_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        
        if query.data == 'confirm':
            user_data = context.user_data
            telegram_id = update.effective_user.id
            username = update.effective_user.username
            role_id = 1  # Assuming role_id is 1 for the applicant role

            try:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO users (telegram_id, role_id, name, username, email, phone, gender, dob, country, city) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (telegram_id, role_id, f"{user_data['firstname']} {user_data['lastname']}", username, user_data['email'], user_data['phone'],
                     user_data.get('gender'), user_data.get('dob'), user_data['country'], user_data['city'])
                )
                conn.commit()
                cur.close()
            except Exception as db_error:
                await query.edit_message_text("An error occurred while saving your data to the database. Please try again.")
                print(f"Database error in confirm_registration: {db_error}")
                return ConversationHandler.END

            await query.edit_message_text(
                f"Registration complete \t 🎉 \n\nWelcome to HulumJobs <b>{user_data['firstname'].capitalize()}</b>!",
                parse_mode='HTML'
            )
            # TODO: better way to handle redirect to `start`
            
            keyboard = [
                ["Browse Jobs", "Saved Jobs"],
                ["My Profile", "My Applications"],
                # ["Job Notifications", "Help"]
                ["Help"]
            ]
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"<b>Hello {user_data['firstname'].capitalize()} 👋\t Welcome to HulumJobs!</b> \n\n"
                    "<b>💼 \tBrowse Jobs</b>:\t find jobs that best fit your schedule \n\n"
                    "<b>📌 \tSaved Jobs</b>:\t your saved jobs \n\n"
                    "<b>👤 \tMy Profile</b>:\t manage your profile \n\n"
                    "<b>📑 \tMy Applications</b>:\t view and track your applications \n\n"
                    # "<b>🔔 \tJob Notifications</b>:\t customize notifications you wanna receive \n\n"
                    "<b>❓ \tHelp</b>:\t show help message \n\n",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
                parse_mode='HTML'
            )
            # return REGISTER_COMPLETE
            # await update.message.reply_text("/start")
        elif query.data == 'restart':
            await query.edit_message_text("Let's start over. Use /start to begin again.")
        return ConversationHandler.END
    except Exception as e:
        await query.edit_message_text("An error occurred during confirmation. Please try again.")
        print(f"Error in confirm_registration: {e}")
        return ConversationHandler.END


# Cancel command
async def onboarding_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Registration canceled. Type /start to restart.")
    return ConversationHandler.END


async def redirect_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)
    return ConversationHandler.END


# async def confirm_registration_old(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     await query.answer()
    
#     telegram_id = update.effective_user.id
#     username = update.effective_user.username
#     role_id = 1  # Assuming role_id is 1 for the applicant role
    
#     if query.data == 'confirm':
#         user_data = context.user_data
#         cur = conn.cursor()
#         cur.execute(
#             "INSERT INTO users (telegram_id, role_id, name, username, email, phone, gender, dob, country, city) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
#             (telegram_id, role_id, {user_data['firstname'] + ' ' + user_data['lastname']}, username, user_data['email'], user_data['phone'],
#              user_data.get('gender'), user_data.get('dob'), user_data['country'], user_data['city'])
#         )
#         conn.commit()

#         await query.edit_message_text("🎉 \tRegistration complete! Welcome to HulumJobs!")
#     elif query.data == 'restart':
#         await query.edit_message_text("Let's start over. Use /start to begin again.")
#     return ConversationHandler.END



# ? HELPERS (will be extracted to a separate helpers.py file)
def get_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE telegram_id = %s AND role_id = 1", (telegram_id,))
    user = cur.fetchone()
    return user


def get_job(update: Update, context: ContextTypes.DEFAULT_TYPE, job_id):
    cur = conn.cursor()
    cur.execute("SELECT * FROM jobs WHERE job_id = %s", (job_id,))
    job = cur.fetchone()
    return job


def format_date(date):
    return date.strftime("%B %d, %Y")


def format_date_for_db(date):
    return datetime.strptime(date, "%Y-%m-%d")


def is_valid_email(email):
    # regex pattern for validating an email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def get_all_cities():
    buttons = [
        InlineKeyboardButton(city, callback_data=f"{city}") for city in CITIES
    ]

    # Organize buttons into 2-column rows
    keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]  # Group buttons into rows
    keyboard.append([InlineKeyboardButton("Others", callback_data="Others")]),

    return InlineKeyboardMarkup(keyboard)


def get_city_keyboard(page=0):
    """Generate inline keyboard for cities with pagination."""
    start_index = page * PAGE_SIZE
    end_index = start_index + PAGE_SIZE
    cities_page = CITIES[start_index:end_index]

    # Create buttons for cities
    buttons = [
        InlineKeyboardButton(city, callback_data=f"city_{city}") for city in cities_page
    ]

    # Organize buttons into 2-column rows
    keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]  # [CHANGE] Group buttons into rows

    # Pagination buttons
    navigation_buttons = []
    if page > 0:  # [CHANGE] Add Prev button if applicable
        navigation_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"citypage_{page - 1}"))
    if end_index < len(CITIES):  # [CHANGE] Add Next button if applicable
        navigation_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"citycitypage_{page + 1}"))

    # Add navigation buttons as a row if present
    if navigation_buttons:  # [CHANGE] Ensure navigation buttons are added as a valid row
        keyboard.append(navigation_buttons)

    return InlineKeyboardMarkup(keyboard)  # [CHANGE] Correctly return a structured keyboard




# Conversation handlers
apply_job_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(apply_start, "apply"), CommandHandler("apply", apply_start)],
    states={
        COVER_LETTER: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, cover_letter),
            CallbackQueryHandler(skip_cover_letter, pattern="skip_cover_letter")
        ],
        NEW_CV: [
            MessageHandler(filters.Document.ALL & ~filters.COMMAND, new_cv),
            CallbackQueryHandler(skip_new_cv, pattern="skip_new_cv")
        ],
        PORTFOLIO: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, portfolio),
            CallbackQueryHandler(skip_portfolio, pattern="skip_portfolio")
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
        # REGISTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)],
        REGISTER_FIRSTNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_firstname)],
        REGISTER_LASTNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_lastname)],
        REGISTER_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_email)],
        REGISTER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_phone)],
        REGISTER_GENDER: [CallbackQueryHandler(register_gender)],
        REGISTER_DOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_dob)],
        REGISTER_COUNTRY: [CallbackQueryHandler(register_country)],
        REGISTER_CITY: [CallbackQueryHandler(register_city)],
        CONFIRMATION: [CallbackQueryHandler(confirm_registration)],
    },
    fallbacks=[CommandHandler('cancel', onboarding_cancel)],
)



def main():
    app = ApplicationBuilder().token(os.getenv('APPLICANT_BOT_TOKEN')).build()
    
    # app.add_handler(CallbackQueryHandler(register_country, pattern="^citypage_.*"))
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
