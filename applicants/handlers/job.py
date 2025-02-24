from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ContextTypes,
)

from applicants.handlers.general import start_command
from utils.db import execute_query
from utils.helpers import format_date, get_applicant
from utils.constants import (
    CURRENT_JOB_INDEX,
    TOTAL_JOBS,
    CURRENT_SAVEDJOB_INDEX,
    TOTAL_SAVEDJOBS,
)


async def show_job(update: Update, context: ContextTypes.DEFAULT_TYPE, job_id: str):
    """
    Shows a job with a given job_id.

    Args:
        update (Update): The Telegram update.
        context (ContextTypes.DEFAULT_TYPE): The context of the Telegram conversation.
        job_id (str): The job ID to show.

    Returns:
        None
    """

    job = execute_query(
        "SELECT * FROM jobs WHERE job_id = %s",
        (job_id),
    )

    if not job:
        if update.callback_query:
            await update.callback_query.answer("Job not found.")
        else:
            await update.message.reply_text("Job not found.")
        return

    job_details = (
        f"Job Title: <b>\t{job["job_title"]}</b> \n\n"
        f"Job Type: <b>\t{job["job_site"]} - {job["job_type"]}</b> \n\n"
        f"Work Location: <b>\t{job["job_city"]}, {job["job_country"]}</b> \n\n"
        f"Applicants Needed: <b>\t{job["gender_preference"]}</b> \n\n"
        f"Salary: <b>\t{job["salary_amount"]} {job["salary_currency"]}, {job["salary_type"]}</b> \n\n"
        f"Deadline: <b>\t{format_date(job["job_deadline"])}</b> \n\n"
        f"<b>Description</b>: \t{job["job_description"]} \n\n"
        f"<b>Requirements</b>: \t{job["job_requirements"]} \n\n"
    )

    keyboard = [
        [
            InlineKeyboardButton("Save", callback_data=f"save_{job["job_id"]}"),
            InlineKeyboardButton("Apply", callback_data=f"apply_{job["job_id"]}"),
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


async def browse_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Shows a list of the most recent 50 jobs.

    Args:
        update (Update): The Telegram update.
        context (ContextTypes.DEFAULT_TYPE): The context of the Telegram conversation.

    Returns:
        None
    """

    jobs = execute_query("SELECT * FROM jobs ORDER BY created_at DESC LIMIT 50")

    if not jobs:
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "No jobs available at the moment."
            )
        else:
            await update.message.reply_text("No jobs available at the moment.")
        return

    job_list = [job for job in jobs]
    # global CURRENT_JOB_INDEX
    job = job_list[CURRENT_JOB_INDEX]
    global TOTAL_JOBS
    TOTAL_JOBS = len(job_list)
    # CURRENT_JOB_INDEX = 0  # Reset index when starting

    job_details = (
        f"Job Title: <b>\t{job["job_title"]}</b> \n\n"
        f"Job Type: <b>\t{job["job_site"]} - {job["job_type"]}</b> \n\n"
        f"Work Location: <b>\t{job["job_city"]}, {job["job_country"]}</b> \n\n"
        f"Applicants Needed: <b>\t{job["gender_preference"]}</b> \n\n"
        f"Salary: <b>\t{job["salary_amount"]} {job["salary_currency"]}, {job["salary_type"]}</b> \n\n"
        f"Deadline: <b>\t{format_date(job["job_deadline"])}</b> \n\n"
        f"<b>Description</b>: \t{job["job_description"]} \n\n"
        f"<b>Requirements</b>: \t{job["job_requirements"]} \n\n"
    )

    # keyboard = []
    # if CURRENT_JOB_INDEX > 0:
    #     keyboard.append([InlineKeyboardButton("Previous", callback_data='job_previous')])
    # if CURRENT_JOB_INDEX < len(job_list) - 1:
    #     keyboard.append([InlineKeyboardButton("Next", callback_data='job_next')])

    if TOTAL_JOBS > 1:
        if CURRENT_JOB_INDEX > 0:
            keyboard = [
                [
                    InlineKeyboardButton("Previous", callback_data="job_previous"),
                    InlineKeyboardButton("Next", callback_data="job_next"),
                ],
                [
                    InlineKeyboardButton("Save", callback_data=f"save_{job["job_id"]}"),
                    InlineKeyboardButton(
                        "Apply", callback_data=f"apply_{job["job_id"]}"
                    ),
                ],
            ]
            if TOTAL_JOBS == CURRENT_JOB_INDEX + 1:
                keyboard = [
                    [InlineKeyboardButton("Previous", callback_data="job_previous")],
                    [
                        InlineKeyboardButton(
                            "Save", callback_data=f"save_{job["job_id"]}"
                        ),
                        InlineKeyboardButton(
                            "Apply", callback_data=f"apply_{job["job_id"]}"
                        ),
                    ],
                ]
        else:
            keyboard = [
                [InlineKeyboardButton("Next", callback_data="job_next")],
                [
                    InlineKeyboardButton("Save", callback_data=f"save_{job["job_id"]}"),
                    InlineKeyboardButton(
                        "Apply", callback_data=f"apply_{job["job_id"]}"
                    ),
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


async def next_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the callback query for the next/previous job buttons.

    Args:
        update (Update): The Telegram update.
        context (ContextTypes.DEFAULT_TYPE): The context of the Telegram conversation.
    """

    global CURRENT_JOB_INDEX
    query = update.callback_query
    await query.answer()

    if query.data == "job_next":
        CURRENT_JOB_INDEX += 1
    elif query.data == "job_previous":
        CURRENT_JOB_INDEX -= 1

    await browse_jobs(update, context)


async def saved_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Shows a list of jobs that the user has saved.

    Args:
        update (Update): The Telegram update.
        context (ContextTypes.DEFAULT_TYPE): The context of the Telegram conversation.
    """

    applicant = get_applicant(update, context)

    if not applicant:
        await start_command(update, context)
        return

    savedjobs = execute_query(
        "SELECT j.*, sj.* FROM saved_jobs sj JOIN jobs j ON sj.job_id = j.job_id WHERE sj.user_id = %s ORDER BY sj.created_at DESC LIMIT 50",
        (applicant["user_id"],),
    )

    if not savedjobs:
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "You haven't saved any jobs yet."
            )
        else:
            await update.message.reply_text("You haven't saved any jobs yet.")
        return

    savedjobs_list = [job for job in savedjobs]
    # global CURRENT_SAVEDJOB_INDEX
    savedjob = savedjobs_list[CURRENT_SAVEDJOB_INDEX]
    global TOTAL_SAVEDJOBS
    TOTAL_SAVEDJOBS = len(savedjobs_list)
    # CURRENT_SAVEDJOB_INDEX = 0  # Reset index when starting

    savedjob_details = (
        f"Job Title: <b>\t{savedjob["job_title"]}</b> \n\n"
        f"Job Type: <b>\t{savedjob["job_site"]} - {savedjob["job_type"]}</b> \n\n"
        f"Work Location: <b>\t{savedjob["job_city"]}, {savedjob["job_country"]}</b> \n\n"
        f"Applicants Needed: <b>\t{savedjob["gender_preference"]}</b> \n\n"
        f"Salary: <b>\t{savedjob["salary_amount"]} {savedjob["salary_currency"]}, {savedjob["salary_type"]}</b> \n\n"
        f"Deadline: <b>\t{format_date(savedjob["job_deadline"])}</b> \n\n"
        f"<b>Description</b>: \t{savedjob["job_description"]} \n\n"
        f"<b>Requirements</b>: \t{savedjob["job_requirements"]} \n\n"
    )

    if TOTAL_SAVEDJOBS > 1:
        if CURRENT_SAVEDJOB_INDEX > 0:
            keyboard = [
                [
                    InlineKeyboardButton("Previous", callback_data="savedjob_previous"),
                    InlineKeyboardButton("Next", callback_data="savedjob_next"),
                ],
                [
                    InlineKeyboardButton(
                        "Apply", callback_data=f"apply_{savedjob["job_id"]}"
                    )
                ],
            ]
            if TOTAL_SAVEDJOBS == CURRENT_SAVEDJOB_INDEX + 1:
                keyboard = [
                    [
                        InlineKeyboardButton(
                            "Previous", callback_data="savedjob_previous"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "Apply", callback_data=f"apply_{savedjob["job_id"]}"
                        )
                    ],
                ]
        else:
            keyboard = [
                [InlineKeyboardButton("Next", callback_data="savedjob_next")],
                [
                    InlineKeyboardButton(
                        "Apply", callback_data=f"apply_{savedjob["job_id"]}"
                    )
                ],
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
    """
    Handles the callback query for the next/previous job buttons.

    Args:
        update (Update): The Telegram update.
        context (ContextTypes.DEFAULT_TYPE): The context of the Telegram conversation.
    """

    global CURRENT_SAVEDJOB_INDEX
    query = update.callback_query
    await query.answer()

    if query.data == "savedjob_next":
        CURRENT_SAVEDJOB_INDEX += 1
    elif query.data == "savedjob_previous":
        CURRENT_SAVEDJOB_INDEX -= 1

    await saved_jobs(update, context)


async def save_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Saves a job to the applicant's saved jobs list.

    Args:
        update (Update): The Telegram update containing the callback query.
        context (ContextTypes.DEFAULT_TYPE): The context of the Telegram conversation.

    Retrieves the job ID from the callback query data and checks if the applicant
    has already saved the job. If not, it inserts the job into the saved_jobs
    table associated with the applicant's user ID. Sends a confirmation message
    to the applicant on successful saving or a duplicate message if the job
    is already saved.

    Handles exceptions by notifying the applicant of an error and logs the error
    details for debugging purposes.
    """

    try:
        query = update.callback_query
        await query.answer()
        job_id = int(query.data.split("_")[-1])
        applicant = get_applicant(update, context)

        if not applicant:
            await start_command(update, context)
            return

        # checking duplicate
        duplicate = execute_query(
            "SELECT * FROM saved_jobs WHERE job_id = %s AND user_id = %s",
            (job_id, applicant["user_id"]),
        )
        if duplicate:
            await context.bot.send_message(
                chat_id=query.from_user.id,
                text="You've already saved this job.",
                parse_mode="HTML",
            )
        else:
            response = execute_query(
                "INSERT INTO saved_jobs (job_id, user_id) VALUES (%s, %s)",
                (
                    job_id,
                    applicant["user_id"],
                ),
            )

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
