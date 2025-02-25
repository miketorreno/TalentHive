import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    filters,
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
)

from employers.handlers.general import start_command
from employers.states.all import (
    SELECT_COMPANY,
    JOB_TITLE,
    JOB_SITE,
    JOB_TYPE,
    JOB_SECTOR,
    EDUCATION_QUALIFICATION,
    EXPERIENCE_LEVEL,
    GENDER_PREFERENCE,
    JOB_DEADLINE,
    VACANCIES,
    JOB_DESCRIPTION,
    JOB_CITY,
    JOB_COUNTRY,
    SALARY_TYPE,
    SALARY_AMOUNT,
    SALARY_CURRENCY,
    CONFIRM_JOB,
)

from utils.db import execute_query
from utils.helpers import (
    format_date,
    get_all_cities,
    get_categories,
    get_companies,
    get_employer,
    get_jobs,
    is_isalnum_w_space,
    is_valid_date_format,
)
from utils.constants import (
    CURRENT_APPLICANT_INDEX,
    TOTAL_APPLICANTS,
    CURRENT_MYJOB_INDEX,
    TOTAL_MYJOBS,
    ROLE_APPLICANT,
)


async def my_job_posts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    employer = get_employer(update, context)

    if not employer:
        await start_command(update, context)
        return

    myjobs = get_jobs(employer["user_id"])

    if not myjobs:
        keyboard = [[InlineKeyboardButton("Post a Job", callback_data="post_a_job")]]
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "You haven't posted a job yet"
            )
        else:
            await update.message.reply_text("You haven't posted a job yet")
        return

    myjobs_list = [job for job in myjobs]
    # global CURRENT_MYJOB_INDEX
    myjob = myjobs_list[CURRENT_MYJOB_INDEX]
    global TOTAL_MYJOBS
    TOTAL_MYJOBS = len(myjobs_list)
    # CURRENT_MYJOB_INDEX = 0  # Reset index when starting

    myjob_details = (
        f"Job Title: <b>\t{myjob["job_title"]}</b> \n\n"
        f"Job Type: <b>\t{myjob["job_site"]} - {myjob["job_type"]}</b> \n\n"
        f"Work Location: <b>\t{myjob["job_city"]}, {myjob["job_country"]}</b> \n\n"
        f"Applicants Needed: <b>\t{myjob["gender_preference"]}</b> \n\n"
        f"Salary: <b>\t{myjob["salary_amount"]} {myjob["salary_currency"]}, {myjob["salary_type"]}</b> \n\n"
        f"Deadline: <b>\t{format_date(myjob["job_deadline"])}</b> \n\n"
        f"<b>Description</b>: \t{myjob["job_description"]} \n\n"
        f"<b>Requirements</b>: \t{myjob["job_requirements"]} \n\n"
    )

    keyboard = []
    if TOTAL_MYJOBS > 1:
        if CURRENT_MYJOB_INDEX > 0:
            keyboard = [
                [
                    InlineKeyboardButton("Previous", callback_data="myjob_previous"),
                    InlineKeyboardButton("Next", callback_data="myjob_next"),
                ],
                [
                    InlineKeyboardButton("Edit", callback_data="myjob_edit"),
                    InlineKeyboardButton("Close", callback_data="myjob_close"),
                ],
                [
                    InlineKeyboardButton(
                        "View Applicants",
                        callback_data=f"view_applicants_{myjob["job_id"]}",
                    )
                ],
            ]
            if TOTAL_MYJOBS == CURRENT_MYJOB_INDEX + 1:
                keyboard = [
                    [InlineKeyboardButton("Previous", callback_data="myjob_previous")],
                    [
                        InlineKeyboardButton("Edit", callback_data="myjob_edit"),
                        InlineKeyboardButton("Close", callback_data="myjob_close"),
                    ],
                    [
                        InlineKeyboardButton(
                            "View Applicants",
                            callback_data=f"view_applicants_{myjob["job_id"]}",
                        )
                    ],
                ]
        else:
            keyboard = [
                [InlineKeyboardButton("Next", callback_data="myjob_next")],
                [
                    InlineKeyboardButton("Edit", callback_data="myjob_edit"),
                    InlineKeyboardButton("Close", callback_data="myjob_close"),
                ],
                [
                    InlineKeyboardButton(
                        "View Applicants",
                        callback_data=f"view_applicants_{myjob["job_id"]}",
                    )
                ],
            ]

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=myjob_details,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text(
            text=myjob_details,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )


async def next_myjob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CURRENT_MYJOB_INDEX
    query = update.callback_query
    await query.answer()

    if query.data == "myjob_next":
        CURRENT_MYJOB_INDEX += 1
    elif query.data == "myjob_previous":
        CURRENT_MYJOB_INDEX -= 1

    await my_job_posts(update, context)


