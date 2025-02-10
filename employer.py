import os
import re
import logging
from datetime import datetime
import psycopg2
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ApplicationBuilder,
    ContextTypes,
)


# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,  # level=logging.INFO | logging.DEBUG
)
logging.getLogger("httpx").setLevel(
    logging.WARNING
)  # avoid all GET and POST requests being logged
logger = logging.getLogger(__name__)


# Connect to PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    database="hulumjobs",
    user="postgres",
    password="postgres",
    port="5432",
)


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
    COMPANY_TYPE,
    STARTUP_TYPE,
    COMPANY_NAME,
    TRADE_LICENSE,
    EMPLOYER_TYPE,
    EMPLOYER_PHOTO,
    COMPANY_AUTH_LETTER,
    CONFIRM_COMPANY,
    CHOOSE_ACTION,
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
    JOB_REQUIREMENTS,
    JOB_CITY,
    JOB_COUNTRY,
    SALARY_TYPE,
    SALARY_AMOUNT,
    SALARY_CURRENCY,
    SKILLS_EXPERTISE,
    CONFIRM_JOB,
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
) = range(49)

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

current_myjob_index = 0
total_myjobs = 0
current_company_index = 0
total_companies = 0
current_applicant_index = 0
total_applicants = 0

GROUP_TOPIC_New_Company_Created_ID = 67
GROUP_TOPIC_New_Employer_Registration_ID = 17


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
        keyboard = [
            ["Post a Job", "My Job Posts"],
            ["My Profile", "My Companies"],
            ["Help"],
            # ["My Companies", "Notifications"],
            # ["My Profile", "Help"],
        ]
        await update.message.reply_text(
            text=f"<b>Hello {(user[3].split()[0]).capitalize()} 👋\t Welcome to HulumJobs!</b> \n\n"
            "<b>🔊 \tPost a Job</b>:\t find the right candidates for you \n\n"
            "<b>📑 \tMy Job posts</b>:\t view & manage your job posts \n\n"
            "<b>🏢 \tMy Companies</b>:\t add & manage your companies \n\n"
            # "<b>🔔 \tNotifications</b>:\t customize notifications you wanna receive \n\n"
            "<b>👤 \tMy Profile</b>:\t manage your profile \n\n"
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

    # * "post a job" is handled by another
    # if choice == "post a job":
    # await update.message.reply_text("Post a job")
    # await post_a_job(update, context)
    if choice == "my job posts":
        await my_job_posts(update, context)
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


async def my_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all jobs posted by the user."""
    user = get_user(update, context)

    if not user:
        await start(update, context)
        return

    # Fetch jobs
    cur = conn.cursor()
    cur.execute("SELECT * FROM jobs WHERE user_id = %s", (user[0],))
    jobs = cur.fetchall()

    if not jobs:
        await update.message.reply_text("You haven't posted any jobs yet.")
        return

    # Format the list of jobs
    message = "**Your Jobs Posts:** \n\n"
    for job in jobs:
        message += f"- **ID:** {job[0]}\n  **Title:** {job[5]}\n  **Description:** {job[6]}\n  **Approval status:** {job[12]}\n\n"

    await update.message.reply_text(message, parse_mode="Markdown")


async def my_job_posts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all companies owned by the user."""
    user = get_user(update, context)

    if not user:
        await start(update, context)
        return

    # Fetch companies
    cur = conn.cursor()
    cur.execute("SELECT * FROM jobs WHERE user_id = %s", (user[0],))
    myjobs = cur.fetchall()

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
    global current_myjob_index
    myjob = myjobs_list[current_myjob_index]
    global total_myjobs
    total_myjobs = len(myjobs_list)
    # current_myjob_index = 0  # Reset index when starting

    myjob_details = (
        f"Job Title: <b>\t{myjob[4]}</b> \n\n"
        f"Job Type: <b>\t{myjob[6]} - {myjob[5]}</b> \n\n"
        f"Work Location: <b>\t{myjob[15]}, {myjob[16]}</b> \n\n"
        f"Salary: <b>\t{myjob[17]}</b> \n\n"
        f"Deadline: <b>\t{format_date(myjob[11])}</b> \n\n"
        f"<b>Description</b>: \n{myjob[13]} \n\n"
        f"<b>Requirements</b>: \n{myjob[14]} \n\n"
    )

    keyboard = []
    if total_myjobs > 1:
        if current_myjob_index > 0:
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
                        "View Applicants", callback_data=f"view_applicants_{myjob[0]}"
                    )
                ],
            ]
            if total_myjobs == current_myjob_index + 1:
                keyboard = [
                    [InlineKeyboardButton("Previous", callback_data="myjob_previous")],
                    [
                        InlineKeyboardButton("Edit", callback_data="myjob_edit"),
                        InlineKeyboardButton("Close", callback_data="myjob_close"),
                    ],
                    [
                        InlineKeyboardButton(
                            "View Applicants",
                            callback_data=f"view_applicants_{myjob[0]}",
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
                        "View Applicants", callback_data=f"view_applicants_{myjob[0]}"
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
    global current_myjob_index
    query = update.callback_query
    await query.answer()  # Acknowledge the callback

    if query.data == "myjob_next":
        current_myjob_index += 1
    elif query.data == "myjob_previous":
        current_myjob_index -= 1

    await my_job_posts(update, context)


async def view_applicants(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all companies owned by the user."""
    query = update.callback_query
    await query.answer()
    job_id = int(query.data.split("_")[-1])

    # Fetch applicants
    cur = conn.cursor()
    # cur.execute("SELECT * FROM applications WHERE job_id = %s", (job_id,))
    cur.execute(
        "SELECT u.*, a.* FROM applications a JOIN users u ON a.user_id = u.user_id WHERE a.job_id = %s AND u.role_id = 1 ORDER BY a.created_at ASC LIMIT 50",
        (job_id,),
    )
    applicants = cur.fetchall()

    if not applicants:
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="No applicants yet",
            parse_mode="HTML",
        )
        return

    applicants_list = [job for job in applicants]
    global current_applicant_index
    applicant = applicants_list[current_applicant_index]
    global total_applicants
    total_applicants = len(applicants_list)
    # current_applicant_index = 0  # Reset index when starting

    applicant_details = (
        f"Name: <b>\t{applicant[4]}</b> \n"
        f"Email: <b>\t{applicant[7]}</b> \n"
        f"Phone: <b>\t{applicant[8]}</b> \n\n"
        f"<b>Cover Letter:</b> \n{applicant[25]} \n\n"
        f"<b>CV:</b> \n{applicant[26]} \n\n"
        f"<b>Portfolio:</b> \n{applicant[27]} \n\n"
    )

    keyboard = [[InlineKeyboardButton("Back to My Jobs", callback_data="my_job_posts")]]
    if total_applicants > 1:
        if current_applicant_index > 0:
            keyboard = [
                [
                    InlineKeyboardButton(
                        "Previous", callback_data="applicant_previous"
                    ),
                    InlineKeyboardButton("Next", callback_data="applicant_next"),
                ],
                [InlineKeyboardButton("Back to My Jobs", callback_data="my_job_posts")],
            ]
            if total_applicants == current_applicant_index + 1:
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
    global current_applicant_index
    query = update.callback_query
    await query.answer()  # Acknowledge the callback

    if query.data == "applicant_next":
        current_applicant_index += 1
    elif query.data == "applicant_previous":
        current_applicant_index -= 1

    await view_applicants(update, context)


async def my_companies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all companies owned by the user."""
    user = get_user(update, context)

    if not user:
        await start(update, context)
        return

    # Fetch companies
    cur = conn.cursor()
    cur.execute("SELECT * FROM companies WHERE user_id = %s", (user[0],))
    companies = cur.fetchall()

    if not companies:
        keyboard = [
            [InlineKeyboardButton("Add Company", callback_data="create_company")],
        ]
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "You haven't created a company yet",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        else:
            await update.message.reply_text(
                "You haven't created a company yet",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        return

    company_list = [job for job in companies]
    global current_company_index
    company = company_list[current_company_index]
    global total_companies
    total_companies = len(company_list)
    # current_company_index = 0  # Reset index when starting

    company_details = (
        f"Name: <b>\t{company[4]}{' \t✅' if company[9] else ''}</b> \n\n"
        f"Description: <b>\t{company[7]}</b> \n\n"
        f"Approval status: <b>\t{company[8]}</b> \n\n"
        f"Verified: <b>\t{company[9]}</b> \n\n"
    )

    keyboard = []
    if total_companies > 1:
        if current_company_index > 0:
            keyboard = [
                [
                    InlineKeyboardButton(
                        "Previous", callback_data="mycompany_previous"
                    ),
                    InlineKeyboardButton("Next", callback_data="mycompany_next"),
                ],
                [InlineKeyboardButton("Add Company", callback_data="create_company")],
            ]
            if total_companies == current_company_index + 1:
                keyboard = [
                    [
                        InlineKeyboardButton(
                            "Previous", callback_data="mycompany_previous"
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            "Add Company", callback_data="create_company"
                        )
                    ],
                ]
        else:
            keyboard = [
                [InlineKeyboardButton("Next", callback_data="mycompany_next")],
                [InlineKeyboardButton("Add Company", callback_data="create_company")],
            ]

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=company_details,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text(
            text=company_details,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )


async def next_mycompany(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_company_index
    query = update.callback_query
    await query.answer()  # Acknowledge the callback

    if query.data == "mycompany_next":
        current_company_index += 1
    elif query.data == "mycompany_previous":
        current_company_index -= 1

    await my_companies(update, context)


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
        "UPDATE users SET name = %s WHERE telegram_id = %s AND role_id = 2",
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
        "UPDATE users SET username = %s WHERE telegram_id = %s AND role_id = 2",
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
            "UPDATE users SET gender = %s WHERE telegram_id = %s AND role_id = 2",
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
                    "UPDATE users SET dob = %s WHERE telegram_id = %s AND role_id = 2",
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
            "UPDATE users SET country = %s WHERE telegram_id = %s AND role_id = 2",
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
            "UPDATE users SET city = %s WHERE telegram_id = %s AND role_id = 2",
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
            "UPDATE users SET email = %s WHERE telegram_id = %s AND role_id = 2",
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
            "UPDATE users SET phone = %s WHERE telegram_id = %s AND role_id = 2",
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


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        text="<b>Help</b>\n\n"
        "<b>Post a Job</b> - find the right candidates for you \n\n"
        "<b>My Job posts</b> - view & manage your job posts \n\n"
        "<b>My Companies</b> - add & manage your companies \n\n"
        # "<b>Notifications</b> - customize notifications you wanna receive \n\n"
        "<b>My Profile</b> - manage your profile \n\n"
        "<b>Help</b> - show help message \n\n",
        parse_mode="HTML",
    )
    return


# Create company conversation
async def create_company_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()

        keyboard = [
            [
                InlineKeyboardButton("Company", callback_data="company"),
                InlineKeyboardButton("Startup", callback_data="startup"),
            ]
        ]

        await query.edit_message_text(
            "<b>Let's create your company, please select the type of your company</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return COMPANY_TYPE
    except Exception as e:
        await query.edit_message_text(
            "An error occurred creating your company. Please try again."
        )
        # Optionally log the error for debugging
        print(f"Error in create_company_start: {e}")
        return ConversationHandler.END


async def company_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()

        context.user_data["company_type"] = query.data
        if query.data == "company":
            context.user_data["startup_type"] = None
            await query.edit_message_text(
                "<b>Please enter the name of your company</b>", parse_mode="HTML"
            )
            return COMPANY_NAME
        elif query.data == "startup":
            keyboard = [
                [
                    InlineKeyboardButton("Licensed", callback_data="licensed"),
                    InlineKeyboardButton("Unlicensed", callback_data="unlicensed"),
                ]
            ]
            await query.edit_message_text(
                "<b>Please select the type of your startup</b>",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML",
            )
            return STARTUP_TYPE
        else:
            await query.edit_message_text(
                "An error occurred with your company type. Please try again."
            )
            # Optionally log the error for debugging
            print(f"Error in company_photo: There's a third company type")
            return ConversationHandler.END
    except Exception as e:
        await query.edit_message_text(
            "An error occurred while saving your company type. Please try again."
        )
        # Optionally log the error for debugging
        print(f"Error in company_type: {e}")
        return ConversationHandler.END


async def startup_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()

        context.user_data["startup_type"] = query.data
        await query.edit_message_text(
            "<b>Please enter the name of your company</b>", parse_mode="HTML"
        )
        return COMPANY_NAME
    except Exception as e:
        await query.edit_message_text(
            "An error occurred while saving your startup type. Please try again."
        )
        # Optionally log the error for debugging
        print(f"Error in startup_type: {e}")
        return ConversationHandler.END


async def company_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        name = update.message.text.strip()

        if not name.isalnum():
            await update.message.reply_text(
                "<i>* Company name should only contain alphabets and numbers.</i>\n\n<b>Please enter the name your company</b>",
                parse_mode="HTML",
            )
            return COMPANY_NAME

        context.user_data["name"] = name
        if (
            context.user_data["company_type"] == "company"
            or context.user_data["startup_type"] == "licensed"
        ):
            await update.message.reply_text(
                "<b>Please upload your trade license</b> \n\n<i>* you can upload pdf or photo</i>",
                parse_mode="HTML",
            )
            return TRADE_LICENSE
        elif context.user_data["startup_type"] == "unlicensed":
            context.user_data["trade_license"] = None
            keyboard = [
                [
                    InlineKeyboardButton("Founder", callback_data="founder"),
                    InlineKeyboardButton("Recruiter", callback_data="recruiter"),
                ]
            ]

            await update.message.reply_text(
                "<b>Are you the founder or recruiter?</b>",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML",
            )
            return EMPLOYER_TYPE
        else:
            await update.message.reply_text(
                "An error occurred while saving your company name. Please try again."
            )
            # Optionally log the error for debugging
            print(f"Error in company_name: There's a third company type")
            return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(
            "An error occurred while saving your company name. Please try again."
        )
        # Optionally log the error for debugging
        print(f"Error in company_name: {e}")
        return ConversationHandler.END


async def trade_license(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message.photo:
            await update.message.reply_text(
                "<i>* invalid format.</i>\n\n<b>Please upload your trade license</b>",
                parse_mode="HTML",
            )
            return TRADE_LICENSE

        context.user_data["trade_license"] = update.message.photo[-1].file_id
        keyboard = [
            [
                InlineKeyboardButton(
                    "General Manager", callback_data="general_manager"
                ),
                InlineKeyboardButton("Recruiter", callback_data="recruiter"),
            ]
        ]

        await update.message.reply_text(
            "<b>Are you the general manager or recruiter?</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return EMPLOYER_TYPE
    except Exception as e:
        await update.message.reply_text(
            "An error occurred while uploading your trade license. Please try again."
        )
        # Optionally log the error for debugging
        print(f"Error in trade_license: {e}")
        return ConversationHandler.END


async def unsupported_trade_license(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text(
            "<i>* invalid file type</i>\n\n<b>Please upload a PHOTO</b>",
            parse_mode="HTML",
        )
        return TRADE_LICENSE
    except Exception as e:
        await update.message.reply_text(
            "An error occurred with your trade license. Please try again."
        )
        # Optionally log the error for debugging
        print(f"Error in unsupported_trade_license: {e}")
        return ConversationHandler.END


async def employer_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()

        context.user_data["employer_type"] = query.data
        await query.edit_message_text(
            "<b>Please upload your ID photo</b>", parse_mode="HTML"
        )
        return EMPLOYER_PHOTO
    except Exception as e:
        await query.edit_message_text(
            "An error occurred while saving employer type. Please try again."
        )
        # Optionally log the error for debugging
        print(f"Error in employer_type: {e}")
        return ConversationHandler.END


async def employer_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message.photo:
            await update.message.reply_text(
                "<i>* invalid format.</i>\n\n<b>Please upload your ID photo</b>",
                parse_mode="HTML",
            )
            return EMPLOYER_PHOTO

        context.user_data["employer_photo"] = update.message.photo[-1].file_id
        keyboard = [
            [
                InlineKeyboardButton("Confirm", callback_data="confirm_company"),
                InlineKeyboardButton("Cancel", callback_data="cancel_company"),
            ]
        ]
        company_type = context.user_data["company_type"]
        startup_type = (
            context.user_data["startup_type"] if company_type != "company" else ""
        )
        company_details = (
            f"<b>COMPANY INFO</b>\n\n"
            f"Company Name: {context.user_data["name"]}\n\n"
            # f"Company Type: {context.user_data["company_type"]}\n\n"
            f"{'Type: ' + startup_type.capitalize() + ' Startup \n\n' if company_type == 'startup' else ''}"
            f"{'Trade License Photo: \t✅ \n\n' if startup_type != 'unlicensed' else ''}"
            f"Employer Photo: \t✅\n\n"
        )

        if (
            context.user_data["employer_type"] == "general_manager"
            or context.user_data["employer_type"] == "founder"
        ):
            await update.message.reply_text(
                text=company_details,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML",
            )
            return CONFIRM_COMPANY
        # elif context.user_data['employer_type'] == 'founder':
        #     await update.message.reply_text(
        #         text=company_details,
        #         reply_markup=InlineKeyboardMarkup(keyboard),
        #         parse_mode='HTML'
        #     )
        #     return CONFIRM_COMPANY
        elif context.user_data["employer_type"] == "recruiter":
            await update.message.reply_text(
                "<b>Please upload recruiter authorization letter</b>", parse_mode="HTML"
            )
            return COMPANY_AUTH_LETTER
        else:
            await update.message.reply_text(
                "An error occurred while uploading your photo. Please try again."
            )
            # Optionally log the error for debugging
            print(f"Error in employer_photo: There's a fourth employer type")
            return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(
            "An error occurred while uploading your photo. Please try again."
        )
        # Optionally log the error for debugging
        print(f"Error in employer_photo: {e}")
        return ConversationHandler.END


async def unsupported_employer_photo(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    try:
        await update.message.reply_text(
            "<i>* invalid file type</i>\n\n<b>Please upload a PHOTO</b>",
            parse_mode="HTML",
        )
        return EMPLOYER_PHOTO
    except Exception as e:
        await update.message.reply_text(
            "An error occurred with your photo. Please try again."
        )
        # Optionally log the error for debugging
        print(f"Error in unsupported_employer_photo: {e}")
        return ConversationHandler.END


async def company_auth_letter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.message.document:
            # Validate the file type
            file_name = update.message.document.file_name
            if not file_name.endswith((".pdf", ".doc", ".docx")):
                await update.message.reply_text(
                    "Invalid file type. Please upload a PDF or Word document.",
                    parse_mode="HTML",
                )
                return COMPANY_AUTH_LETTER

            # Save the file ID
            context.user_data["auth_letter"] = update.message.document.file_id
            keyboard = [
                [
                    InlineKeyboardButton("Confirm", callback_data="confirm_company"),
                    InlineKeyboardButton("Cancel", callback_data="cancel_company"),
                ]
            ]
            company_type = context.user_data["company_type"]
            startup_type = (
                context.user_data["startup_type"] if company_type != "company" else ""
            )
            auth_letter = context.user_data["auth_letter"]
            company_details = (
                f"<b>COMPANY INFO</b>\n\n"
                f"Company Name: {context.user_data["name"]}\n\n"
                # f"Company Type: {context.user_data["company_type"]}\n\n"
                f"{'Type: ' + startup_type.capitalize() + ' Startup \n\n' if company_type == 'startup' else ''}"
                f"{'Trade License Photo: \t✅ \n\n' if startup_type != 'unlicensed' else ''}"
                f"Employer Photo: \t✅\n\n"
                f"{'Authorization Letter: \t✅' if auth_letter else ''}\n\n"
            )
            await update.message.reply_text(
                text=company_details,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML",
            )
            return CONFIRM_COMPANY
        else:
            await update.message.reply_text(
                "<b>Please upload a valid document</b>", parse_mode="HTML"
            )
            return COMPANY_AUTH_LETTER
    except Exception as e:
        await update.message.reply_text(
            "An error occurred while uploading your authorization letter. Please try again."
        )
        # Optionally log the error for debugging
        print(f"Error in company_auth_letter: {e}")
        return ConversationHandler.END


async def unsupported_auth_letter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text(
            "<i>* invalid file type</i>\n\n<b>Please upload a PDF or Word document</b>",
            parse_mode="HTML",
        )
        return COMPANY_AUTH_LETTER
    except Exception as e:
        await update.message.reply_text(
            "An error occurred with your authorization letter. Please try again."
        )
        # Optionally log the error for debugging
        print(f"Error in unsupported_auth_letter: {e}")
        return ConversationHandler.END


async def confirm_company(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        data = context.user_data

        user = get_user(update, context)

        if not user:
            await start(update, context)
            return

        cur = conn.cursor()
        cur.execute(
            "INSERT INTO companies (user_id, type, startup_type, name, trade_license, employer_photo, created_by) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (
                user[0],
                data["company_type"],
                data["startup_type"],
                data["name"],
                data["trade_license"],
                data["employer_photo"],
                data["employer_type"],
            ),
        )
        conn.commit()

        # Notify the group about the new company creation
        await notify_group_on_creation(update, context, data)

        await query.edit_message_text(
            "<b>Company created successfully!</b>", parse_mode="HTML"
        )
        return ConversationHandler.END
    except Exception as e:
        await query.edit_message_text(
            "An error occurred while saving your company details. Please try again."
        )
        # Optionally log the error for debugging
        print(f"Error in confirm_company: {e}")
        return ConversationHandler.END


async def cancel_company(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "<b>Company creation canceled</b>", parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            "<b>Company creation canceled</b>", parse_mode="HTML"
        )

    return ConversationHandler.END


async def cancel_company_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "<b>Company creation canceled</b>", parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            "<b>Company creation canceled</b>", parse_mode="HTML"
        )
    return ConversationHandler.END


# Post job conversation
async def post_job_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = get_user(update, context)

        if not user:
            await start(update, context)
            return

        companies = fetch_companies(user[0])

        if not companies:
            await update.message.reply_text(
                "<i>* No companies found. Please register a company first</i> \n\n<b>Go to My Companies > Add Company</b>",
                parse_mode="HTML",
            )
            return ConversationHandler.END

        buttons = [
            InlineKeyboardButton(company[4], callback_data=f"company_{company[0]}")
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
    try:
        query = update.callback_query
        await query.answer()

        if not query.data.startswith("company_"):
            await query.message.reply_text(
                "<i>* invalid selection</i>", parse_mode="HTML"
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
                InlineKeyboardButton("On-site", callback_data="on-site"),
                InlineKeyboardButton("Remote", callback_data="remote"),
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
    try:
        query = update.callback_query
        await query.answer()

        context.user_data["job_type"] = query.data
        categories = fetch_categories()
        buttons = [
            InlineKeyboardButton(name, callback_data=f"{name}_{category_id}")
            for category_id, name in categories
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
    try:
        query = update.callback_query
        await query.answer()

        context.user_data["category_id"] = query.data.split("_")[1]
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
    try:
        deadline = update.message.text.strip()

        # TODO: implement data checker

        if not is_valid_date_format(deadline):
            await update.message.reply_text(
                "<i>* invalid date format</i>\n\n<b>Please enter job deadline in YYYY-MM-DD format</b>",
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
    try:
        vacancies = update.message.text.strip()

        if not vacancies.isdigit() or len(vacancies) < 1:
            await update.message.reply_text(
                "<i>* invalid value</i>\n\n<b>Please enter number of vacancies</b>",
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
    try:
        job_description = update.message.text.strip()

        # TODO: implement description checker

        context.user_data["description"] = job_description
        keyboard = [[InlineKeyboardButton("Ethiopia", callback_data="Ethiopia")]]

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
    try:
        query = update.callback_query
        await query.answer()

        keyboard = get_all_cities()
        context.user_data["job_country"] = query.data
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
        salary_amount = update.message.text.strip()

        if not salary_amount.isdigit() or len(salary_amount) < 1:
            await update.message.reply_text(
                "<i>* invalid salary amount</i>\n\n<b>Please enter salary amount</b>",
                parse_mode="HTML",
            )
            return SALARY_AMOUNT

        context.user_data["salary_amount"] = salary_amount
        keyboard = [[InlineKeyboardButton("Skip", callback_data="skip")]]
        await update.message.reply_text(
            "<b>Finally, please pick some soft skills (optional)</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )

        # await skills_expertise(update, context)

        return SKILLS_EXPERTISE
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

        keyboard = [[InlineKeyboardButton("Skip", callback_data="skip")]]
        await query.edit_message_text(
            "<b>Finally, please pick some soft skills (optional)</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )

        # await skills_expertise(update, context)

        return SKILLS_EXPERTISE
    except Exception as e:
        await query.edit_message_text(
            "An error occurred while saving salary amount. Please try again."
        )
        print(f"Error in salary_amount: {e}")
        return ConversationHandler.END


async def skills_expertise(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = context.user_data
    keyboard = [
        [
            InlineKeyboardButton("Confirm", callback_data="confirm_job"),
            InlineKeyboardButton("Cancel", callback_data="cancel_job"),
        ],
    ]
    job_details = (
        f"<b>Please confirm job details</b> \n\n"
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
    return CONFIRM_JOB


# async def collect_deadline(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     context.user_data["deadline"] = update.message.text.strip()
#     keyboard = [
#         [
#             InlineKeyboardButton("Confirm", callback_data='confirm_job'),
#             InlineKeyboardButton("Cancel", callback_data='cancel_job')
#         ],
#     ]

#     try:
#         job = context.user_data

#         job_details = f"\nJob Title: <b>\t{job['title']}</b> \n\nJob Type: <b>\t</b> \n\nWork Location: <b>\t{job['city']}, {job['country']}</b> \n\nSalary: <b>\t{job['salary']}</b> \n\nDeadline: <b>\t{format_date_for_db(job['deadline'])}</b> \n\n<b>Description</b>: \t{job['description']} \n\n<b>Requirements</b>: \t{job['requirements']} \n\n"

#         # message = (
#         #     "Please confirm the job details: \n\n"
#         #     f"Title: {user_data['title']} \n\n"
#         #     f"Description: {user_data['description']} \n\n"
#         #     f"Requirements: {user_data['requirements']} \n\n"
#         #     f"City: {user_data['city']} \n\n"
#         #     f"Country: {user_data['country']} \n\n"
#         #     f"Salary: {user_data['salary']} \n\n"
#         #     f"Deadline: {user_data['deadline']} \n\n"
#         #     "Post job?"
#         # )
#         await update.message.reply_text(
#             job_details,
#             reply_markup=InlineKeyboardMarkup(keyboard),
#             parse_mode='HTML'
#         )
#         return CONFIRM_JOB
#     except ValueError:
#         await update.message.reply_text("Invalid date format. Please use YYYY-MM-DD.")
#         return JOB_DEADLINE


async def confirm_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = get_user(update, context)

    if not user:
        await start(update, context)
        return

    data = context.user_data
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO jobs (company_id, user_id, category_id, job_title, job_type, job_site, job_sector, education_qualification, experience_level, gender_preference, job_deadline, vacancies, job_description, job_city, job_country, salary_type, salary_amount, salary_currency)        
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING job_id
        """,
        (
            data["company_id"],
            user[0],
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
    conn.commit()
    job_id = cur.fetchone()[0]

    # # Notify the group about the new job
    # notify_group_on_job_post(update, context, job_id)

    # cur = conn.cursor()
    cur.execute(
        "SELECT j.*, c.* FROM jobs j JOIN companies c ON j.company_id = c.company_id WHERE job_id = %s",
        (job_id,),
    )
    job = cur.fetchone()

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

    # Post job to the channel
    # job_message = (
    #     f"📌 \t**Job Title:** \t{context.user_data['title']} \n\n"
    #     # f"🏢 \t**Company:** \t{context.user_data['company_name']} \n\n"
    #     f"📍 \t**Location:** \t{context.user_data['city']}, {context.user_data['country']} \n\n"
    #     # f"💼 \t**Type:** \t{context.user_data['type']} \n\n"
    #     f"💰 \t**Salary:** \t{context.user_data['salary']} \n\n"
    #     f"📝 \t**Description:** \t{context.user_data['description']} \n\n"
    #     f"📅 \t**Deadline:** \t{context.user_data['deadline']} \n\n"
    #     # f"📅 \t**Deadline:** \t{format_date(context.user_data['deadline'])} \n\n"
    # )

    # Generate a deep link to the Applicant Bot
    deep_link_url = f"https://t.me/HulumJobsApplicantBot?start=apply_{job_id}"

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

    await query.edit_message_text(
        "<b>Job posted successfully and shared to the channel!</b>", parse_mode="HTML"
    )

    # await query.edit_message_text("Job posted successfully!")
    return ConversationHandler.END


async def cancel_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "<b>Job posting canceled</b>", parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            "<b>Job posting canceled</b>", parse_mode="HTML"
        )
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
                "<i>* invalid email format.</i>\n\nPlease enter your email address",
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
                "<i>* invalid phone number.</i>\n\nPlease enter your phone number",
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
                "<i>* invalid age.</i>\n\nPlease enter your age between 10 and 100",
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

        context.user_data["job_country"] = "Ethiopia"
        keyboard = get_all_cities()
        await update.message.reply_text(
            "<b>Please select your city</b>", reply_markup=keyboard, parse_mode="HTML"
        )
        return REGISTER_CITY
    except Exception as e:
        await update.message.reply_text(
            "An error occurred while saving your age. Please try again."
        )
        print(f"Error in register_dob: {e}")
        return ConversationHandler.END


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
        await update.effective_message.reply_text(
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
            role_id = 2  # Assuming role_id is 2 for the employer role

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
                ["Post a Job", "My Job Posts"],
                ["My Profile", "My Companies"],
                ["Help"],
                # ["My Companies", "Notifications"],
                # ["My Profile", "Help"],
            ]
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"<b>Hello {user_data['firstname'].capitalize()} 👋\t Welcome to HulumJobs!</b> \n\n"
                "<b>🔊 \tPost a Job</b>:\t find the right candidates for you \n\n"
                "<b>📑 \tMy Job posts</b>:\t view & manage your job posts \n\n"
                "<b>🏢 \tMy Companies</b>:\t add & manage your companies \n\n"
                # "<b>🔔 \tNotifications</b>:\t customize notifications you wanna receive \n\n"
                "<b>👤 \tMy Profile</b>:\t manage your profile \n\n"
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


# * HELPERS (will be extracted to a separate helpers.py file)
def get_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        telegram_id = update.callback_query.from_user.id
    else:
        telegram_id = update.effective_user.id

    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM users WHERE telegram_id = %s AND role_id = 2", (telegram_id,)
    )
    user = cur.fetchone()
    return user


def get_user_from_telegram_id(
    update: Update, context: ContextTypes.DEFAULT_TYPE, telegram_id
):
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM users WHERE telegram_id = %s AND role_id = 2", (telegram_id,)
    )
    user = cur.fetchone()
    return user


def format_date(date):
    return date.strftime("%B %d, %Y")


def format_date_for_db(date):
    return datetime.strptime(date, "%Y-%m-%d")


def is_valid_email(email):
    # regex pattern for validating an email
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def fetch_companies(user_id):
    cur = conn.cursor()
    cur.execute("SELECT * FROM companies WHERE user_id = %s", (user_id,))
    companies = cur.fetchall()
    return companies


def fetch_categories():
    cur = conn.cursor()
    cur.execute("SELECT category_id, name FROM categories")
    categories = cur.fetchall()
    return categories


def is_isalnum_w_space(s):
    if not s:
        return False

    # Check if all characters are alphanumeric or spaces
    return all(char.isalnum() or char.isspace() for char in s)


def is_valid_date_format(date_string):
    # Regular expression pattern for YYYY-M-D or YYYY-MM-DD
    pattern = r"^\d{4}-(\d{1,2})-(\d{1,2})$"

    # Check if the date string matches the pattern
    match = re.match(pattern, date_string)
    if not match:
        return False

    # Extract month and day from the match
    month = int(match.group(1))
    day = int(match.group(2))

    # Check if month is valid
    if month < 1 or month > 12:
        return False

    # Check if day is valid based on the month
    if day < 1 or day > 31:
        return False

    # Check for months with specific day limits
    if month in {4, 6, 9, 11} and day > 30:
        return False
    if month == 2:
        # Check for leap year
        year = int(date_string[:4])
        if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
            if day > 29:  # Leap year
                return False
        else:
            if day > 28:  # Non-leap year
                return False

    return True


async def notify_group_on_registration(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_data,
    topic_id=GROUP_TOPIC_New_Employer_Registration_ID,
):
    view_keyboard = [
        [
            InlineKeyboardButton(
                "View Profile",
                callback_data=f"view_employer_{user_data['telegram_id']}",
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


async def view_employer_profile(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    topic_id=GROUP_TOPIC_New_Employer_Registration_ID,
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
            f"<b>Employer</b>\n\n"
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


async def notify_group_on_creation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_data,
    topic_id=GROUP_TOPIC_New_Company_Created_ID,
):
    view_keyboard = [
        [InlineKeyboardButton("View Company", callback_data=f"view_company_")]
    ]
    message = (
        f"\n🎉 <b>New Company Created!</b>\n\n"
        f"<b>Company Name</b>: {context.user_data["name"]}\n\n"
        f"<b>Type</b>: {user_data["startup_type"].capitalize() + ' Startup' if user_data["company_type"] == 'startup' else user_data["company_type"].capitalize()}\n\n"
    )

    await context.bot.send_message(
        chat_id=os.getenv("HULUMJOBS_GROUP_ID"),
        text=message,
        reply_markup=InlineKeyboardMarkup(view_keyboard),
        parse_mode="HTML",
        message_thread_id=topic_id,
    )
    return


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
    print("capturing group topics...")
    print(f"\n update.message: {update.message} \n")
    # if update.message and update.message.is_topic_message:
    #     topic_name = update.message.forum_topic_created.name
    #     thread_id = update.message.message_thread_id
    #     print(f"\n Topic Name: {topic_name}, Thread ID: {thread_id} \n")
    # Save these details in your database or bot memory if needed


# * Conversation handlers
company_creation_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(create_company_start, pattern="create_company")],
    states={
        COMPANY_TYPE: [CallbackQueryHandler(company_type)],
        STARTUP_TYPE: [CallbackQueryHandler(startup_type)],
        COMPANY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, company_name)],
        TRADE_LICENSE: [
            MessageHandler(filters.PHOTO, trade_license),
            MessageHandler(filters.ALL & ~filters.PHOTO, unsupported_trade_license),
        ],
        EMPLOYER_TYPE: [CallbackQueryHandler(employer_type)],
        EMPLOYER_PHOTO: [
            MessageHandler(filters.PHOTO, employer_photo),
            MessageHandler(filters.ALL & ~filters.PHOTO, unsupported_employer_photo),
        ],
        COMPANY_AUTH_LETTER: [
            MessageHandler(filters.Document.ALL, company_auth_letter),
            MessageHandler(
                filters.ALL & ~filters.Document.ALL, unsupported_auth_letter
            ),
        ],
        CONFIRM_COMPANY: [
            CallbackQueryHandler(confirm_company, pattern="confirm_company"),
            CallbackQueryHandler(cancel_company, pattern="cancel_company"),
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel_company_creation)],
)


post_job_handler = ConversationHandler(
    entry_points=[
        MessageHandler(filters.TEXT & filters.Regex("^Post a Job$"), post_job_start)
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
        SKILLS_EXPERTISE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, skills_expertise),
            CallbackQueryHandler(skills_expertise),
        ],
        CONFIRM_JOB: [
            CallbackQueryHandler(confirm_job, pattern="confirm_job"),
            CallbackQueryHandler(cancel_job, pattern="cancel_job"),
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel_job)],
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
    app = ApplicationBuilder().token(os.getenv("EMPLOYER_BOT_TOKEN")).build()

    # * For DEBUG purposes ONLY
    # app.add_handler(MessageHandler(filters.ALL, capture_group_topics))

    # Callback Query Handlers
    app.add_handler(
        CallbackQueryHandler(view_applicants, pattern="^view_applicants_.*")
    )
    app.add_handler(CallbackQueryHandler(next_applicant, pattern="^applicant_.*"))
    app.add_handler(CallbackQueryHandler(next_mycompany, pattern="^mycompany_.*"))
    app.add_handler(CallbackQueryHandler(next_myjob, pattern="^myjob_.*"))

    app.add_handler(CallbackQueryHandler(my_job_posts, pattern="^my_job_posts$"))
    app.add_handler(CallbackQueryHandler(my_profile, pattern="^my_profile$"))
    app.add_handler(CallbackQueryHandler(edit_profile, pattern="^edit_profile$"))
    app.add_handler(CallbackQueryHandler(done_profile, pattern="^done_profile$"))
    app.add_handler(CallbackQueryHandler(update_username, pattern="^update_username$"))
    app.add_handler(
        CallbackQueryHandler(view_employer_profile, pattern="^view_employer_.*")
    )

    app.add_handler(post_job_handler)
    app.add_handler(company_creation_handler)
    app.add_handler(profile_handler)
    app.add_handler(onboarding_handler)

    # main menu handler (general)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu))

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("cancel", cancel))
    # app.add_handler(CommandHandler("post_a_job", post_a_job))
    app.add_handler(CommandHandler("my_job_posts", my_job_posts))
    app.add_handler(CommandHandler("my_profile", my_profile))
    app.add_handler(CommandHandler("my_companies", my_companies))

    print("Bot is running...")
    app.run_polling(timeout=60)


if __name__ == "__main__":
    main()
