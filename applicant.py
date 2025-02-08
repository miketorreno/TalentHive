import os
import re
import sys
import json
import signal
import logging
import psycopg2
from datetime import date, datetime
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ApplicationBuilder,
    ContextTypes,
)

from config import HUGGINGFACE_MODEL
from utils.cover_letter import CoverLetterGenerator

# cover_letter_gen = CoverLetterGenerator(HUGGINGFACE_MODEL)


# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,  # level=logging.INFO | logging.DEBUG
)
logging.getLogger("httpx").setLevel(
    logging.WARNING
)  # avoid all GET and POST requests from being logged
logger = logging.getLogger(__name__)


# Connect to PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    database="hulumjobs",
    user="postgres",
    password="postgres",
    port="5432",
)

# TODO: Research this block of code & use it or remove it
# def shutdown_handler(signal_received, frame):
#     if conn:
#         conn.close()
#         print("Database connection closed.")
#     sys.exit(0)

# signal.signal(signal.SIGINT, shutdown_handler)


# Define states
(
    REGISTER,
    REGISTER_NAME,
    REGISTER_FIRSTNAME,
    REGISTER_LASTNAME,
    REGISTER_EMAIL,
    REGISTER_PHONE,
    REGISTER_GENDER,
    REGISTER_DOB,
    REGISTER_COUNTRY,
    REGISTER_CITY,
    CONFIRMATION,
    CHOOSE_ACTION,
    COVER_LETTER,
    NEW_CV,
    PORTFOLIO,
    CONFIRM_APPLY,
    CHOOSE_FIELD,
    EDIT_NAME,
    EDIT_USERNAME,
    EDIT_GENDER,
    EDIT_DOB,
    EDIT_COUNTRY,
    EDIT_CITY,
    EDIT_EMAIL,
    EDIT_PHONE,
    EDIT_DONE,
    GENERATE_JOB_TITLE,
    GENERATE_SKILLS,
    GENERATE_COMPANY,
    CONFIRM_GENERATE,
) = range(30)

# List of cities sorted alphabetically
CITIES = sorted(
    [
        "Addis Ababa",
        "Adama",
        "Adigrat",
        "Adwa",
        "Agaro",
        "Alaba Kulito",
        "Alamata",
        "Aleta Wendo",
        "Ambo",
        "Arba Minch",
        "Areka",
        "Arsi Negele",
        "Assosa",
        "Awassa",
        "Axum",
        "Bahir Dar",
        "Bale Robe",
        "Bedessa",
        "Bishoftu",
        "Boditi",
        "Bonga",
        "Burayu",
        "Batu",
        "Butajira",
        "Chiro",
        "Dambacha",
        "Dangila",
        "Debre Birhan",
        "Debre Mark'os",
        "Debre Tabor",
        "Dessie",
        "Dembi Dolo",
        "Dilla",
        "Dire Dawa",
        "Durame",
        "Fiche",
        "Finote Selam",
        "Gambela",
        "Goba",
        "Gode",
        "Gimbi",
        "Gonder",
        "Haramaya",
        "Harar",
        "Hosaena",
        "Jimma",
        "Jijiga",
        "Jinka",
        "Kobo",
        "Kombolcha",
        "Mekelle",
        "Meki",
        "Metu",
        "Mizan Teferi",
        "Mojo",
        "Mota",
        "Nekemte",
        "Negele Borana",
        "Sawla",
        "Sebeta",
        "Shashamane",
        "Shire",
        "Sodo",
        "Tepi",
        "Waliso",
        "Weldiya",
        "Welkite",
        "Wukro",
        "Yirgalem",
        "Ziway",
    ]
)

current_job_index = 0
total_jobs = 0
current_application_index = 0
total_applications = 0
current_savedjob_index = 0
total_savedjobs = 0

GROUP_TOPIC_New_JobSeeker_Registration_ID = 14


# Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update, context)

    if not user:
        keyboard = [
            [InlineKeyboardButton("Register", callback_data="register")],
        ]

        """Start the onboarding process."""
        await update.message.reply_text(
            "<b>Hello there 👋\t Welcome to HulumJobs! </b>\n\n"
            "Let’s get started, Please click the button below to register.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
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
                ["Help"],
                # ["Job Notifications", "Help"]
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
                parse_mode="HTML",
            )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hope we can talk again soon.")
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


def fetch_data(query, params=None, offset: int = 0, limit: int = 25):
    """
    Connects to PostgreSQL, fetches data using the provided offset and limit,
    and returns a list of rows.
    """

    cur = conn.cursor()
    query = """
        SELECT id, name, description
        FROM your_table
        ORDER BY id
        LIMIT %s OFFSET %s;
    """

    if params:
        cur.execute(query, params, (limit, offset))
    else:
        cur.execute(query, (limit, offset))

    data = cur.fetchall()
    cur.close()
    return data


def format_data(rows):
    """
    Formats a list of rows into a nicely formatted string.
    """
    if not rows:
        return "No data available."
    formatted_rows = []
    for row in rows:
        # Adjust the formatting based on your data
        formatted_rows.append(f"ID: {row[0]}\nName: {row[1]}\nDescription: {row[2]}\n")
    return "\n".join(formatted_rows)


def build_keyboard(offset: int, limit: int, rows_count: int):
    """
    Returns an InlineKeyboardMarkup with Next and Previous buttons.
    The callback_data includes the direction, current offset, and limit.
    """
    buttons = []
    if offset > 0:
        buttons.append(
            InlineKeyboardButton("Previous", callback_data=f"prev|{offset}|{limit}")
        )
    # If the page is “full”, assume there may be more rows to show
    if rows_count == limit:
        buttons.append(
            InlineKeyboardButton("Next", callback_data=f"next|{offset}|{limit}")
        )
    if buttons:
        return InlineKeyboardMarkup([buttons])
    return None


