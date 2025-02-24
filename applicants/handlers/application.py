import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    filters,
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
)
from applicants.handlers.general import start_command
from applicants.states.all import (
    COVER_LETTER,
    NEW_CV,
    PORTFOLIO,
    CONFIRM_APPLY,
    CONFIRM_GENERATE,
)
from utils.constants import (
    CURRENT_APPLICATION_INDEX,
    TOTAL_APPLICATIONS,
)
from utils.db import execute_query
from utils.helpers import format_date, get_applicant, get_job, get_telegram_id


async def my_applications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Shows a list of jobs that the user has applied for.

    Args:
        update (Update): The Telegram update.
        context (ContextTypes.DEFAULT_TYPE): The context of the Telegram conversation.
    """

    applicant = get_applicant(update, context)

    if not applicant:
        await start_command(update, context)
        return

    applications = execute_query(
        "SELECT j.*, a.* FROM applications a JOIN jobs j ON a.job_id = j.job_id WHERE a.user_id = %s ORDER BY a.created_at DESC LIMIT 50",
        (applicant["user_id"],),
    )

    if not applications:
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "You haven't applied for any jobs yet."
            )
        else:
            await update.message.reply_text("You haven't applied for any jobs yet.")
        return

    application_list = [job for job in applications]
    # global CURRENT_APPLICATION_INDEX
    application = application_list[CURRENT_APPLICATION_INDEX]
    global TOTAL_APPLICATIONS
    TOTAL_APPLICATIONS = len(application_list)
    # CURRENT_APPLICATION_INDEX = 0  # Reset index when starting

    application_details = (
        f"Job Title: <b>\t{application["job_title"]}</b> \n\n"
        f"Job Type: <b>\t{application["job_site"]} - {application["job_type"]}</b> \n\n"
        f"Work Location: <b>\t{application["job_city"]}, {application["job_country"]}</b> \n\n"
        f"Applicants Needed: <b>\t{application["gender_preference"]}</b> \n\n"
        f"Salary: <b>\t{application["salary_amount"]} {application["salary_currency"]}, {application["salary_type"]}</b> \n\n"
        f"Deadline: <b>\t{format_date(application["job_deadline"])}</b> \n\n"
        f"<b>Description</b>: \t{application["job_description"]} \n\n"
        f"<b>Requirements</b>: \t{application["job_requirements"]} \n\n"
        f"<b>__________________</b>\n\n"
        # f"<b>Applied at</b>: \t{format_date(application["a.created_at"])} \n\n"
        f"<b>Application Status</b>: \t{application["status"].upper()} \n\n"
    )

    # keyboard = []
    # if CURRENT_APPLICATION_INDEX > 0:
    #     keyboard.append([InlineKeyboardButton("Previous", callback_data='job_previous')])
    # if CURRENT_APPLICATION_INDEX < len(job_list) - 1:
    #     keyboard.append([InlineKeyboardButton("Next", callback_data='job_next')])

    if TOTAL_APPLICATIONS > 1:
        if CURRENT_APPLICATION_INDEX > 0:
            keyboard = [
                [
                    InlineKeyboardButton(
                        "Previous", callback_data="application_previous"
                    ),
                    InlineKeyboardButton("Next", callback_data="application_next"),
                ],
            ]
            if TOTAL_APPLICATIONS == CURRENT_APPLICATION_INDEX + 1:
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
    """
    Handles the callback query for navigating to the next or previous application.

    Args:
        update (Update): The Telegram update containing the callback query.
        context (ContextTypes.DEFAULT_TYPE): The context of the Telegram conversation.

    Increments or decrements the global CURRENT_APPLICATION_INDEX based on the user's input
    and calls the my_applications function to display the updated application list.
    """

    global CURRENT_APPLICATION_INDEX
    query = update.callback_query
    await query.answer()

    if query.data == "application_next":
        CURRENT_APPLICATION_INDEX += 1
    elif query.data == "application_previous":
        CURRENT_APPLICATION_INDEX -= 1

    await my_applications(update, context)


async def apply_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the start of an application process by a user.

    This function is called when a user clicks on the "Apply" button on a job post.
    It checks if the user has already applied for the job and if so, exits the
    conversation. Otherwise, it asks the user if they want to write a cover letter
    and provides a button to generate a cover letter with AI.

    Args:
        update (Update): The update object containing information about the user's
            message.
        context (ContextTypes.DEFAULT_TYPE): The context object containing
            information about the conversation.

    Returns:
        COVER_LETTER: The next state of the conversation. The user is asked to
            write a cover letter.
    """

    query = update.callback_query
    await query.answer()
    context.user_data["job_id"] = int(query.data.split("_")[-1])
    applicant = get_applicant(update, context)

    if not applicant:
        await start_command(update, context)
        return

    # checking duplicate
    duplicate = execute_query(
        "SELECT * FROM applications WHERE job_id = %s AND user_id = %s",
        (context.user_data["job_id"], applicant["user_id"]),
    )
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
    """
    Handles the user's input for the cover letter and prompts for CV submission.

    This function saves the user's cover letter text and presents options for
    submitting a new CV. Users can choose to skip CV submission or generate a CV
    with AI assistance.

    Args:
        update (Update): The update object containing the user's message.
        context (ContextTypes.DEFAULT_TYPE): The context object containing the
            conversation state and user data.

    Returns:
        NEW_CV: The next state of the conversation where the user is prompted to
            submit a new CV.
    """

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
    """
    Skips the cover letter submission and prompts the user for CV submission.

    This function is triggered when a user opts to skip writing a cover letter.
    It sets the cover letter in the user's data to None and presents options for
    submitting a new CV. Users can choose to skip CV submission or generate a CV
    with AI assistance.

    Args:
        update (Update): The update object containing the user's interaction data.
        context (ContextTypes.DEFAULT_TYPE): The context object containing the
            conversation state and user data.

    Returns:
        NEW_CV: The next state of the conversation where the user is prompted to
            submit a new CV.
    """

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
    """
    Generates a draft of a cover letter using AI and presents it to the user.

    This function retrieves job and company information from the database
    based on the job ID stored in the user's context data. It then uses
    predefined skills and experience to generate a draft cover letter. The user
    is presented with options to accept, decline, write, or regenerate the cover letter.

    Args:
        update (Update): The update object containing the user's interaction data.
        context (ContextTypes.DEFAULT_TYPE): The context object containing the
            conversation state and user data.

    Returns:
        None: The function sends a message with the generated cover letter and
        options for further actions.
    """

    job = execute_query(
        "SELECT j.*, c.* FROM jobs j JOIN companies c ON j.company_id = c.company_id WHERE job_id = %s",
        (context.user_data["job_id"],),
    )

    job_title = job["job_title"]
    company_name = job["name"]
    job_description = job["job_description"]
    skills = "react, vue, node, mongodb, python, laravel, javascript, typescript"
    experience = "4 years"

    # TODO: Generate cover letter with AI
    letter = "Cover letter generated by AI"
    # letter = cover_letter_generator_one(
    #     job_title, company_name, job_description, skills, experience
    # )

    keyboard = [
        [
            InlineKeyboardButton("Accept", callback_data="accept_cover_letter"),
            InlineKeyboardButton("Decline", callback_data="decline_cover_letter"),
        ],
        [
            InlineKeyboardButton("Write", callback_data="write_cover_letter"),
            InlineKeyboardButton("Regenerate", callback_data="regenerate_cover_letter"),
        ],
    ]

    await update.callback_query.edit_message_text(
        f"<b>Here's your draft:</b> \n\n {letter}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )


async def confirm_generated_cover_letter(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """
    Confirms the generated cover letter and saves it to the user's context data.

    This function is called when the user accepts, declines, writes, or regenerates
    the cover letter. The function saves the cover letter to the user's context data,
    and then determines the next state of the conversation based on the user's input.

    Args:
        update (Update): The update object containing the user's interaction data.
        context (ContextTypes.DEFAULT_TYPE): The context object containing the
            conversation state and user data.

    Returns:
        str: The next state of the conversation.
    """

    query = update.callback_query
    await query.answer()
    context.user_data["cover_letter"] = query.message.text.strip()

    next_state = None
    states = {
        "accept_cover_letter": COVER_LETTER,
        "decline_cover_letter": COVER_LETTER,
        "write_cover_letter": COVER_LETTER,
        "regenerate_cover_letter": COVER_LETTER,
        "skip_cover_letter": COVER_LETTER,
    }
    next_state = states.get(query.data, None)

    return next_state


async def new_cv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the submission of a new CV by the user.

    This function is triggered when a user uploads a document as part of their job application.
    It validates the file type to ensure it is a PDF, DOC, or DOCX file. If the file type is valid,
    the document's file ID is saved to the user's context data and the user is prompted to add
    portfolio links. If the file type is invalid, the user is asked to upload a correct file type
    or skip the step.

    Args:
        update (Update): The update object containing the user's uploaded document.
        context (ContextTypes.DEFAULT_TYPE): The context object containing the conversation state
            and user data.

    Returns:
        int: The next state of the conversation, which can be prompting for portfolio links or
            re-uploading a document if the file type is invalid.
    """

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
    """
    Handles unsupported file uploads by notifying the user of an invalid file type.

    This function is called when a user uploads a file type that is not supported.
    It sends a message to the user indicating the invalid file type and prompts
    them to upload a PDF or Word document instead. The user also has the option
    to skip uploading a new CV.

    Args:
        update (Update): The update object containing the user's message.
        context (ContextTypes.DEFAULT_TYPE): The context object containing the
            conversation state and user data.

    Returns:
        int: The next state of the conversation, which is prompting for a new CV.
    """

    keyboard = [[InlineKeyboardButton("Skip", callback_data="skip_new_cv")]]
    await update.message.reply_text(
        "<i>* invalid file type</i> \n\n<b>Please upload a PDF or Word document</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )
    return NEW_CV


async def skip_new_cv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Skips the new CV submission step and prompts the user for portfolio links.

    This function is triggered when a user opts to skip uploading a new CV.
    It sets the new CV in the user's data to None and presents options for
    adding portfolio links. Users can choose to skip adding portfolio links
    and proceed with the application process.

    Args:
        update (Update): The update object containing the user's interaction data.
        context (ContextTypes.DEFAULT_TYPE): The context object containing the
            conversation state and user data.

    Returns:
        PORTFOLIO: The next state of the conversation where the user is prompted
        to add portfolio links.
    """

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
    """
    Updates the user's portfolio information and displays job details for confirmation.

    This function processes the user's input to extract and store portfolio links in the
    user's context data. It retrieves job details using the job ID stored in the user's
    context, formats these details for display, and prompts the user to confirm or cancel
    the job application. The function ensures that the user's cover letter, CV, and
    portfolio information are included in the confirmation message.

    Args:
        update (Update): The update object containing the user's input message.
        context (ContextTypes.DEFAULT_TYPE): The context object containing the
            conversation state and user data.

    Returns:
        CONFIRM_APPLY: The next state of the conversation where the user is prompted
        to confirm or cancel their application.
    """

    context.user_data["portfolio"] = (
        update.message.text.split(",") if update.message.text else []
    )

    job = get_job(context.user_data["job_id"])
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
    context.user_data["job_title"] = job["job_title"]
    context.user_data["employer_id"] = job["user_id"]

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
    """
    Skips the portfolio submission step and displays job details for application confirmation.

    This function is invoked when a user chooses to bypass adding portfolio links during
    the job application process. It clears any existing portfolio data from the user's
    context and retrieves detailed information about the job the user is applying for.
    The job details, along with any cover letter and CV information, are presented to the
    user with options to confirm or cancel the application.

    Args:
        update (Update): The update object containing the user's interaction data.
        context (ContextTypes.DEFAULT_TYPE): The context object containing the
            conversation state and user data.

    Returns:
        CONFIRM_APPLY: The next state of the conversation where the user is prompted
        to confirm or cancel their application.
    """

    query = update.callback_query
    await query.answer()
    context.user_data["portfolio"] = []

    job = get_job(context.user_data["job_id"])
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
    context.user_data["job_title"] = job["job_title"]
    context.user_data["employer_id"] = job["user_id"]

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
    applicant = get_applicant(update, context)

    if not applicant:
        await start_command(update, context)
        return

    execute_query(
        "INSERT INTO applications (job_id, user_id, cover_letter, cv, portfolio) VALUES (%s, %s, %s, %s, %s)",
        (
            context.user_data["job_id"],
            applicant["user_id"],
            context.user_data["cover_letter"],
            context.user_data["new_cv"],
            json.dumps(context.user_data.get("portfolio", [])),
        ),
    )
    await query.edit_message_text("Application submitted successfully!")

    # TODO: Notify employer
    employer_telegram_id = get_telegram_id(context.user_data["employer_id"])
    await context.bot.send_message(
        chat_id=employer_telegram_id,
        text=f"🔔 A new application has been submitted for this job \n"
        f"<b>Job Title:</b>\t {context.user_data["job_title"]}\n\n"
        f"<b>Applicant:</b>\t {update.effective_user.first_name} {update.effective_user.last_name if update.effective_user.last_name else ''}\n\n",
        parse_mode="HTML",
    )

    return ConversationHandler.END


async def cancel_apply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Cancels the job application process.

    This function is called when a user chooses to cancel their job application.
    It provides a confirmation message to the user and ends the conversation.

    Args:
        update (Update): The update object containing the user's interaction data.
        context (ContextTypes.DEFAULT_TYPE): The context object containing the
            conversation state and user data.

    Returns:
        ConversationHandler.END: The next state of the conversation which ends the
            conversation.
    """

    if update.callback_query:
        query = update.callback_query
        await query.edit_message_text("Application canceled")
    else:
        await update.message.reply_text("Application canceled")

    return ConversationHandler.END


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
        CONFIRM_GENERATE: [
            CallbackQueryHandler(
                confirm_generated_cover_letter, pattern="accept_cover_letter"
            ),
            CallbackQueryHandler(
                confirm_generated_cover_letter, pattern="skip_cover_letter"
            ),
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