async def view_applicants(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    job_id = int(query.data.split("_")[-1])

    applicants = execute_query(
        "SELECT u.*, a.* FROM applications a JOIN users u ON a.user_id = u.user_id WHERE a.job_id = %s AND u.role_id = %s ORDER BY a.created_at ASC LIMIT 50",
        (job_id, ROLE_APPLICANT),
    )

    if not applicants:
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="No applicants yet",
            parse_mode="HTML",
        )
        return

    applicants_list = [job for job in applicants]
    # global CURRENT_APPLICANT_INDEX
    applicant = applicants_list[CURRENT_APPLICANT_INDEX]
    global TOTAL_APPLICANTS
    TOTAL_APPLICANTS = len(applicants_list)
    # CURRENT_APPLICANT_INDEX = 0  # Reset index when starting

    applicant_details = (
        f"Name: <b>\t{applicant["name"]}</b> \n"
        f"Email: <b>\t{applicant["email"]}</b> \n"
        f"Phone: <b>\t{applicant["phone"]}</b> \n\n"
        f"<b>Cover Letter:</b> \n{applicant["cover_letter"]} \n\n"
        f"<b>CV:</b> \n{applicant["cv"]} \n\n"
        f"<b>Portfolio:</b> \n{applicant["portfolio"]} \n\n"
    )

    keyboard = [[InlineKeyboardButton("Back to My Jobs", callback_data="my_job_posts")]]
    if TOTAL_APPLICANTS > 1:
        if CURRENT_APPLICANT_INDEX > 0:
            keyboard = [
                [
                    InlineKeyboardButton(
                        "Previous", callback_data="applicant_previous"
                    ),
                    InlineKeyboardButton("Next", callback_data="applicant_next"),
                ],
                [InlineKeyboardButton("Back to My Jobs", callback_data="my_job_posts")],
            ]
            if TOTAL_APPLICANTS == CURRENT_APPLICANT_INDEX + 1:
                keyboard = [
                    [
                        InlineKeyboardButton(
                            "Previous", callback_data="applicant_previous"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "Back to My Jobs", callback_data="my_job_posts"
                        )
                    ],
                ]
        else:
            keyboard = [
                [InlineKeyboardButton("Next", callback_data="applicant_next")],
                [InlineKeyboardButton("Back to My Jobs", callback_data="my_job_posts")],
            ]

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=applicant_details,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text(
            text=applicant_details,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )


async def next_applicant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CURRENT_APPLICANT_INDEX
    query = update.callback_query
    await query.answer()

    if query.data == "applicant_next":
        CURRENT_APPLICANT_INDEX += 1
    elif query.data == "applicant_previous":
        CURRENT_APPLICANT_INDEX -= 1

    await view_applicants(update, context)


async def post_job_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Initiates the job posting process for an employer.

    This function checks if the user is registered as an employer. If the employer is not
    found, it starts the registration command. It then fetches the list of companies
    associated with the employer. If no companies are found, it prompts the user to add
    a company. If companies are available, it displays them as inline keyboard buttons for
    the user to select from.

    Args:
        update (Update): The update object containing information about the user's interaction.
        context (ContextTypes.DEFAULT_TYPE): The context object containing data related to the
            conversation.

    Returns:
        SELECT_COMPANY: The next state in the conversation if companies are found, or ends the
        conversation if no companies are available or an error occurs.
    """

    try:
        employer = get_employer(update, context)

        if not employer:
            await start_command(update, context)
            return

        companies = get_companies(employer["user_id"])
        if not companies:
            keyboard = [
                [InlineKeyboardButton("Add Company", callback_data="create_company")],
            ]
            await update.message.reply_text(
                "You haven't created a company yet",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
            return ConversationHandler.END

        # if not companies:
        #     await update.message.reply_text(
        #         "<i>* No companies found. Please register a company first</i> \n\nGo to \n<b>My Companies > Add Company</b>",
        #         parse_mode="HTML",
        #     )
        #     return ConversationHandler.END

        buttons = [
            InlineKeyboardButton(
                company["name"],
                callback_data=f"company_{company["company_id"]}",
            )
            for company in companies
        ]
        keyboard = [
            buttons[i : i + 2] for i in range(0, len(buttons), 2)
        ]  # Group buttons into rows

        await update.message.reply_text(
            "<b>Let's post a new job, please select company</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return SELECT_COMPANY
    except Exception as e:
        await update.message.reply_text(
            "An error occurred while posting a job. Please try again."
        )
        # Optionally log the error for debugging
        print(f"Error in post_job_start: {e}")
        return ConversationHandler.END


async def select_company(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the selection of a company from the callback query data and prompts for the job title.

    This function processes the user's callback query to confirm the selection of a company.
    It checks if the callback data is valid and extracts the company ID, storing it in the
    user's context data. Upon successful selection, it prompts the user to enter a job title.
    If an error occurs during the process, an error message is sent to the user.

    Args:
        update (Update): The update object containing information about the user's interaction.
        context (ContextTypes.DEFAULT_TYPE): The context object containing data related to the
            conversation.

    Returns:
        JOB_TITLE: The next state in the conversation when a valid company is selected.
        ConversationHandler.END: Ends the conversation if an invalid selection occurs or an
        error is encountered.
    """

    try:
        query = update.callback_query
        await query.answer()

        if not query.data.startswith("company_"):
            await query.message.reply_text(
                "<i>* Invalid selection</i>", parse_mode="HTML"
            )
            return ConversationHandler.END

        context.user_data["company_id"] = query.data.split("_")[1]
        await query.edit_message_text(
            "<b>Please enter job title</b>", parse_mode="HTML"
        )
        return JOB_TITLE
    except Exception as e:
        await query.edit_message_text(
            "An error occurred while selecting your company. Please try again."
        )
        # Optionally log the error for debugging
        print(f"Error in select_company: {e}")
        return ConversationHandler.END