async def paginate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the inline button callbacks to paginate the data.
    """
    query = update.callback_query
    await query.answer()  # Acknowledge the callback

    # The callback_data is in the form: "direction|offset|limit"
    data = query.data.split("|")
    if len(data) != 3:
        await query.edit_message_text("Error: invalid pagination data.")
        return

    direction, offset_str, limit_str = data
    current_offset = int(offset_str)
    limit = int(limit_str)

    if direction == "next":
        new_offset = current_offset + limit
    elif direction == "prev":
        new_offset = max(current_offset - limit, 0)
    else:
        new_offset = current_offset  # Fallback (should not occur)

    rows = fetch_data(new_offset, limit)
    text = format_data(rows)
    keyboard = build_keyboard(new_offset, limit, len(rows))
    await query.edit_message_text(text, reply_markup=keyboard)


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

    job_details = (
        f"Job Title: <b>\t{job[4]}</b> \n\n"
        f"Job Type: <b>\t{job[6]} - {job[5]}</b> \n\n"
        f"Work Location: <b>\t{job[15]}, {job[16]}</b> \n\n"
        f"Applicants Needed: <b>\t{job[10]}</b> \n\n"
        f"Salary: <b>\t{job[17]}</b> \n\n"
        f"Deadline: <b>\t{format_date(job[11])}</b> \n\n"
        f"<b>Description</b>: \t{job[13]} \n\n"
        f"<b>Requirements</b>: \t{job[14]} \n\n"
    )

    keyboard = [
        [
            InlineKeyboardButton("Save", callback_data=f"save_{job[0]}"),
            InlineKeyboardButton("Apply", callback_data=f"apply_{job[0]}"),
        ],
    ]

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=job_details,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text(
            text=job_details,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
    return


async def browse_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cur = conn.cursor()
    cur.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT 50")
    jobs = cur.fetchall()

    if not jobs:
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "No jobs available at the moment."
            )
        else:
            await update.message.reply_text("No jobs available at the moment.")
        return

    job_list = [job for job in jobs]
    global current_job_index
    job = job_list[current_job_index]
    global total_jobs
    total_jobs = len(job_list)
    # current_job_index = 0  # Reset index when starting

    job_details = (
        f"Job Title: <b>\t{job[4]}</b> \n\n"
        f"Job Type: <b>\t{job[6]} - {job[5]}</b> \n\n"
        f"Work Location: <b>\t{job[15]}, {job[16]}</b> \n\n"
        f"Applicants Needed: <b>\t{job[10]}</b> \n\n"
        f"Salary: <b>\t{job[17]}</b> \n\n"
        f"Deadline: <b>\t{format_date(job[11])}</b> \n\n"
        f"<b>Description</b>: \t{job[13]} \n\n"
        f"<b>Requirements</b>: \t{job[14]} \n\n"
    )

    # keyboard = []
    # if current_job_index > 0:
    #     keyboard.append([InlineKeyboardButton("Previous", callback_data='job_previous')])
    # if current_job_index < len(job_list) - 1:
    #     keyboard.append([InlineKeyboardButton("Next", callback_data='job_next')])

    if total_jobs > 1:
        if current_job_index > 0:
            keyboard = [
                [
                    InlineKeyboardButton("Previous", callback_data="job_previous"),
                    InlineKeyboardButton("Next", callback_data="job_next"),
                ],
                [
                    InlineKeyboardButton("Save", callback_data=f"save_{job[0]}"),
                    InlineKeyboardButton("Apply", callback_data=f"apply_{job[0]}"),
                ],
            ]
            if total_jobs == current_job_index + 1:
                keyboard = [
                    [InlineKeyboardButton("Previous", callback_data="job_previous")],
                    [
                        InlineKeyboardButton("Save", callback_data=f"save_{job[0]}"),
                        InlineKeyboardButton("Apply", callback_data=f"apply_{job[0]}"),
                    ],
                ]
        else:
            keyboard = [
                [InlineKeyboardButton("Next", callback_data="job_next")],
                [
                    InlineKeyboardButton("Save", callback_data=f"save_{job[0]}"),
                    InlineKeyboardButton("Apply", callback_data=f"apply_{job[0]}"),
                ],
            ]
    else:
        keyboard = []

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=job_details,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text(
            text=job_details,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
    return


async def next_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_job_index
    query = update.callback_query
    await query.answer()  # Acknowledge the callback

    if query.data == "job_next":
        current_job_index += 1
    elif query.data == "job_previous":
        current_job_index -= 1

    await browse_jobs(update, context)


async def saved_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update, context)

    if not user:
        await start(update, context)
        return

    cur = conn.cursor()
    cur.execute(
        "SELECT j.*, sj.* FROM saved_jobs sj JOIN jobs j ON sj.job_id = j.job_id WHERE sj.user_id = %s ORDER BY sj.created_at DESC LIMIT 50",
        (user[0],),
    )
    savedjobs = cur.fetchall()

    if not savedjobs:
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "You haven't saved any jobs yet."
            )
        else:
            await update.message.reply_text("You haven't saved any jobs yet.")
        return

    savedjobs_list = [job for job in savedjobs]
    global current_savedjob_index
    savedjob = savedjobs_list[current_savedjob_index]
    global total_savedjobs
    total_savedjobs = len(savedjobs_list)
    # current_savedjob_index = 0  # Reset index when starting

    savedjob_details = (
        f"Job Title: <b>\t{savedjob[4]}</b> \n\n"
        f"Job Type: <b>\t{savedjob[6]} - {savedjob[5]}</b> \n\n"
        f"Work Location: <b>\t{savedjob[15]}, {savedjob[16]}</b> \n\n"
        f"Salary: <b>\t{savedjob[17]}</b> \n\n"
        f"Deadline: <b>\t{format_date(savedjob[11])}</b> \n\n"
        f"<b>Description</b>: \n{savedjob[13]} \n\n"
        f"<b>Requirements</b>: \n{savedjob[14]} \n\n"
    )

    if total_savedjobs > 1:
        if current_savedjob_index > 0:
            keyboard = [
                [
                    InlineKeyboardButton("Previous", callback_data="savedjob_previous"),
                    InlineKeyboardButton("Next", callback_data="savedjob_next"),
                ],
                [InlineKeyboardButton("Apply", callback_data=f"apply_{savedjob[0]}")],
            ]
            if total_savedjobs == current_savedjob_index + 1:
                keyboard = [
                    [
                        InlineKeyboardButton(
                            "Previous", callback_data="savedjob_previous"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "Apply", callback_data=f"apply_{savedjob[0]}"
                        )
                    ],
                ]
        else:
            keyboard = [
                [InlineKeyboardButton("Next", callback_data="savedjob_next")],
                [InlineKeyboardButton("Apply", callback_data=f"apply_{savedjob[0]}")],
            ]
    else:
        keyboard = []

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=savedjob_details,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text(
            text=savedjob_details,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )


async def next_savedjob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_savedjob_index
    query = update.callback_query
    await query.answer()  # Acknowledge the callback

    if query.data == "savedjob_next":
        current_savedjob_index += 1
    elif query.data == "savedjob_previous":
        current_savedjob_index -= 1

    await saved_jobs(update, context)


async def my_applications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update, context)

    if not user:
        await start(update, context)
        return

    cur = conn.cursor()
    cur.execute(
        "SELECT j.*, a.* FROM applications a JOIN jobs j ON a.job_id = j.job_id WHERE a.user_id = %s ORDER BY a.created_at DESC LIMIT 50",
        (user[0],),
    )
    applications = cur.fetchall()

    if not applications:
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "You haven't applied for any jobs yet."
            )
        else:
            await update.message.reply_text("You haven't applied for any jobs yet.")
        return

    application_list = [job for job in applications]
    global current_application_index
    application = application_list[current_application_index]
    global total_applications
    total_applications = len(application_list)
    # current_application_index = 0  # Reset index when starting

    application_details = (
        f"Job Title: <b>\t{application[4]}</b> \n\n"
        f"Job Type: <b>\t{application[6]} - {application[5]}</b> \n\n"
        f"Work Location: <b>\t{application[15]}, {application[16]}</b> \n\n"
        f"Salary: <b>\t{application[17]}</b> \n\n"
        f"Deadline: <b>\t{format_date(application[11])}</b> \n\n"
        f"<b>Description</b>: \n{application[13]} \n\n"
        f"<b>Requirements</b>: \n{application[14]} \n\n"
        f"<b>__________________</b>\n\n"
        f"<b>Applied at</b>: \t{format_date(application[34])} \n\n"
        f"<b>Application Status</b>: \t{application[33].upper()} \n\n"
    )

    # keyboard = []
    # if current_application_index > 0:
    #     keyboard.append([InlineKeyboardButton("Previous", callback_data='job_previous')])
    # if current_application_index < len(job_list) - 1:
    #     keyboard.append([InlineKeyboardButton("Next", callback_data='job_next')])

    if total_applications > 1:
        if current_application_index > 0:
            keyboard = [
                [
                    InlineKeyboardButton(
                        "Previous", callback_data="application_previous"
                    ),
                    InlineKeyboardButton("Next", callback_data="application_next"),
                ],
            ]
            if total_applications == current_application_index + 1:
                keyboard = [
                    [
                        InlineKeyboardButton(
                            "Previous", callback_data="application_previous"
                        ),
                    ],
                ]
        else:
            keyboard = [
                [InlineKeyboardButton("Next", callback_data="application_next")],
            ]
    else:
        keyboard = []

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=application_details,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text(
            text=application_details,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
    return


async def next_application(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_application_index
    query = update.callback_query
    await query.answer()  # Acknowledge the callback

    if query.data == "application_next":
        current_application_index += 1
    elif query.data == "application_previous":
        current_application_index -= 1

    await my_applications(update, context)


async def my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update, context)

    if not user:
        await start(update, context)
        return

    keyboard = [[InlineKeyboardButton("Edit Profile", callback_data="edit_profile")]]

    if update.callback_query:
        query = update.callback_query
        await query.edit_message_text(
            text=f"<b>My Profile</b> \n\n"
            f"<b>👤 \tName</b>: \t{(user[3].split()[0]).capitalize()} {(user[3].split()[1]).capitalize() if len(user[3].split()) > 1 else ''} \n\n"
            f"<b>\t&#64; \t\tUsername</b>: \t{user[4]} \n\n"
            f"<b>👫 \tGender</b>: \t{user[5]} \n\n"
            f"<b>🎂 \tAge</b>: \t{user[6]} \n\n"
            f"<b>🌐 \tCountry</b>: \t{user[9]} \n\n"
            f"<b>🏙️ \tCity</b>: \t{user[10]} \n\n"
            f"<b>📧 \tEmail</b>: \t{user[7]} \n\n"
            f"<b>📞 \tPhone</b>: \t{user[8]} \n\n",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text(
            text=f"<b>My Profile</b> \n\n"
            f"<b>👤 \tName</b>: \t{(user[3].split()[0]).capitalize()} {(user[3].split()[1]).capitalize() if len(user[3].split()) > 1 else ''} \n\n"
            f"<b>\t&#64; \t\tUsername</b>: \t{user[4]} \n\n"
            f"<b>👫 \tGender</b>: \t{user[5]} \n\n"
            f"<b>🎂 \tAge</b>: \t{user[6]} \n\n"
            f"<b>🌐 \tCountry</b>: \t{user[9]} \n\n"
            f"<b>🏙️ \tCity</b>: \t{user[10]} \n\n"
            f"<b>📧 \tEmail</b>: \t{user[7]} \n\n"
            f"<b>📞 \tPhone</b>: \t{user[8]} \n\n",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
    return


async def edit_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton("Edit Name", callback_data="edit_name"),
            InlineKeyboardButton("Update Username", callback_data="update_username"),
        ],
        [
            InlineKeyboardButton("Edit Gender", callback_data="edit_gender"),
            InlineKeyboardButton("Edit Age", callback_data="edit_dob"),
        ],
        [
            InlineKeyboardButton("Edit Country", callback_data="edit_country"),
            InlineKeyboardButton("Edit City", callback_data="edit_city"),
        ],
        [
            InlineKeyboardButton("Edit Email", callback_data="edit_email"),
            InlineKeyboardButton("Edit Phone", callback_data="edit_phone"),
        ],
        [InlineKeyboardButton("Done", callback_data="done_profile")],
    ]

    await query.edit_message_reply_markup(
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return


async def choose_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data

    if choice == "edit_name":
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="Please enter your new name (First and Last) \n\n<i>* Type /cancel to abort editing</i>",
            parse_mode="HTML",
        )
        return EDIT_NAME
        # elif choice == 'edit_username':
        # await context.bot.send_message(
        #     chat_id=query.from_user.id,
        #     text="<i>* Updating your username...</i>",
        #     parse_mode="HTML",
        # )
        # return EDIT_USERNAME
        # return edit_username(update, context)
    elif choice == "edit_gender":
        keyboard = [
            [
                InlineKeyboardButton("Male", callback_data="Male"),
                InlineKeyboardButton("Female", callback_data="Female"),
            ],
        ]

        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="Please choose your gender \n\n<i>* Type /cancel to abort editing</i>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return EDIT_GENDER
    elif choice == "edit_dob":
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="Please enter your age between 10 and 100 \n\n<i>* Type /cancel to abort editing</i>",
            parse_mode="HTML",
        )
        return EDIT_DOB
    elif choice == "edit_country":
        keyboard = [[InlineKeyboardButton("Ethiopia", callback_data="Ethiopia")]]

        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="Please select your country \n\n<i>* Type /cancel to abort editing</i>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return EDIT_COUNTRY
    elif choice == "edit_city":
        keyboard = get_all_cities()

        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="Please select your city \n\n<i>* Type /cancel to abort editing</i>",
            reply_markup=keyboard,
            parse_mode="HTML",
        )
        return EDIT_CITY
    elif choice == "edit_email":
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="Please enter your email address \n\n<i>* Type /cancel to abort editing</i>",
            parse_mode="HTML",
        )
        return EDIT_EMAIL
    elif choice == "edit_phone":
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="Please enter your phone number \n\n<i>* Type /cancel to abort editing</i>",
            parse_mode="HTML",
        )
        return EDIT_PHONE
    else:
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="Invalid choice, please select again",
            parse_mode="HTML",
        )
        return CHOOSE_FIELD


async def edit_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    telegram_id = update.effective_user.id

    cur = conn.cursor()
    cur.execute(
        f"UPDATE users SET name = %s WHERE telegram_id = %s AND role_id = 1",
        (name, telegram_id),
    )
    conn.commit()

    keyboard = [[InlineKeyboardButton("Back to Profile", callback_data="my_profile")]]

    await update.message.reply_text(
        text="Name updated successfully!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )
    return ConversationHandler.END


async def update_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    username = update.effective_user.username
    query = update.callback_query
    await query.answer()

    cur = conn.cursor()
    cur.execute(
        f"UPDATE users SET username = %s WHERE telegram_id = %s AND role_id = 1",
        (username, telegram_id),
    )
    conn.commit()

    keyboard = [[InlineKeyboardButton("Back to Profile", callback_data="my_profile")]]

    await context.bot.send_message(
        chat_id=query.from_user.id,
        text="Username updated successfully!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )
    return ConversationHandler.END


async def edit_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        telegram_id = update.effective_user.id

        cur = conn.cursor()
        cur.execute(
            f"UPDATE users SET gender = %s WHERE telegram_id = %s AND role_id = 1",
            (query.data, telegram_id),
        )
        conn.commit()

        keyboard = [
            [InlineKeyboardButton("Back to Profile", callback_data="my_profile")]
        ]

        await query.edit_message_text(
            text="Gender updated successfully!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return ConversationHandler.END
    except Exception as e:
        await query.edit_message_text(
            "An error occurred while updating your gender. Please try again."
        )
        print(f"Error in edit_gender: {e}")
        return ConversationHandler.END


async def edit_dob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        dob = update.message.text.strip()

        if dob.isdigit():
            # Check if the input is a number between 10 and 100
            age = int(dob)
            if 10 <= age <= 100:
                keyboard = [
                    [
                        InlineKeyboardButton(
                            "Back to Profile", callback_data="my_profile"
                        )
                    ]
                ]

                telegram_id = update.effective_user.id

                cur = conn.cursor()
                cur.execute(
                    f"UPDATE users SET dob = %s WHERE telegram_id = %s AND role_id = 1",
                    (dob, telegram_id),
                )
                conn.commit()

                await update.message.reply_text(
                    text="Age updated successfully!",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="HTML",
                )
                return ConversationHandler.END
            else:
                await update.message.reply_text(
                    "<i>* Age out of range</i>\n\nPlease enter your age between 10 and 100 \n\n<i>* Type /cancel to abort editing</i>",
                    parse_mode="HTML",
                )
                return EDIT_DOB
        else:
            await update.message.reply_text(
                "<i>* Invalid age.</i>\n\nPlease enter your age between 10 and 100 \n\n<i>* Type /cancel to abort editing</i>",
                parse_mode="HTML",
            )
            return EDIT_DOB
    except Exception as e:
        await update.message.reply_text(
            "An error occurred while updating your age. Please try again."
        )
        print(f"Error in edit_dob: {e}")
        return ConversationHandler.END


async def edit_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        telegram_id = update.effective_user.id

        cur = conn.cursor()
        cur.execute(
            f"UPDATE users SET country = %s WHERE telegram_id = %s AND role_id = 1",
            (query.data, telegram_id),
        )
        conn.commit()

        keyboard = [
            [InlineKeyboardButton("Back to Profile", callback_data="my_profile")]
        ]

        await query.edit_message_text(
            text="Country updated successfully!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return ConversationHandler.END
    except Exception as e:
        await query.edit_message_text(
            "An error occurred while updating your country. Please try again."
        )
        print(f"Error in edit_country: {e}")
        return ConversationHandler.END


async def edit_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        telegram_id = update.effective_user.id

        cur = conn.cursor()
        cur.execute(
            f"UPDATE users SET city = %s WHERE telegram_id = %s AND role_id = 1",
            (query.data, telegram_id),
        )
        conn.commit()

        keyboard = [
            [InlineKeyboardButton("Back to Profile", callback_data="my_profile")]
        ]

        await query.edit_message_text(
            text="City updated successfully!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return ConversationHandler.END
    except Exception as e:
        await update.effective_message.reply_text(
            "An error occurred while saving your city. Please try again."
        )
        print(f"Error in edit_city: {e}")
        return ConversationHandler.END


async def edit_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        email = update.message.text.strip()
        telegram_id = update.effective_user.id

        if not is_valid_email(email):
            await update.message.reply_text(
                "<i>* Invalid email format.</i>\n\nPlease enter your email address \n\n<i>* Type /cancel to abort editing</i>",
                parse_mode="HTML",
            )
            return EDIT_EMAIL

        cur = conn.cursor()
        cur.execute(
            f"UPDATE users SET email = %s WHERE telegram_id = %s AND role_id = 1",
            (email, telegram_id),
        )
        conn.commit()

        keyboard = [
            [InlineKeyboardButton("Back to Profile", callback_data="my_profile")]
        ]

        await update.message.reply_text(
            text="Email updated successfully!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(
            "An error occurred while updating your email address. Please try again."
        )
        print(f"Error in edit_email: {e}")
        return ConversationHandler.END


async def edit_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        phone = update.message.text.strip()
        telegram_id = update.effective_user.id

        if not phone.isdigit() or len(phone) < 9:  # Basic validation for phone numbers
            await update.message.reply_text(
                "<i>* Invalid phone number.</i>\n\nPlease enter your phone number \n\n<i>* Type /cancel to abort editing</i>",
                parse_mode="HTML",
            )
            return EDIT_PHONE

        cur = conn.cursor()
        cur.execute(
            f"UPDATE users SET phone = %s WHERE telegram_id = %s AND role_id = 1",
            (phone, telegram_id),
        )
        conn.commit()

        keyboard = [
            [InlineKeyboardButton("Back to Profile", callback_data="my_profile")]
        ]

        await update.message.reply_text(
            text="Email updated successfully!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(
            "An error occurred while updating your phone number. Please try again."
        )
        print(f"Error in edit_phone: {e}")
        return ConversationHandler.END


async def done_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [[InlineKeyboardButton("Edit Profile", callback_data="edit_profile")]]

    await query.edit_message_reply_markup(
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return


async def cancel_edit_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Back to Profile", callback_data="my_profile")]]

    await update.message.reply_text(
        "Profile update canceled.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return ConversationHandler.END


# TODO: postponed
async def job_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Job Notifications")
    return


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        text="<b>Help</b>\n\n"
        "<b>Browse Jobs</b> - find jobs that best fit your schedule \n\n"
        "<b>Saved Jobs</b> - your saved jobs \n\n"
        "<b>My Profile</b> - manage your profile \n\n"
        "<b>My Applications</b> - view and track your applications \n\n"
        # "<b>Job Notifications</b> - customize notifications you wanna receive \n\n"
        "<b>Help</b> - show help message \n\n",
        parse_mode="HTML",
    )
    return


async def save_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        job_id = int(query.data.split("_")[-1])
        user = get_user(update, context)

        if not user:
            await start(update, context)
            return

        # checking duplicate
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM saved_jobs WHERE job_id = %s AND user_id = %s",
            (job_id, user[0]),
        )
        duplicate = cur.fetchone()

        if duplicate:
            await context.bot.send_message(
                chat_id=query.from_user.id,
                text="You've already saved this job.",
                parse_mode="HTML",
            )
        else:
            cur.execute(
                "INSERT INTO saved_jobs (job_id, user_id) VALUES (%s, %s)",
                (job_id, user[0]),
            )
            conn.commit()

            await context.bot.send_message(
                chat_id=query.from_user.id,
                text="Job saved",
                parse_mode="HTML",
            )
    except Exception as e:
        await update.message.reply_text(
            "An error occurred while saving job. Please try again."
        )
        print(f"Error in save_job: {e}")
        return


# APPLYING FOR JOBS


async def apply_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["job_id"] = int(query.data.split("_")[-1])
    user = get_user(update, context)

    if not user:
        await start(update, context)
        return

    # checking duplicate
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM applications WHERE job_id = %s AND user_id = %s",
        (context.user_data["job_id"], user[0]),
    )
    duplicate = cur.fetchone()
    if duplicate:
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="You've already applied for this job.",
            parse_mode="HTML",
        )
        return ConversationHandler.END

    keyboard = [
        [
            InlineKeyboardButton("Skip", callback_data="skip_cover_letter"),
            InlineKeyboardButton(
                "✨ Generate with AI", callback_data="generate_cover_letter"
            ),
        ]
    ]
    await query.edit_message_text(
        "Would you like to write cover letter \n\n<i>*enter less than 500 characters</i>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )
    return COVER_LETTER


async def cover_letter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["cover_letter"] = update.message.text

    keyboard = [
        [
            InlineKeyboardButton("Skip", callback_data="skip_new_cv"),
            InlineKeyboardButton(
                "✨ Generate with AI", callback_data="generate_new_cv"
            ),
        ]
    ]
    await update.message.reply_text(
        "Would you like to submit a new CV \n\n<i>*please upload pdf or word document</i>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )
    return NEW_CV


async def skip_cover_letter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["cover_letter"] = None

    keyboard = [
        [
            InlineKeyboardButton("Skip", callback_data="skip_new_cv"),
            InlineKeyboardButton(
                "✨ Generate with AI", callback_data="generate_new_cv"
            ),
        ]
    ]
    await query.edit_message_text(
        "Would you like to submit a new CV \n\n<i>*please upload pdf or word document</i>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )
    return NEW_CV


async def generate_cover_letter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Great! give me some details. \n\nWhat is the job title you're applying for?",
        parse_mode="HTML",
    )
    return GENERATE_JOB_TITLE


async def collect_job_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["job_title"] = update.message.text
    await update.message.reply_text(
        text="What are your top skills/experiences for this job?",
        parse_mode="HTML",
    )
    return GENERATE_SKILLS


async def collect_skills(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["skills"] = update.message.text
    await update.message.reply_text(
        text="What is the company's name?",
        parse_mode="HTML",
    )
    return GENERATE_COMPANY


async def collect_company(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="<i>Generating your cover letter...</i>",
        parse_mode="HTML",
    )

    context.user_data["company"] = update.message.text
    user_data = context.user_data

    # generated = await cover_letter_gen.generate_cover_letter(
    #     user_data['job_title'],
    #     user_data['skills'],
    #     user_data['company']
    # )
    generated = "DONE!"

    print(f"\n generated : {generated} \n")

    keyboard = [
        [
            InlineKeyboardButton("Accept", callback_data="accept_cover_letter"),
            InlineKeyboardButton("Reject", callback_data="skip_cover_letter"),
        ],
    ]
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"{generated}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )
    return CONFIRM_GENERATE


async def generated_cover_letter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["cover_letter"] = query.message.text

    if query.data == "skip_cover_letter":
        return COVER_LETTER

    if query.data == "accept_cover_letter":
        return COVER_LETTER


async def new_cv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.document:
        # Validate the file type
        file_name = update.message.document.file_name
        if not file_name.endswith((".pdf", ".doc", ".docx")):
            keyboard = [[InlineKeyboardButton("Skip", callback_data="skip_new_cv")]]
            await update.message.reply_text(
                "<i>* invalid file type</i> \n\n<b>Please upload a PDF or Word document</b>",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML",
            )
            return NEW_CV

        # Save the file ID
        context.user_data["new_cv"] = update.message.document.file_id

        keyboard = [[InlineKeyboardButton("Skip", callback_data="skip_portfolio")]]

        await update.message.reply_text(
            "Would you like to add portfolio links \n\n<i>* separated by commas</i>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return PORTFOLIO
    else:
        await update.message.reply_text("Please upload a valid document.")
        return NEW_CV


async def unsupported_cv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unsupported file uploads."""
    keyboard = [[InlineKeyboardButton("Skip", callback_data="skip_new_cv")]]
    await update.message.reply_text(
        "<i>* invalid file type</i> \n\n<b>Please upload a PDF or Word document</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )
    return NEW_CV


async def skip_new_cv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["new_cv"] = None

    keyboard = [[InlineKeyboardButton("Skip", callback_data="skip_portfolio")]]
    await query.edit_message_text(
        "Would you like to add portfolio links \n\n<i>* separated by commas</i>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )
    return PORTFOLIO


async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["portfolio"] = (
        update.message.text.split(",") if update.message.text else []
    )

    job = get_job(update, context, context.user_data["job_id"])

    job_details = f"\nJob Title: <b>\t{job[5]}</b> \n\nJob Type: <b>\t{job[4]}</b> \n\nWork Location: <b>\t{job[8]}, {job[9]}</b> \n\nSalary: <b>\t{job[10]}</b> \n\nDeadline: <b>\t{format_date(job[11])}</b> \n\n<b>Description</b>: \n{job[6]} \n\n<b>Requirements</b>: \n{job[7]} \n\n"

    keyboard = [
        [InlineKeyboardButton("Confirm", callback_data="confirm_apply")],
        [InlineKeyboardButton("Cancel", callback_data="cancel_apply")],
    ]
    await update.message.reply_text(
        f"{job_details}"
        f"<b>__________________</b>\n\n"
        f"<b>Cover Letter</b> \n{context.user_data['cover_letter'] if context.user_data['cover_letter'] else None}\n\n"
        f"<b>CV Uploaded</b> \n{'✅' if context.user_data['new_cv'] else None}\n\n"
        f"<b>Portfolio(s)</b> \n{context.user_data['portfolio'] if context.user_data['portfolio'] else None}\n\n\n"
        # f"<b>CV</b> \n{file.file_path}\n\n"
        f"<b>Apply for the job?</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )
    return CONFIRM_APPLY


async def skip_portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["portfolio"] = []

    job = get_job(update, context, context.user_data["job_id"])

    job_details = f"\nJob Title: <b>\t{job[5]}</b> \n\nJob Type: <b>\t{job[4]}</b> \n\nWork Location: <b>\t{job[8]}, {job[9]}</b> \n\nSalary: <b>\t{job[10]}</b> \n\nDeadline: <b>\t{format_date(job[11])}</b> \n\n<b>Description</b>: \n{job[6]} \n\n<b>Requirements</b>: \n{job[7]} \n\n"

    # if context.user_data['new_cv']:
    #     file = await context.bot.get_file(context.user_data['new_cv'])

    keyboard = [
        [InlineKeyboardButton("Confirm", callback_data="confirm_apply")],
        [InlineKeyboardButton("Cancel", callback_data="cancel_apply")],
    ]
    await query.edit_message_text(
        f"{job_details}"
        f"<b>__________________</b>\n\n"
        f"<b>Cover Letter</b> \n{context.user_data['cover_letter'] if context.user_data['cover_letter'] else None}\n\n"
        f"<b>CV Uploaded</b> \n{'✅' if context.user_data['new_cv'] else None}\n\n"
        f"<b>Portfolio(s)</b> \n{context.user_data['portfolio'] if context.user_data['portfolio'] else None}\n\n\n"
        # f"<b>CV</b> \n{file.file_path}\n\n"
        f"<b>Apply for the job?</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )
    return CONFIRM_APPLY


async def confirm_apply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = get_user(update, context)

    if not user:
        await start(update, context)
        return

    # checking duplicate
    # cur.execute("SELECT * FROM applications WHERE job_id = %s AND user_id = %s", (context.user_data['job_id'], user[0]))
    # duplicate = cur.fetchone()
    # if duplicate:
    #     await query.edit_message_text("You've already applied for this job.")
    #     return ConversationHandler.END

    cur = conn.cursor()
    cur.execute(
        "INSERT INTO applications (job_id, user_id, cover_letter, cv, portfolio) VALUES (%s, %s, %s, %s, %s)",
        (
            context.user_data["job_id"],
            user[0],
            context.user_data["cover_letter"],
            context.user_data["new_cv"],
            json.dumps(context.user_data.get("portfolio", [])),
        ),
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


# Onboarding
async def onboarding_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()

        # await query.edit_message_text(text=f"Please enter your first name")

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Please enter your first name",
            parse_mode="HTML",
        )
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
                parse_mode="HTML",
            )
            return REGISTER_FIRSTNAME

        context.user_data["firstname"] = firstname
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
                parse_mode="HTML",
            )
            return REGISTER_LASTNAME

        context.user_data["lastname"] = lastname
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
                parse_mode="HTML",
            )
            return REGISTER_EMAIL

        context.user_data["email"] = email
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
                parse_mode="HTML",
            )
            return REGISTER_PHONE

        context.user_data["phone"] = phone
        keyboard = [
            [
                InlineKeyboardButton("Male", callback_data="Male"),
                InlineKeyboardButton("Female", callback_data="Female"),
            ],
            [InlineKeyboardButton("Skip", callback_data="skip")],
        ]
        await update.message.reply_text(
            "Please choose your gender", reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return REGISTER_GENDER
    except Exception as e:
        await update.message.reply_text(
            "An error occurred while saving your phone number. Please try again."
        )
        print(f"Error in register_phone: {e}")
        return ConversationHandler.END


async def register_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()

        context.user_data["gender"] = query.data if query.data != "skip" else None
        await query.edit_message_text("Please enter your age between 10 and 100")
        return REGISTER_DOB
    except Exception as e:
        await update.effective_message.reply_text(
            "An error occurred while saving your gender. Please try again."
        )
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
#         await update.message.reply_text("Please select your country")
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
                context.user_data["dob"] = age
            else:
                await update.message.reply_text(
                    "<i>* Age out of range</i>\n\nPlease enter your age between 10 and 100",
                    parse_mode="HTML",
                )
                return REGISTER_DOB
        else:
            await update.message.reply_text(
                "<i>* Invalid age.</i>\n\nPlease enter your age between 10 and 100",
                parse_mode="HTML",
            )
            return REGISTER_DOB

        # keyboard = [
        #     [InlineKeyboardButton("Ethiopia", callback_data='Ethiopia')]
        # ]
        # await update.message.reply_text(
        #     "Please select your country",
        #     reply_markup=InlineKeyboardMarkup(keyboard)
        # )
        # return REGISTER_COUNTRY

        keyboard = get_all_cities()
        context.user_data["country"] = "Ethiopia"
        await update.message.reply_text(
            "Please select your city", reply_markup=keyboard
        )
        return REGISTER_CITY
    except Exception as e:
        await update.message.reply_text(
            "An error occurred while saving your age. Please try again."
        )
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
#             [InlineKeyboardButton("Ethiopia", callback_data='Ethiopia')]
#         ]
#         await update.message.reply_text(
#             "Please select your country",
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

        keyboard = get_all_cities()
        context.user_data["country"] = country
        await query.edit_message_text("Please select your city", reply_markup=keyboard)
        return REGISTER_CITY
    except Exception as e:
        await query.edit_message_text(
            "An error occurred while saving your country. Please try again."
        )
        print(f"Error in register_country: {e}")
        return ConversationHandler.END


async def register_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        city = query.data

        context.user_data["city"] = city
        user_data = context.user_data
        keyboard = [
            [InlineKeyboardButton("Confirm ✅", callback_data="confirm")],
            [InlineKeyboardButton("Start Over 🔄", callback_data="restart")],
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
            parse_mode="HTML",
        )
        return CONFIRMATION
    except Exception as e:
        await update.effective_message.reply_text(
            "An error occurred while saving your city. Please try again."
        )
        print(f"Error in register_city: {e}")
        return ConversationHandler.END


async def confirm_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()

        if query.data == "confirm":
            user_data = context.user_data
            user_data["telegram_id"] = update.effective_user.id
            username = update.effective_user.username
            role_id = 1  # Assuming role_id is 1 for the applicant role

            try:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO users (telegram_id, role_id, name, username, email, phone, gender, dob, country, city) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (
                        user_data["telegram_id"],
                        role_id,
                        f"{user_data['firstname']} {user_data['lastname']}",
                        username,
                        user_data["email"],
                        user_data["phone"],
                        user_data.get("gender"),
                        user_data.get("dob"),
                        user_data["country"],
                        user_data["city"],
                    ),
                )
                conn.commit()
                cur.close()
            except Exception as db_error:
                await query.edit_message_text(
                    "An error occurred while saving your data to the database. Please try again."
                )
                print(f"Database error in confirm_registration: {db_error}")
                return ConversationHandler.END

            await query.edit_message_text(
                f"Registered successfully \t 🎉",
                # f"Registered successfully \t 🎉 \n\nWelcome to HulumJobs <b>{user_data['firstname'].capitalize()}</b>!",
                parse_mode="HTML",
            )

            # TODO: implement a better way to handle redirect to `start`
            keyboard = [
                ["Browse Jobs", "Saved Jobs"],
                ["My Profile", "My Applications"],
                ["Help"],
                # ["Job Notifications", "Help"]
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
                parse_mode="HTML",
            )

            # Notify the group about the new registration
            await notify_group_on_registration(update, context, user_data)

            # return REGISTER_COMPLETE
            # await update.message.reply_text("/start")

        elif query.data == "restart":
            await query.edit_message_text(
                "Let's start over. Use /start to begin again."
            )
        return ConversationHandler.END
    except Exception as e:
        await query.edit_message_text(
            "An error occurred during confirmation. Please try again."
        )
        print(f"Error in confirm_registration: {e}")
        return ConversationHandler.END


