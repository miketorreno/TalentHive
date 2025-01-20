import os
import re
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
REGISTER, REGISTER_NAME, REGISTER_FIRSTNAME, REGISTER_LASTNAME, REGISTER_EMAIL, REGISTER_PHONE, REGISTER_GENDER, REGISTER_DOB, REGISTER_COUNTRY, REGISTER_CITY, CONFIRMATION, COMPANY_TYPE, STARTUP_TYPE, COMPANY_NAME, TRADE_LICENSE, EMPLOYER_TYPE, EMPLOYER_PHOTO, COMPANY_AUTH_LETTER, CONFIRM_COMPANY, CHOOSE_ACTION, SELECT_COMPANY, SELECT_CATEGORY, SELECT_TYPE, TITLE, DESCRIPTION, REQUIREMENTS, CITY, COUNTRY, SALARY, DEADLINE, CONFIRM_JOB = range(31)

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

GROUP_TOPIC_New_Company_Created_ID = 67
GROUP_TOPIC_New_Employer_Registration_ID = 17


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
        keyboard = [
            ["Post a Job", "My Job Posts"],
            ["My Companies", "Notifications"],
            ["My Profile", "Help"]
        ]
        await update.message.reply_text(
            text=f"<b>Hello {(user[3].split()[0]).capitalize()} 👋\t Welcome to HulumJobs!</b> \n\n"
                "<b>🔊 \tPost a Job</b>:\t find the right candidates for you \n\n"
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
        "Hope we can talk again soon."
    )
    return ConversationHandler.END


async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    choice = choice.lower()

    # ? "post a job" is handled by another
    # if choice == "post a job":
        # await update.message.reply_text("Post a job")
        # await post_a_job(update, context)
    if choice == "my job posts":
        await my_jobs(update, context)
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



# Posting a job
def fetch_companies(user_id):
    cur = conn.cursor()
    cur.execute("SELECT company_id, name FROM companies WHERE user_id = %s", (user_id,))
    companies = cur.fetchall()
    return companies


def fetch_categories():
    cur = conn.cursor()
    cur.execute("SELECT category_id, name FROM categories")
    categories = cur.fetchall()
    return categories