async def job_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Processes the user's input to set the job title and prompts for the job site selection.

    This function extracts the job title from the user's message and validates it to ensure
    it contains only alphabets and numbers. If the validation fails, it prompts the user to
    re-enter the job title. Upon successful validation, it stores the job title in the user's
    context data and presents options for selecting the job site.

    Args:
        update (Update): The update object containing the user's message.
        context (ContextTypes.DEFAULT_TYPE): The context object containing the conversation state
            and user data.

    Returns:
        JOB_TITLE: If the job title validation fails, prompting the user to re-enter the title.
        JOB_SITE: Upon successful validation, prompting the user to select the job site.
        ConversationHandler.END: If an exception occurs during processing.
    """

    try:
        title = update.message.text.strip()

        # if not title.is_isalnum():
        if not is_isalnum_w_space(title):
            await update.message.reply_text(
                "<i>* Company job title should only contain alphabets and numbers.</i> \n\n<b>Please enter job title</b>",
                parse_mode="HTML",
            )
            return JOB_TITLE

        context.user_data["job_title"] = title
        keyboard = [
            [
                InlineKeyboardButton("On-site", callback_data="On-site"),
                InlineKeyboardButton("Remote", callback_data="Remote"),
            ]
        ]
        await update.message.reply_text(
            "<b>Please select job site</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return JOB_SITE
    except Exception as e:
        await update.message.reply_text(
            "An error occurred while saving job title. Please try again."
        )
        # Optionally log the error for debugging
        print(f"Error in job_title: {e}")
        return ConversationHandler.END


async def job_site(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Processes the user's input to set the job site and prompts for the job type selection.

    This function extracts the job site from the user's callback query and validates it to
    ensure it is either "on-site" or "remote". If the validation fails, it prompts the user to
    re-select the job site. Upon successful validation, it stores the job site in the user's
    context data and presents options for selecting the job type.

    Args:
        update (Update): The update object containing the user's callback query.
        context (ContextTypes.DEFAULT_TYPE): The context object containing the conversation state
            and user data.

    Returns:
        JOB_TYPE: Upon successful validation, prompting the user to select the job type.
        ConversationHandler.END: If an exception occurs during processing.
    """

    try:
        query = update.callback_query
        await query.answer()

        context.user_data["job_site"] = query.data
        keyboard = [
            [
                InlineKeyboardButton("Full-time", callback_data="Full-time"),
                InlineKeyboardButton("Part-time", callback_data="Part-time"),
            ],
            [
                InlineKeyboardButton("Contractual", callback_data="Contractual"),
                InlineKeyboardButton("Freelance", callback_data="Freelance"),
            ],
            [
                InlineKeyboardButton("Intern (Paid)", callback_data="Intern (Paid)"),
                InlineKeyboardButton("Intern (Paid)", callback_data="Intern (Paid)"),
            ],
            [InlineKeyboardButton("Volunteer", callback_data="Volunteer")],
        ]
        await query.edit_message_text(
            "<b>Please select job type</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return JOB_TYPE
    except Exception as e:
        await query.edit_message_text(
            "An error occurred while selecting job site. Please try again."
        )
        # Optionally log the error for debugging
        print(f"Error in job_site: {e}")
        return ConversationHandler.END


async def job_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the callback query to select a job type and prompts the user to choose a job sector.

    This function extracts the job type from the callback data, stores it in the user's context data,
    and fetches available job categories to present as inline keyboard buttons for the user to select
    their desired job sector.

    Args:
        update (Update): The update object containing information about the user's interaction.
        context (ContextTypes.DEFAULT_TYPE): The context object containing data related to the conversation.

    Returns:
        JOB_SECTOR: The next state in the conversation for selecting a job sector.
        ConversationHandler.END: If an exception occurs during processing.
    """

    try:
        query = update.callback_query
        await query.answer()

        context.user_data["job_type"] = query.data
        categories = get_categories()
        buttons = [
            InlineKeyboardButton(
                category["name"],
                callback_data=f"{category["name"]}_{category["category_id"]}",
            )
            for category in categories
        ]

        keyboard = [
            buttons[i : i + 2] for i in range(0, len(buttons), 2)
        ]  # Group buttons into rows

        # def get_all_cities():
        #     buttons = [InlineKeyboardButton(city, callback_data=f"{city}") for city in CITIES]

        #     # Organize buttons into 2-column rows
        #     keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]  # Group buttons into rows
        #     keyboard.append([InlineKeyboardButton("Others", callback_data="Others")]),

        #     return InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "<b>Choose a job sector</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return JOB_SECTOR
    except Exception as e:
        await query.edit_message_text(
            "An error occurred while selecting job type. Please try again."
        )
        # Optionally log the error for debugging
        print(f"Error in job_type: {e}")
        return ConversationHandler.END


async def job_sector(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the callback query to select a job sector and prompts the user to choose their educational qualification.

    This function extracts the job category and sector from the callback data, stores them in the user's context data, and presents an inline keyboard for the user to choose their educational qualification level.

    Args:
        update (Update): The update object containing information about the user's interaction.
        context (ContextTypes.DEFAULT_TYPE): The context object containing data related to the conversation.

    Returns:
        EDUCATION_QUALIFICATION: The next state in the conversation for selecting educational qualification.
    """

    try:
        query = update.callback_query
        await query.answer()

        context.user_data["category_id"] = int(query.data.split("_")[1])
        context.user_data["job_sector"] = query.data.split("_")[0]

        keyboard = [
            [
                InlineKeyboardButton(
                    "Secondary School", callback_data="Secondary School"
                ),
                InlineKeyboardButton("Certificate", callback_data="Certificate"),
            ],
            [
                InlineKeyboardButton("TVET", callback_data="TVET"),
                InlineKeyboardButton("Diploma", callback_data="Diploma"),
            ],
            [
                InlineKeyboardButton(
                    "Bachelors Degree", callback_data="Bachelors Degree"
                ),
                InlineKeyboardButton("Masters Degree", callback_data="Masters Degree"),
            ],
            [
                InlineKeyboardButton("Phd", callback_data="Phd"),
                InlineKeyboardButton("Not Required", callback_data="Not Required"),
            ],
        ]
        await query.edit_message_text(
            "<b>Educational Qualification</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return EDUCATION_QUALIFICATION
    except Exception as e:
        await query.edit_message_text(
            "An error occurred while selecting job sector. Please try again."
        )
        # Optionally log the error for debugging
        print(f"Error in job_sector: {e}")
        return ConversationHandler.END


async def education_qualification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the callback query to select an educational qualification and prompts the user to choose an experience level.

    This function stores the selected educational qualification in the user's context data and presents an inline keyboard
    for the user to choose their experience level.

    Args:
        update (Update): The update object containing information about the user's interaction.
        context (ContextTypes.DEFAULT_TYPE): The context object containing data related to the conversation.

    Returns:
        EXPERIENCE_LEVEL: The next state in the conversation for selecting an experience level.
        ConversationHandler.END: If an exception occurs during processing.
    """

    try:
        query = update.callback_query
        await query.answer()

        context.user_data["education"] = query.data

        keyboard = [
            [
                InlineKeyboardButton("Entry", callback_data="Entry"),
                InlineKeyboardButton("Junior", callback_data="Junior"),
            ],
            [
                InlineKeyboardButton("Intermediate", callback_data="Intermediate"),
                InlineKeyboardButton("Senior", callback_data="Senior"),
            ],
            [
                InlineKeyboardButton("Expert", callback_data="Expert"),
                InlineKeyboardButton("Not Required", callback_data="Not Required"),
            ],
        ]
        await query.edit_message_text(
            "<b>Experience Level</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return EXPERIENCE_LEVEL
    except Exception as e:
        await query.edit_message_text(
            "An error occurred while selecting educational qualification. Please try again."
        )
        # Optionally log the error for debugging
        print(f"Error in education_qualification: {e}")
        return ConversationHandler.END


async def experience_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the callback query to select an experience level and prompts the user to choose a gender preference.

    This function stores the selected experience level in the user's context data and presents an inline keyboard
    for the user to choose their preferred gender.

    Args:
        update (Update): The update object containing information about the user's interaction.
        context (ContextTypes.DEFAULT_TYPE): The context object containing data related to the conversation.

    Returns:
        GENDER_PREFERENCE: The next state in the conversation for selecting a gender preference.
        ConversationHandler.END: If an exception occurs during processing.
    """

    try:
        query = update.callback_query
        await query.answer()

        context.user_data["experience"] = query.data

        keyboard = [
            [
                InlineKeyboardButton("Male", callback_data="Male"),
                InlineKeyboardButton("Female", callback_data="Female"),
            ],
            [InlineKeyboardButton("Both", callback_data="Both")],
        ]
        await query.edit_message_text(
            "<b>Gender Preferred</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return GENDER_PREFERENCE
    except Exception as e:
        await query.edit_message_text(
            "An error occurred while selecting experience level. Please try again."
        )
        # Optionally log the error for debugging
        print(f"Error in experience_level: {e}")
        return ConversationHandler.END


async def gender_preference(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the callback query to select a gender preference and prompts the user to enter a job deadline.

    This function stores the selected gender preference in the user's context data and sends a message
    to the user to input the job deadline in the specified format. If an error occurs during this process,
    an error message is sent to the user.

    Args:
        update (Update): The update object containing information about the user's interaction.
        context (ContextTypes.DEFAULT_TYPE): The context object containing data related to the conversation.

    Returns:
        JOB_DEADLINE: The next state in the conversation for entering the job deadline.
        ConversationHandler.END: If an exception occurs during processing.
    """

    try:
        query = update.callback_query
        await query.answer()

        context.user_data["gender"] = query.data

        await query.edit_message_text(
            "<b>Please enter job deadline in YYYY-MM-DD format</b>", parse_mode="HTML"
        )
        return JOB_DEADLINE
    except Exception as e:
        await query.edit_message_text(
            "An error occurred while selecting gender. Please try again."
        )
        # Optionally log the error for debugging
        print(f"Error in gender_preference: {e}")
        return ConversationHandler.END


async def job_deadline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the user's input for the job deadline and prompts the user to enter the number of vacancies.

    This function checks the validity of the entered deadline and stores it in the user's context data if it's valid.
    If the deadline is invalid, an error message is sent to the user. If an exception occurs during this process,
    an error message is sent to the user.

    Args:
        update (Update): The update object containing information about the user's interaction.
        context (ContextTypes.DEFAULT_TYPE): The context object containing data related to the conversation.

    Returns:
        VACANCIES: The next state in the conversation for entering the number of vacancies.
        ConversationHandler.END: If an exception occurs during processing.
    """

    try:
        deadline = update.message.text.strip()

        if not is_valid_date_format(deadline):
            await update.message.reply_text(
                "<i>* Invalid date format</i>\n\n<b>Please enter job deadline in YYYY-MM-DD format</b>",
                parse_mode="HTML",
            )
            return JOB_DEADLINE

        context.user_data["deadline"] = deadline
        await update.message.reply_text(
            "<b>Please enter number of vacancies</b>", parse_mode="HTML"
        )
        return VACANCIES
    except Exception as e:
        await update.message.reply_text(
            "An error occurred while saving job deadline. Please try again."
        )
        print(f"Error in job_deadline: {e}")
        return ConversationHandler.END


async def job_vacancies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the user's input for the number of job vacancies and prompts the user to write the job description.

    This function verifies that the input is a valid number. If the input is invalid, it prompts the user to re-enter
    the number of vacancies. Upon successful validation, it stores the number of vacancies in the user's context data
    and asks the user to provide the job description. If an exception occurs during this process, an error message
    is sent to the user.

    Args:
        update (Update): The update object containing information about the user's interaction.
        context (ContextTypes.DEFAULT_TYPE): The context object containing data related to the conversation.

    Returns:
        JOB_DESCRIPTION: The next state in the conversation for writing the job description.
        VACANCIES: If the input validation fails, prompting the user to re-enter the number of vacancies.
        ConversationHandler.END: If an exception occurs during processing.
    """

    try:
        vacancies = update.message.text.strip()

        if not vacancies.isdigit() or len(vacancies) < 1:
            await update.message.reply_text(
                "<i>* Invalid value</i>\n\n<b>Please enter number of vacancies</b>",
                parse_mode="HTML",
            )
            return VACANCIES

        context.user_data["vacancies"] = vacancies
        await update.message.reply_text(
            "<b>Please write the job description</b>", parse_mode="HTML"
        )
        return JOB_DESCRIPTION
    except Exception as e:
        await update.message.reply_text(
            "An error occurred while saving number of vacancies. Please try again."
        )
        print(f"Error in vacancies: {e}")
        return ConversationHandler.END


async def job_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the user's input for the job description and prompts the user to select a job location.

    This function stores the job description in the user's context data and presents options for selecting a job location.
    If an exception occurs during this process, an error message is sent to the user.

    Args:
        update (Update): The update object containing information about the user's interaction.
        context (ContextTypes.DEFAULT_TYPE): The context object containing data related to the conversation.

    Returns:
        JOB_COUNTRY: The next state in the conversation for selecting a job location.
        ConversationHandler.END: If an exception occurs during processing.
    """

    try:
        job_description = update.message.text.strip()

        # TODO: implement description inhancer

        context.user_data["description"] = job_description
        keyboard = [
            [
                InlineKeyboardButton("Ethiopia", callback_data="Ethiopia"),
                InlineKeyboardButton("Remote", callback_data="Remote"),
            ]
        ]

        await update.message.reply_text(
            "<b>Please select job location</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return JOB_COUNTRY
    except Exception as e:
        await update.message.reply_text(
            "An error occurred while saving job description. Please try again."
        )
        print(f"Error in job_description: {e}")
        return ConversationHandler.END


async def job_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the callback query to select a job country and prompts the user to choose a city.

    This function extracts the job country from the callback data, stores it in the user's context data,
    and presents an inline keyboard for the user to select a city. If the selected job country is "remote",
    it sets the job city as "Anywhere" and proceeds to the salary type selection.

    Args:
        update (Update): The update object containing information about the user's interaction.
        context (ContextTypes.DEFAULT_TYPE): The context object containing data related to the conversation.

    Returns:
        JOB_CITY: The next state in the conversation for selecting a city.
        SALARY_TYPE: If the selected job country is "remote".
        ConversationHandler.END: If an exception occurs during processing.
    """

    try:
        query = update.callback_query
        await query.answer()

        context.user_data["job_country"] = query.data
        if context.user_data["job_country"].lower() == "remote":
            context.user_data["job_city"] = "Anywhere"
            keyboard = [
                [
                    InlineKeyboardButton("Fixed", callback_data="Fixed"),
                    InlineKeyboardButton("Hourly", callback_data="Hourly"),
                ],
                [
                    InlineKeyboardButton("Weekly", callback_data="Weekly"),
                    InlineKeyboardButton("Monthly", callback_data="Monthly"),
                ],
            ]
            await query.edit_message_text(
                "<b>Please select salary type</b>",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML",
            )
            return SALARY_TYPE

        keyboard = get_all_cities()
        await query.edit_message_text(
            "<b>Please select the city</b>", reply_markup=keyboard, parse_mode="HTML"
        )
        return JOB_CITY
    except Exception as e:
        await query.edit_message_text(
            "An error occurred while saving work location. Please try again."
        )
        print(f"Error in job_country: {e}")
        return ConversationHandler.END


async def job_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the callback query to select a job city and prompts the user to choose a salary type.

    This function extracts the job city from the callback data, stores it in the user's context data,
    and presents an inline keyboard for the user to select a salary type.

    Args:
        update (Update): The update object containing information about the user's interaction.
        context (ContextTypes.DEFAULT_TYPE): The context object containing data related to the conversation.

    Returns:
        SALARY_TYPE: The next state in the conversation for selecting a salary type.
        ConversationHandler.END: If an exception occurs during processing.
    """

    try:
        query = update.callback_query
        await query.answer()

        context.user_data["job_city"] = query.data

        keyboard = [
            [
                InlineKeyboardButton("Fixed", callback_data="Fixed"),
                InlineKeyboardButton("Hourly", callback_data="Hourly"),
            ],
            [
                InlineKeyboardButton("Weekly", callback_data="Weekly"),
                InlineKeyboardButton("Monthly", callback_data="Monthly"),
            ],
        ]
        await query.edit_message_text(
            "<b>Please select salary type</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return SALARY_TYPE
    except Exception as e:
        await query.message.reply_text(
            "An error occurred while saving city. Please try again."
        )
        print(f"Error in job_city: {e}")
        return ConversationHandler.END


async def salary_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the callback query to select a salary type and prompts the user to choose a currency.

    This function stores the selected salary type in the user's context data and presents an inline keyboard
    for the user to choose their preferred currency.

    Args:
        update (Update): The update object containing information about the user's interaction.
        context (ContextTypes.DEFAULT_TYPE): The context object containing data related to the conversation.

    Returns:
        SALARY_CURRENCY: The next state in the conversation for selecting a currency.
        ConversationHandler.END: If an exception occurs during processing.
    """

    try:
        query = update.callback_query
        await query.answer()

        context.user_data["salary_type"] = query.data

        keyboard = [
            [
                InlineKeyboardButton("USD", callback_data="USD"),
                InlineKeyboardButton("EUR", callback_data="EUR"),
            ],
            [InlineKeyboardButton("ETB", callback_data="ETB")],
        ]
        await query.edit_message_text(
            "<b>Please select currency</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return SALARY_CURRENCY
    except Exception as e:
        await query.edit_message_text(
            "An error occurred while selecting salary type. Please try again."
        )
        # Optionally log the error for debugging
        print(f"Error in salary_type: {e}")
        return ConversationHandler.END


async def salary_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the callback query to select a salary currency and prompts the user to enter a salary amount.

    This function stores the selected salary currency in the user's context data and presents an inline keyboard
    for the user to enter a salary amount.

    Args:
        update (Update): The update object containing information about the user's interaction.
        context (ContextTypes.DEFAULT_TYPE): The context object containing data related to the conversation.

    Returns:
        SALARY_AMOUNT: The next state in the conversation for entering a salary amount.
        ConversationHandler.END: If an exception occurs during processing.
    """

    try:
        query = update.callback_query
        await query.answer()

        context.user_data["salary_currency"] = query.data

        keyboard = [[InlineKeyboardButton("Skip", callback_data="skip")]]
        await query.edit_message_text(
            "<b>Please enter salary amount</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return SALARY_AMOUNT
    except Exception as e:
        await query.edit_message_text(
            "An error occurred while selecting salary currency. Please try again."
        )
        # Optionally log the error for debugging
        print(f"Error in salary_currency: {e}")
        return ConversationHandler.END


async def salary_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = update.message.text.strip()

        if not amount.isdigit() or len(amount) < 1:
            await update.message.reply_text(
                "<i>* Invalid salary amount</i>\n\n<b>Please enter salary amount</b>",
                parse_mode="HTML",
            )
            return SALARY_AMOUNT

        context.user_data["salary_amount"] = amount

        data = context.user_data
        keyboard = [
            [
                InlineKeyboardButton("Confirm", callback_data="confirm_job"),
                InlineKeyboardButton("Cancel", callback_data="cancel_job"),
            ],
        ]
        job_details = (
            "<b>Please confirm job details</b> \n\n"
            f"<b>Job Title</b>: {data['job_title']} \n\n"
            f"<b>Job Site</b>: {data['job_site']} \n\n"
            f"<b>Job Type</b>: {data['job_type']} \n\n"
            f"<b>Job Sector</b>: {data['job_sector']} \n\n"
            f"<b>Education Qualification</b>: {data['education']} \n\n"
            f"<b>Experience Level</b>: {data['experience']} \n\n"
            f"<b>Gender</b>: {data['gender']} \n\n"
            f"<b>Deadline</b>: {data['deadline']} \n\n"
            f"<b>Vacancies</b>: {data['vacancies']} \n\n"
            f"<b>Description</b>: {data['description']} \n\n"
            f"<b>Country</b>: {data['job_country']} \n\n"
            f"<b>City</b>: {data['job_city']} \n\n"
            f"<b>Salary Type</b>: {data['salary_type']} \n\n"
            f"<b>Salary Amount</b>: {data['salary_amount']} \n\n"
            f"<b>Salary Currency</b>: {data['salary_currency']} \n\n"
        )

        await update.message.reply_text(
            text=job_details,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )

        return CONFIRM_JOB
    except Exception as e:
        await update.message.reply_text(
            "An error occurred while saving salary amount. Please try again."
        )
        print(f"Error in salary_amount: {e}")
        return ConversationHandler.END


async def skip_salary_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        context.user_data["salary_amount"] = None

        data = context.user_data
        keyboard = [
            [
                InlineKeyboardButton("Confirm", callback_data="confirm_job"),
                InlineKeyboardButton("Cancel", callback_data="cancel_job"),
            ],
        ]
        job_details = (
            "<b>Please confirm job details</b> \n\n"
            f"<b>Job Title</b>: {data['job_title']} \n\n"
            f"<b>Job Site</b>: {data['job_site']} \n\n"
            f"<b>Job Type</b>: {data['job_type']} \n\n"
            f"<b>Job Sector</b>: {data['job_sector']} \n\n"
            f"<b>Education Qualification</b>: {data['education']} \n\n"
            f"<b>Experience Level</b>: {data['experience']} \n\n"
            f"<b>Gender</b>: {data['gender']} \n\n"
            f"<b>Deadline</b>: {data['deadline']} \n\n"
            f"<b>Vacancies</b>: {data['vacancies']} \n\n"
            f"<b>Description</b>: {data['description']} \n\n"
            f"<b>Country</b>: {data['job_country']} \n\n"
            f"<b>City</b>: {data['job_city']} \n\n"
            f"<b>Salary Type</b>: {data['salary_type']} \n\n"
            f"<b>Salary Amount</b>: {data['salary_amount']} \n\n"
            f"<b>Salary Currency</b>: {data['salary_currency']} \n\n"
        )

        await query.edit_message_text(
            text=job_details,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )

        return CONFIRM_JOB
    except Exception as e:
        await query.edit_message_text(
            "An error occurred while saving salary amount. Please try again."
        )
        print(f"Error in salary_amount: {e}")
        return ConversationHandler.END


async def confirm_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    employer = get_employer(update, context)

    if not employer:
        await start_command(update, context)
        return

    data = context.user_data
    response = execute_query(
        """
        INSERT INTO jobs (company_id, user_id, category_id, job_title, job_type, job_site, job_sector, education_qualification, experience_level, gender_preference, job_deadline, vacancies, job_description, job_city, job_country, salary_type, salary_amount, salary_currency)        
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING job_id
        """,
        (
            data["company_id"],
            employer["user_id"],
            data["category_id"],
            data["job_title"],
            data["job_type"],
            data["job_site"],
            data["job_sector"],
            data["education"],
            data["experience"],
            data["gender"],
            data["deadline"],
            data["vacancies"],
            data["description"],
            data["job_city"],
            data["job_country"],
            data["salary_type"],
            data["salary_amount"],
            data["salary_currency"],
        ),
    )

    # # Notify the group about the new job
    # notify_group_on_job_post(update, context, job_id)

    job = execute_query(
        "SELECT j.*, c.* FROM jobs j JOIN companies c ON j.company_id = c.company_id WHERE j.user_id = %s ORDER BY j.created_at LIMIT 1",
        (employer["user_id"],),
    )[0]

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

    # job_message = (
    #     f"📌 \t**Job Title:** \t{job['title']} \n\n"
    #     f"🏢 \t**Company:** \t{job['company_name']} \n\n"
    #     f"📍 \t**Location:** \t{job['city']}, {job['country']} \n\n"
    #     f"💼 \t**Type:** \t{job['type']} \n\n"
    #     f"💰 \t**Salary:** \t{job['salary']} \n\n"
    #     f"📝 \t**Description:** \t{job['description']} \n\n"
    #     f"📅 \t**Deadline:** \t{format_date(job['deadline'])} \n\n"
    #     # f"📅 \t**Deadline:** \t{job['deadline']} \n\n"
    # )

    # Generate a deep link to the Applicant Bot
    deep_link_url = f"https://t.me/HulumJobsApplicantBot?start=apply_{job["job_id"]}"

    # Create an InlineKeyboardButton with a URL
    apply_button = InlineKeyboardButton("Apply", url=deep_link_url)
    reply_markup = InlineKeyboardMarkup([[apply_button]])

    # Add an "Apply" button
    # apply_button = InlineKeyboardMarkup(
    #     [[InlineKeyboardButton("Apply", callback_data=f"apply_")]]
    #     # [[InlineKeyboardButton("Apply", callback_data=f"apply_{job_id}")]]
    # )

    await context.bot.send_message(
        chat_id=os.getenv("HULUMJOBS_ETHIOIPA_CHANNEL_ID"),
        text=job_details,
        reply_markup=reply_markup,
        parse_mode="HTML",
    )

    await query.edit_message_text("<b>Job posted successfully</b>", parse_mode="HTML")

    # await query.edit_message_text("Job posted successfully!")
    return ConversationHandler.END


async def cancel_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the cancel job button. This function edits the message text
    of the callback query or the message to indicate that the job posting
    has been canceled, and ends the conversation.

    Args:
        update (Update): The Telegram update.
        context (ContextTypes.DEFAULT_TYPE): The context of the Telegram conversation.
    """

    if update.callback_query:
        await update.callback_query.edit_message_text(
            "<b>Job posting canceled</b>", parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            "<b>Job posting canceled</b>", parse_mode="HTML"
        )
    return ConversationHandler.END


post_job_handler = ConversationHandler(
    entry_points=[
        MessageHandler(filters.TEXT & filters.Regex("^Post a Job$"), post_job_start),
        CommandHandler("post_job", post_job_start),
    ],
    states={
        SELECT_COMPANY: [CallbackQueryHandler(select_company)],
        JOB_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, job_title)],
        JOB_SITE: [CallbackQueryHandler(job_site)],
        JOB_TYPE: [CallbackQueryHandler(job_type)],
        JOB_SECTOR: [CallbackQueryHandler(job_sector)],
        EDUCATION_QUALIFICATION: [CallbackQueryHandler(education_qualification)],
        EXPERIENCE_LEVEL: [CallbackQueryHandler(experience_level)],
        GENDER_PREFERENCE: [CallbackQueryHandler(gender_preference)],
        JOB_DEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, job_deadline)],
        VACANCIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, job_vacancies)],
        JOB_DESCRIPTION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, job_description)
        ],
        # JOB_REQUIREMENTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, job_requirements)],
        JOB_CITY: [CallbackQueryHandler(job_city)],
        JOB_COUNTRY: [CallbackQueryHandler(job_country)],
        SALARY_TYPE: [CallbackQueryHandler(salary_type)],
        SALARY_CURRENCY: [CallbackQueryHandler(salary_currency)],
        SALARY_AMOUNT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, salary_amount),
            CallbackQueryHandler(skip_salary_amount),
        ],
        CONFIRM_JOB: [
            CallbackQueryHandler(confirm_job, pattern="confirm_job"),
            CallbackQueryHandler(cancel_job, pattern="cancel_job"),
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel_job)],
)