async def onboarding_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Registration canceled. Type /start to restart.")
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

#         await query.edit_message_text("🎉 \tRegistered successfully! Welcome to HulumJobs!")
#     elif query.data == 'restart':
#         await query.edit_message_text("Let's start over. Use /start to begin again.")
#     return ConversationHandler.END


# * HELPERS (will be extracted to a separate helpers.py file)
def get_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        telegram_id = update.callback_query.from_user.id
    else:
        telegram_id = update.effective_user.id

    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM users WHERE telegram_id = %s AND role_id = 1", (telegram_id,)
    )
    user = cur.fetchone()
    return user


def get_user_from_telegram_id(
    update: Update, context: ContextTypes.DEFAULT_TYPE, telegram_id
):
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM users WHERE telegram_id = %s AND role_id = 1", (telegram_id,)
    )
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
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


async def notify_group_on_registration(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_data,
    topic_id=GROUP_TOPIC_New_JobSeeker_Registration_ID,
):
    view_keyboard = [
        [
            InlineKeyboardButton(
                "View Profile",
                callback_data=f"view_jobseeker_{user_data['telegram_id']}",
            )
        ]
    ]
    message = (
        f"\n🎉 <b>New User Registered!</b>\n\n"
        f"<b>Name</b>: {(user_data['firstname']).capitalize()} {(user_data['lastname']).capitalize() if len(user_data['lastname']) > 0 else ''}\n\n"
        f"<b>Email</b>: {user_data['email']}\n\n"
        f"<b>City</b>: {user_data['city']}\n\n"
    )

    await context.bot.send_message(
        chat_id=os.getenv("HULUMJOBS_GROUP_ID"),
        text=message,
        reply_markup=InlineKeyboardMarkup(view_keyboard),
        parse_mode="HTML",
        message_thread_id=topic_id,
    )
    return