# Create company conversation
async def create_company_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        await query.message.reply_text("Let's create your company profile.")
        
        keyboard = [
            [
                InlineKeyboardButton("Company", callback_data='company'), 
                InlineKeyboardButton("Startup", callback_data='startup')
            ]
        ]
    
        await query.message.reply_text(
            "Please select the type of your company",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        return COMPANY_TYPE
    except Exception as e:
        await update.effective_message.reply_text(
            "An error occurred creating your company. Please try again."
        )
        # Optionally log the error for debugging
        print(f"Error in create_company_start: {e}")
        return ConversationHandler.END


async def company_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        
        context.user_data['company_type'] = query.data
        if query.data == 'company':
            context.user_data['startup_type'] = None
            await query.message.reply_text(
                "Please enter the name of your company",
                parse_mode='HTML'
            )
            return COMPANY_NAME
        elif query.data == 'startup':
            keyboard = [
                [
                    InlineKeyboardButton("Licensed", callback_data='licensed'), 
                    InlineKeyboardButton("Unlicensed", callback_data='unlicensed')
                ]
            ]
            await query.message.reply_text(
                "Please select the type of your startup",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
            return STARTUP_TYPE
        else:
            await update.message.reply_text(
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
        
        context.user_data['startup_type'] = query.data
        await query.message.reply_text(
            "Please enter the name of your company",
            parse_mode='HTML'
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
                "<i>* Company name should only contain alphabets and numbers.</i>\n\nPlease enter the name your company",
                parse_mode='HTML'
            )
            return COMPANY_NAME
        
        context.user_data['name'] = name
        if context.user_data['company_type'] == 'company' or context.user_data['startup_type'] == 'licensed':
            await update.message.reply_text(
                "Please upload your trade license \n\n<i>* you can upload pdf or photo</i>",
                parse_mode='HTML'
            )
            return TRADE_LICENSE
        elif context.user_data['startup_type'] == 'unlicensed':
            context.user_data["trade_license"] = None
            keyboard = [
                [
                    InlineKeyboardButton("Founder", callback_data='founder'), 
                    InlineKeyboardButton("Recruiter", callback_data='recruiter')
                ]
            ]
        
            await update.message.reply_text(
                "Are you the founder or recruiter?",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
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
                "<i>* Invalid format.</i>\n\nPlease upload your trade license",
                parse_mode='HTML'
            )
            return TRADE_LICENSE
        
        context.user_data["trade_license"] = update.message.photo[-1].file_id
        keyboard = [
            [
                InlineKeyboardButton("General Manager", callback_data='general_manager'), 
                InlineKeyboardButton("Recruiter", callback_data='recruiter')
            ]
        ]
    
        await update.message.reply_text(
            "Are you the general manager or recruiter?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
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
            "<i>* Invalid file type</i>\n\nPlease upload a PHOTO",
            parse_mode='HTML'
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
        
        context.user_data['employer_type'] = query.data
        await query.message.reply_text(
            "Please upload your ID photo",
            parse_mode='HTML'
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
                "<i>* Invalid format.</i>\n\nPlease upload your ID photo",
                parse_mode='HTML'
            )
            return EMPLOYER_PHOTO
        
        context.user_data["employer_photo"] = update.message.photo[-1].file_id
        keyboard = [
            [
                InlineKeyboardButton("Confirm", callback_data='confirm_company'),
                InlineKeyboardButton("Cancel", callback_data='cancel_company')
            ]
        ]
        company_type = context.user_data['company_type']
        startup_type = context.user_data['startup_type'] if company_type != 'company' else ''
        company_details = (
            f"<b>COMPANY INFO</b>\n\n"
            f"Company Name: {context.user_data["name"]}\n\n"
            # f"Company Type: {context.user_data["company_type"]}\n\n"
            f"{'Type: ' + startup_type.capitalize() + 'Startup \n\n' if company_type == 'startup' else ''}"
            f"{'Trade License Photo: \t✅ \n\n' if startup_type != 'unlicensed' else ''}"
            f"Employer Photo: \t✅\n\n"
        )
        if context.user_data['employer_type'] == 'general_manager' or context.user_data['employer_type'] == 'founder':
            await update.message.reply_text(
                text=company_details,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
            return CONFIRM_COMPANY
        # elif context.user_data['employer_type'] == 'founder':
        #     await update.message.reply_text(
        #         text=company_details,
        #         reply_markup=InlineKeyboardMarkup(keyboard),
        #         parse_mode='HTML'
        #     )
        #     return CONFIRM_COMPANY
        elif context.user_data['employer_type'] == 'recruiter':
            await update.message.reply_text(
                "<b>Please upload recruiter authorization letter</b>",
                parse_mode='HTML'
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


async def unsupported_employer_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text(
            "<i>* Invalid file type</i>\n\nPlease upload a PHOTO",
            parse_mode='HTML'
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
    if update.message.document:
        # Validate the file type
        file_name = update.message.document.file_name
        if not file_name.endswith(('.pdf', '.doc', '.docx')):
            await update.message.reply_text(
                "Invalid file type. Please upload a PDF or Word document.",
                parse_mode='HTML'
            )
            return COMPANY_AUTH_LETTER

        # Save the file ID
        context.user_data['auth_letter'] = update.message.document.file_id
        keyboard = [
            [
                InlineKeyboardButton("Confirm", callback_data='confirm_company'),
                InlineKeyboardButton("Cancel", callback_data='cancel_company')
            ]
        ]
        company_type = context.user_data['company_type']
        startup_type = context.user_data['startup_type'] if company_type != 'company' else ''
        auth_letter = context.user_data['auth_letter']
        company_details = (
            f"<b>COMPANY INFO</b>\n\n"
            f"Company Name: {context.user_data["name"]}\n\n"
            # f"Company Type: {context.user_data["company_type"]}\n\n"
            f"{'Type: ' + startup_type.capitalize() + 'Startup \n\n' if company_type == 'startup' else ''}"
            f"{'Trade License Photo: \t✅ \n\n' if startup_type != 'unlicensed' else ''}"
            f"Employer Photo: \t✅\n\n"
            f"{'Authorization Letter: \t✅' if auth_letter else ''}\n\n"
        )
        await update.message.reply_text(
            text=company_details,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        return CONFIRM_COMPANY
    else:
        await update.message.reply_text("Please upload a valid document.")
        return COMPANY_AUTH_LETTER


async def unsupported_auth_letter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text(
            "<i>* Invalid file type</i>\n\nPlease upload a PDF or Word document",
            parse_mode='HTML'
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
    query = update.callback_query
    await query.answer()
    user = get_user(update, context)
    data = context.user_data
    
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO companies (user_id, type, startup, name, trade_license, employer_photo, created_by) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (user[0], data["company_type"], data["startup_type"], data["name"], data["trade_license"], data["employer_photo"], data["employer_type"]),
    )
    conn.commit()
    
    # Notify the group about the new company creation
    await notify_group_on_creation(update, context, data)

    await query.edit_message_text("Company created successfully!")
    return ConversationHandler.END


async def cancel_company(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        query = update.callback_query
        await query.edit_message_text("Company creation canceled.")
    else:
        await update.message.reply_text("Company creation canceled.")

    return ConversationHandler.END


async def cancel_company_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.edit_message_text("Company creation canceled.")
    else:
        await update.message.reply_text("Company creation canceled.")
    return ConversationHandler.END



# Post job conversation
async def post_job_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Let's post a new job.")
    user = get_user(update, context)
    
    # companies = fetch_companies(update.effective_user.id)
    cur = conn.cursor()
    cur.execute("SELECT * FROM companies WHERE user_id = %s", (user[0],))
    companies = cur.fetchall()
    
    if not companies:
        await update.message.reply_text("No companies found. Please register a company first.")
        return ConversationHandler.END

    buttons = [[InlineKeyboardButton(company[4], callback_data=f"company_{company[0]}")] for company in companies]
    await update.message.reply_text(
        "Please select company:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    return SELECT_COMPANY


async def select_company(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not query.data.startswith("company_"):
        await query.message.reply_text("Invalid selection.")
        return SELECT_COMPANY

    company_id = query.data.split("_")[1]
    context.user_data["company_id"] = company_id
    await query.message.reply_text("Company selected. Please select a job category")
    categories = fetch_categories()
    buttons = [[InlineKeyboardButton(name, callback_data=f"category_{category_id}")] for category_id, name in categories]
    await query.message.reply_text(
        "Choose a job category:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    return SELECT_CATEGORY


async def select_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [
            InlineKeyboardButton("On-site - Full-time", callback_data="On-site - Full-time"),
            InlineKeyboardButton("On-site - Part-time", callback_data="On-site - Part-time"),
        ],
        [
            InlineKeyboardButton("On-site - Contractual", callback_data="On-site - Contractual"),
            InlineKeyboardButton("On-site - Freelance", callback_data="On-site - Freelance"),
        ],
        [
            InlineKeyboardButton("On-site - Intern (Paid)", callback_data="On-site - Intern (Paid)"),
            InlineKeyboardButton("On-site - Intern (UnPaid)", callback_data="On-site - Intern (UnPaid)"),
        ],
        [
            InlineKeyboardButton("Remote - Full-time", callback_data="Remote - Full-time"),
            InlineKeyboardButton("Remote - Part-time", callback_data="Remote - Part-time"),
        ],
        [
            InlineKeyboardButton("Remote - Contractual", callback_data="Remote - Contractual"),
            InlineKeyboardButton("Remote - Freelance", callback_data="Remote - Freelance"),
        ],
        [
            InlineKeyboardButton("Remote - Intern (Paid)", callback_data="Remote - Intern (Paid)"),
            InlineKeyboardButton("Remote - Intern (UnPaid)", callback_data="Remote - Intern (Unpaid)"),
        ],
    ]

    if not query.data.startswith("category_"):
        await query.message.reply_text("Invalid selection.")
        return SELECT_CATEGORY
    
    category_id = query.data.split("_")[1]
    context.user_data["category_id"] = category_id

    await query.message.reply_text("Category selected. Please select job type")
    await query.message.reply_text(
        "Choose a job type:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return SELECT_TYPE

    # await query.message.reply_text("Category selected. Please enter the job title")
    # return TITLE


async def select_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # if not query.data.startswith("type_"):
    #     await query.message.reply_text("Invalid selection.")
    #     return SELECT_TYPE

    # type = query.data.split("_")[1]
    context.user_data["type"] = query.data
    await query.message.reply_text("Category selected. Please enter the job title")
    return TITLE


async def collect_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["title"] = update.message.text.strip()
    await update.message.reply_text("Please enter the job description")
    return DESCRIPTION


async def collect_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = update.message.text.strip()
    await update.message.reply_text("What are the job requirements?")
    return REQUIREMENTS


async def collect_requirements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["requirements"] = update.message.text.strip()
    await update.message.reply_text("Which city is the job located in?")
    return CITY


async def collect_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["city"] = update.message.text.strip()
    await update.message.reply_text("Which country is the job located in?")
    return COUNTRY


async def collect_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["country"] = update.message.text.strip()
    await update.message.reply_text("What is the salary for this job?")
    return SALARY


async def collect_salary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    salary = update.message.text.strip()
    if not salary.isdigit():
        await update.message.reply_text("Invalid salary. Please enter a numeric value.")
        return SALARY
    context.user_data["salary"] = salary
    await update.message.reply_text("Finally, enter the application deadline (YYYY-MM-DD)")
    return DEADLINE


async def collect_deadline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["deadline"] = update.message.text.strip()
    keyboard = [
        [InlineKeyboardButton("Confirm", callback_data='confirm_job')],
        [InlineKeyboardButton("Cancel", callback_data='cancel_job')],
    ]
    
    try:
        job = context.user_data
        
        job_details = f"\nJob Title: <b>\t{job['title']}</b> \n\nJob Type: <b>\t</b> \n\nWork Location: <b>\t{job['city']}, {job['country']}</b> \n\nSalary: <b>\t{job['salary']}</b> \n\nDeadline: <b>\t{format_date_for_db(job['deadline'])}</b> \n\n<b>Description</b>: \t{job['description']} \n\n<b>Requirements</b>: \t{job['requirements']} \n\n"
        
        # message = (
        #     "Please confirm the job details: \n\n"
        #     f"Title: {user_data['title']} \n\n"
        #     f"Description: {user_data['description']} \n\n"
        #     f"Requirements: {user_data['requirements']} \n\n"
        #     f"City: {user_data['city']} \n\n"
        #     f"Country: {user_data['country']} \n\n"
        #     f"Salary: {user_data['salary']} \n\n"
        #     f"Deadline: {user_data['deadline']} \n\n"
        #     "Post job?"
        # )
        await update.message.reply_text(
            job_details, 
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        return CONFIRM_JOB
    except ValueError:
        await update.message.reply_text("Invalid date format. Please use YYYY-MM-DD.")
        return DEADLINE


async def confirm_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = get_user(update, context)
    
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO jobs (company_id, user_id, category_id, type, title, description, requirements, city, country, salary, deadline)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING job_id
        """,
        (
            context.user_data["company_id"],
            user[0],
            context.user_data["category_id"],
            context.user_data["type"],
            context.user_data["title"],
            context.user_data["description"],
            context.user_data["requirements"],
            context.user_data["city"],
            context.user_data["country"],
            context.user_data["salary"],
            context.user_data["deadline"],
        ),
    )
    job_id = cur.fetchone()[0]
    conn.commit()
    
    cur = conn.cursor()
    cur.execute("SELECT j.*, c.* FROM jobs j JOIN companies c ON j.company_id = c.company_id WHERE job_id = %s", (job_id,))
    job = cur.fetchone()
    
    job_message = f"\nJob Title: <b>\t{job[5]}</b> \n\nJob Type: <b>\t{job[4]}</b> \n\nWork Location: <b>\t{job[8]}, {job[9]}</b> \n\nSalary: <b>\t{job[10]}</b> \n\nDeadline: <b>\t{format_date(job[11])}</b> \n\n<b>Description</b>: \n{job[6]} \n\n<b>Requirements</b>: \n{job[7]} \n\n<b>__________________</b>\n\n<b>{job[19]}</b> \n\n"

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
        text=job_message, 
        reply_markup=reply_markup, 
        parse_mode="HTML"
    )

    await query.edit_message_text("Job posted successfully and shared to the channel!")
    
    # await query.edit_message_text("Job posted successfully!")
    return ConversationHandler.END


async def cancel_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.edit_message_text("Job posting canceled.")
    else:
        await update.message.reply_text("Job posting canceled.")
    return ConversationHandler.END


async def my_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all jobs posted by the user."""
    user = get_user(update, context)
    
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


async def my_companies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all companies owned by the user."""
    user = get_user(update, context)
    
    # Fetch companies
    cur = conn.cursor()
    cur.execute("SELECT * FROM companies WHERE user_id = %s", (user[0],))
    companies = cur.fetchall()
    
    keyboard = [
        [InlineKeyboardButton("Add Company", callback_data='create_company')],
    ]

    if not companies:
        await update.message.reply_text(
            "You haven't created any companies yet.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # Format the list of companies
    message = "**Your Companies:** \n\n"
    for company in companies:
        message += f"- **ID:** {company[0]}\n  **Name:** {company[4]}\n  **Description:** {company[7]}\n  **Approval status:** {company[8]}\n\n"

    await update.message.reply_text(
        text=message, 
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


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
            "<b>Post a Job</b> - find the right candidates for you \n\n"
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
    try:
        query = update.callback_query
        await query.answer()
        
        # await query.edit_message_text(text=f"Please enter your first name")
    
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Please enter your first name",
            parse_mode='HTML'
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
            "Please select your country",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return REGISTER_COUNTRY
    except Exception as e:
        await update.message.reply_text("An error occurred while saving your age. Please try again.")
        print(f"Error in register_dob: {e}")
        return ConversationHandler.END


async def register_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        country = query.data
        
        keyboard = get_all_cities()
        context.user_data['country'] = country
        await query.edit_message_text(
            "Please select your city",
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
            user_data['telegram_id'] = update.effective_user.id
            username = update.effective_user.username
            role_id = 2  # Assuming role_id is 2 for the employer role

            try:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO users (telegram_id, role_id, name, username, email, phone, gender, dob, country, city) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (user_data['telegram_id'], role_id, f"{user_data['firstname']} {user_data['lastname']}", username, user_data['email'], user_data['phone'],
                     user_data.get('gender'), user_data.get('dob'), user_data['country'], user_data['city'])
                )
                conn.commit()
                cur.close()
            except Exception as db_error:
                await query.edit_message_text("An error occurred while saving your data to the database. Please try again.")
                print(f"Database error in confirm_registration: {db_error}")
                return ConversationHandler.END

            await query.edit_message_text(
                f"Registered successfully \t 🎉",
                # f"Registered successfully \t 🎉 \n\nWelcome to HulumJobs <b>{user_data['firstname'].capitalize()}</b>!",
                parse_mode='HTML'
            )
            
            # TODO: implement a better way to handle redirect to `start`
            keyboard = [
                ["Post a Job", "My Job Posts"],
                ["My Companies", "Notifications"],
                ["My Profile", "Help"]
            ]
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"<b>Hello {user_data['firstname'].capitalize()} 👋\t Welcome to HulumJobs!</b> \n\n"
                    "<b>🔊 \tPost a Job</b>:\t find the right candidates for you \n\n"
                    "<b>📑 \tMy Job posts</b>:\t view & manage your job posts \n\n"
                    "<b>🏢 \tMy Companies</b>:\t add & manage your companies \n\n"
                    "<b>🔔 \tNotifications</b>:\t customize notifications you wanna receive \n\n"
                    "<b>👤 \tMy Profile</b>:\t manage your profile \n\n"
                    "<b>❓ \tHelp</b>:\t show help message \n\n",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
                parse_mode='HTML'
            )
            
            # Notify the group about the new registration
            await notify_group_on_registration(update, context, user_data)

            # return REGISTER_COMPLETE
            # await update.message.reply_text("/start")
            
        elif query.data == 'restart':
            await query.edit_message_text("Let's start over. Use /start to begin again.")
        return ConversationHandler.END
    except Exception as e:
        await query.edit_message_text("An error occurred during confirmation. Please try again.")
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
    cur.execute("SELECT * FROM users WHERE telegram_id = %s AND role_id = 2", (telegram_id,))
    user = cur.fetchone()
    return user


def get_user_from_telegram_id(update: Update, context: ContextTypes.DEFAULT_TYPE, telegram_id):    
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE telegram_id = %s AND role_id = 2", (telegram_id,))
    user = cur.fetchone()
    return user


def format_date(date):
    return date.strftime("%B %d, %Y")


def format_date_for_db(date):
    return datetime.strptime(date, "%Y-%m-%d")


def is_valid_email(email):
    # regex pattern for validating an email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


async def notify_group_on_registration(update: Update, context: ContextTypes.DEFAULT_TYPE, user_data, topic_id=GROUP_TOPIC_New_Employer_Registration_ID):
    view_keyboard = [
        [InlineKeyboardButton("View Profile", callback_data=f"view_employer_{user_data['telegram_id']}")]
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


async def view_employer_profile(update: Update, context: ContextTypes.DEFAULT_TYPE, topic_id=GROUP_TOPIC_New_Employer_Registration_ID):
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
            parse_mode="HTML"
        )
    
    return


async def notify_group_on_creation(update: Update, context: ContextTypes.DEFAULT_TYPE, user_data, topic_id=GROUP_TOPIC_New_Company_Created_ID):
    view_keyboard = [
        [InlineKeyboardButton("View Company", callback_data=f"view_company_")]
    ]
    message = (
        f"\n🎉 <b>New Company Created!</b>\n\n"
        f"<b>Company Name</b>: {context.user_data["name"]}\n\n"
        f"<b>Type</b>: {user_data["startup_type"].capitalize() + 'Startup' if user_data["company_type"] == 'startup' else user_data["company_type"].capitalize()}\n\n"
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
    buttons = [
        InlineKeyboardButton(city, callback_data=f"{city}") for city in CITIES
    ]

    # Organize buttons into 2-column rows
    keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]  # Group buttons into rows
    keyboard.append([InlineKeyboardButton("Others", callback_data="Others")]),

    return InlineKeyboardMarkup(keyboard)


# * DEBUG (will be extracted to a separate debug.py file)
async def capture_group_topics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("capturing group topics...")
    """
        Capture topics (message_thread_id) from messages in a forum group.
    """
    print(f"\n update.message: {update.message} \n")
    # if update.message and update.message.is_topic_message:
    #     topic_name = update.message.forum_topic_created.name
    #     thread_id = update.message.message_thread_id
    #     print(f"\n Topic Name: {topic_name}, Thread ID: {thread_id} \n")
        # Save these details in your database or bot memory if needed



# Conversation handlers
company_creation_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(create_company_start, pattern='create_company')],
    states={
        COMPANY_TYPE: [CallbackQueryHandler(company_type)],
        STARTUP_TYPE: [CallbackQueryHandler(startup_type)],
        COMPANY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, company_name)],
        TRADE_LICENSE: [
            MessageHandler(filters.PHOTO, trade_license),
            MessageHandler(filters.ALL & ~filters.PHOTO, unsupported_trade_license)
        ],
        EMPLOYER_TYPE: [CallbackQueryHandler(employer_type)],
        EMPLOYER_PHOTO: [
            MessageHandler(filters.PHOTO, employer_photo),
            MessageHandler(filters.ALL & ~filters.PHOTO, unsupported_employer_photo)
        ],
        COMPANY_AUTH_LETTER: [
            MessageHandler(filters.Document.ALL, company_auth_letter),
            MessageHandler(filters.ALL & ~filters.Document.ALL, unsupported_auth_letter)
        ],
        CONFIRM_COMPANY: [
            CallbackQueryHandler(confirm_company, pattern="confirm_company"),
            CallbackQueryHandler(cancel_company, pattern="cancel_company"),
        ]
    },
    fallbacks=[CommandHandler("cancel", cancel_company_creation)],
)



post_job_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.TEXT & filters.Regex("^Post a Job$"), post_job_start)],
    states={
        SELECT_COMPANY: [CallbackQueryHandler(select_company)],
        SELECT_CATEGORY: [CallbackQueryHandler(select_category)],
        SELECT_TYPE: [CallbackQueryHandler(select_type)],
        TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_title)],
        DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_description)],
        REQUIREMENTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_requirements)],
        CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_city)],
        COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_country)],
        SALARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_salary)],
        DEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_deadline)],
        CONFIRM_JOB: [
            CallbackQueryHandler(confirm_job, pattern="confirm_job"),
            CallbackQueryHandler(cancel_job, pattern="cancel_job"),
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel_job)],
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
    app = ApplicationBuilder().token(os.getenv('EMPLOYER_BOT_TOKEN')).build()
    
    # * For DEBUG purposes ONLY
    # app.add_handler(MessageHandler(filters.ALL, capture_group_topics))
    
    # Callback Query Handlers
    app.add_handler(CallbackQueryHandler(view_employer_profile, pattern="^view_employer_.*"))
    
    app.add_handler(post_job_handler)
    app.add_handler(company_creation_handler)
    app.add_handler(onboarding_handler)

    # main menu handler (general)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu))

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('cancel', cancel))
    
    print("Bot is running...")
    app.run_polling(timeout=60)


if __name__ == '__main__':
    main()