async def view_jobseeker_profile(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    topic_id=GROUP_TOPIC_New_JobSeeker_Registration_ID,
):
    """
    Handle the 'View Profile' button and display user details on the group.
    """
    query = update.callback_query
    await query.answer()

    # Extract user ID from callback data
    telegram_id = query.data.split("_")[-1]
    user = get_user_from_telegram_id(update, context, telegram_id)

    # Display user details
    if user:
        await context.bot.send_message(
            chat_id=os.getenv("HULUMJOBS_GROUP_ID"),
            text=f"<b>User Profile</b>\n\n"
            f"<b>Job Seeker</b>\n\n"
            f"<b>👤 \tName</b>: \t{(user[3].split()[0]).capitalize()} {(user[3].split()[1]).capitalize() if len(user[3].split()) > 1 else ''} \n\n"
            f"<b>\t&#64; \t\tUsername</b>: \t{user[4]} \n\n"
            f"<b>👫 \tGender</b>: \t{user[5]} \n\n"
            f"<b>🎂 \tAge</b>: \t{user[6]} \n\n"
            f"<b>🌐 \tCountry</b>: \t{user[9]} \n\n"
            f"<b>🏙️ \tCity</b>: \t{user[10]} \n\n"
            f"<b>📧 \tEmail</b>: \t{user[7]} \n\n"
            f"<b>📞 \tPhone</b>: \t{user[8]} \n\n",
            parse_mode="HTML",
            message_thread_id=topic_id,
        )
    else:
        await context.bot.send_message(
            chat_id=os.getenv("HULUMJOBS_GROUP_ID"),
            text="User not found.",
            parse_mode="HTML",
        )

    return


# async def get_group_topics(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Fetch topics (threads) in the group."""
#     chat_id = os.getenv("HULUMJOBS_GROUP_ID")  # Replace with your group's chat ID
#     response = await context.bot.get_chat(chat_id)
#     print(f"\n Response: {response} \n")
#     topics = response.available_topics  # Only available for forum-enabled groups
#     print(f"\n Topics: {topics} \n")
#     for topic in topics:
#         print(f"\n Topic Name: {topic.name}, Thread ID: {topic.message_thread_id} \n")


def get_all_cities():
    buttons = [InlineKeyboardButton(city, callback_data=f"{city}") for city in CITIES]

    # Organize buttons into 2-column rows
    keyboard = [
        buttons[i : i + 2] for i in range(0, len(buttons), 2)
    ]  # Group buttons into rows
    keyboard.append([InlineKeyboardButton("Others", callback_data="Others")]),

    return InlineKeyboardMarkup(keyboard)


# * DEBUG (will be extracted to a separate debug.py file)
async def capture_group_topics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Capture topics (message_thread_id) from messages in a forum group.
    print("capturing group topics...")
    print(f"\n update.message: {update.message} \n")
    # if update.message and update.message.is_topic_message:
    #     topic_name = update.message.forum_topic_created.name
    #     thread_id = update.message.message_thread_id
    #     print(f"\n Topic Name: {topic_name}, Thread ID: {thread_id} \n")
    # Save these details in your database or bot memory if needed


# Conversation handlers
apply_job_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(apply_start, pattern="^apply_.*"),
        CommandHandler("apply", apply_start),
    ],
    states={
        COVER_LETTER: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, cover_letter),
            CallbackQueryHandler(
                generate_cover_letter, pattern="^generate_cover_letter$"
            ),
            CallbackQueryHandler(skip_cover_letter, pattern="^skip_cover_letter$"),
        ],
        GENERATE_JOB_TITLE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, collect_job_title)
        ],
        GENERATE_SKILLS: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, collect_skills)
        ],
        GENERATE_COMPANY: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, collect_company)
        ],
        CONFIRM_GENERATE: [
            CallbackQueryHandler(generated_cover_letter, pattern="accept_cover_letter"),
            CallbackQueryHandler(generated_cover_letter, pattern="skip_cover_letter"),
        ],
        NEW_CV: [
            MessageHandler(filters.Document.ALL, new_cv),
            MessageHandler(filters.ALL & ~filters.Document.ALL, unsupported_cv),
            CallbackQueryHandler(skip_new_cv, pattern="skip_new_cv"),
        ],
        PORTFOLIO: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, portfolio),
            CallbackQueryHandler(skip_portfolio, pattern="skip_portfolio"),
        ],
        CONFIRM_APPLY: [
            CallbackQueryHandler(confirm_apply, pattern="confirm_apply"),
            CallbackQueryHandler(cancel_apply, pattern="cancel_apply"),
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel_apply)],
)


profile_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(choose_field, pattern="^edit_.*")],
    states={
        CHOOSE_FIELD: [CallbackQueryHandler(choose_field, pattern="^edit_.*")],
        EDIT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_name)],
        # EDIT_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_username)],
        EDIT_GENDER: [CallbackQueryHandler(edit_gender)],
        EDIT_DOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_dob)],
        EDIT_COUNTRY: [CallbackQueryHandler(edit_country)],
        EDIT_CITY: [CallbackQueryHandler(edit_city)],
        EDIT_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_email)],
        EDIT_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_phone)],
    },
    fallbacks=[CommandHandler("cancel", cancel_edit_profile)],
)


onboarding_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(onboarding_start, "register")],
    states={
        REGISTER: [CallbackQueryHandler(onboarding_start)],
        # REGISTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)],
        REGISTER_FIRSTNAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, register_firstname)
        ],
        REGISTER_LASTNAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, register_lastname)
        ],
        REGISTER_EMAIL: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, register_email)
        ],
        REGISTER_PHONE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, register_phone)
        ],
        REGISTER_GENDER: [CallbackQueryHandler(register_gender)],
        REGISTER_DOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_dob)],
        REGISTER_COUNTRY: [CallbackQueryHandler(register_country)],
        REGISTER_CITY: [CallbackQueryHandler(register_city)],
        CONFIRMATION: [CallbackQueryHandler(confirm_registration)],
    },
    fallbacks=[CommandHandler("cancel", onboarding_cancel)],
)


def main():
    app = ApplicationBuilder().token(os.getenv("APPLICANT_BOT_TOKEN")).build()

    # * For DEBUG purposes ONLY
    # app.add_handler(MessageHandler(filters.ALL, capture_group_topics))

    # app.add_handler(CallbackQueryHandler(register_country, pattern="^citypage_.*"))

    # Callback Query Handlers
    app.add_handler(CallbackQueryHandler(next_job, pattern="^job_.*"))
    app.add_handler(CallbackQueryHandler(next_application, pattern="^application_.*"))
    app.add_handler(CallbackQueryHandler(next_savedjob, pattern="^savedjob_.*"))

    app.add_handler(CallbackQueryHandler(save_job, pattern="^save_.*"))

    app.add_handler(CallbackQueryHandler(my_profile, pattern="^my_profile$"))
    app.add_handler(CallbackQueryHandler(edit_profile, pattern="^edit_profile$"))
    app.add_handler(CallbackQueryHandler(done_profile, pattern="^done_profile$"))
    app.add_handler(CallbackQueryHandler(update_username, pattern="^update_username$"))
    app.add_handler(
        CallbackQueryHandler(view_jobseeker_profile, pattern="^view_jobseeker_.*")
    )

    # app.add_handler(CallbackQueryHandler(edit_name, pattern="^edit_name$"))

    app.add_handler(apply_job_handler)
    app.add_handler(profile_handler)
    app.add_handler(onboarding_handler)

    # * main menu handler (general)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu))

    # * command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CommandHandler("browse_jobs", browse_jobs))
    app.add_handler(CommandHandler("saved_jobs", saved_jobs))
    app.add_handler(CommandHandler("my_profile", my_profile))
    app.add_handler(CommandHandler("my_applications", my_applications))

    print("Bot is running...")
    app.run_polling(timeout=60)


if __name__ == "__main__":
    main()
