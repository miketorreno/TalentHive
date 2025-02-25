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
    COMPANY_TYPE,
    STARTUP_TYPE,
    COMPANY_NAME,
    TRADE_LICENSE,
    EMPLOYER_TYPE,
    EMPLOYER_PHOTO,
    COMPANY_AUTH_LETTER,
    CONFIRM_COMPANY,
)

from utils.db import execute_query
from utils.constants import (
    CURRENT_COMPANY_INDEX,
    TOTAL_COMPANIES,
)

from utils.helpers import get_companies, get_employer


async def my_companies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    employer = get_employer(update, context)

    if not employer:
        await start_command(update, context)
        return

    companies = get_companies(employer["user_id"])

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
    # global CURRENT_COMPANY_INDEX
    company = company_list[CURRENT_COMPANY_INDEX]
    global TOTAL_COMPANIES
    TOTAL_COMPANIES = len(company_list)
    # CURRENT_COMPANY_INDEX = 0  # Reset index when starting

    company_details = (
        f"Name: <b>\t{company["name"]}{' \t✅' if company["verified"] else ''}</b> \n\n"
        f"Description: <b>\t{company["description"]}</b> \n\n"
        f"Approval status: <b>\t{company["status"]}</b> \n\n"
        # f"Verified: <b>\t{company["verified"]}</b> \n\n"
    )

    keyboard = []
    if TOTAL_COMPANIES > 1:
        if CURRENT_COMPANY_INDEX > 0:
            keyboard = [
                [InlineKeyboardButton("Add Company", callback_data="create_company")],
                [
                    InlineKeyboardButton(
                        "Previous", callback_data="mycompany_previous"
                    ),
                    InlineKeyboardButton("Next", callback_data="mycompany_next"),
                ],
            ]
            if TOTAL_COMPANIES == CURRENT_COMPANY_INDEX + 1:
                keyboard = [
                    [
                        InlineKeyboardButton(
                            "Add Company", callback_data="create_company"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "Previous", callback_data="mycompany_previous"
                        ),
                    ],
                ]
        else:
            keyboard = [
                [InlineKeyboardButton("Add Company", callback_data="create_company")],
                [InlineKeyboardButton("Next", callback_data="mycompany_next")],
            ]
    else:
        keyboard = [
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
    global CURRENT_COMPANY_INDEX
    query = update.callback_query
    await query.answer()  # Acknowledge the callback

    if query.data == "mycompany_next":
        CURRENT_COMPANY_INDEX += 1
    elif query.data == "mycompany_previous":
        CURRENT_COMPANY_INDEX -= 1

    await my_companies(update, context)


async def create_company_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Initiates the company creation process by presenting the user with a choice between
    creating a company or a startup.

    Args:
        update (Update): The update object containing information about the user's interaction.
        context (ContextTypes.DEFAULT_TYPE): The context object containing data related to the
            conversation.

    Returns:
        COMPANY_TYPE: The next state in the conversation if the user selects a company type.
    """

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
    """
    Handles the callback query to select a company type and prompts the user to enter the
    name of the company or select the type of startup.

    Args:
        update (Update): The update object containing information about the user's interaction.
        context (ContextTypes.DEFAULT_TYPE): The context object containing data related to the
            conversation.

    Returns:
        COMPANY_NAME: The next state in the conversation if the user selects a company type.
        STARTUP_TYPE: The next state in the conversation if the user selects a startup type.
        ConversationHandler.END: If an exception occurs during processing.
    """

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

        if query.data == "startup":
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

        await query.edit_message_text(
            "An error occurred with your company type. Please try again."
        )
        # Optionally log the error for debugging
        print("Error in company_photo: There's a third company type")
        return ConversationHandler.END
    except Exception as e:
        await query.edit_message_text(
            "An error occurred while saving your company type. Please try again."
        )
        # Optionally log the error for debugging
        print(f"Error in company_type: {e}")
        return ConversationHandler.END


async def startup_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the callback query to select a startup type and prompts the user to enter the
    name of the company.

    Args:
        update (Update): The update object containing information about the user's interaction.
        context (ContextTypes.DEFAULT_TYPE): The context object containing data related to the
            conversation.

    Returns:
        COMPANY_NAME: The next state in the conversation if the user selects a startup type.
        ConversationHandler.END: If an exception occurs during processing.
    """

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
    """
    Processes the user's input to set the company name and guides the user
    through the subsequent steps based on the company type.

    This function validates the company name provided by the user, ensuring
    it contains only alphanumeric characters. It updates the user's context
    data with the validated name. Depending on the company type or startup
    type, it prompts the user to either upload a trade license or select
    their role as a founder or recruiter.

    Args:
        update (Update): The update object containing the user's message.
        context (ContextTypes.DEFAULT_TYPE): The context object containing the conversation state
            and user data.

    Returns:
        TRADE_LICENSE: If the user is prompted to upload a trade license.
        EMPLOYER_TYPE: If the user is prompted to select their role.
        COMPANY_NAME: If the name validation fails.
        ConversationHandler.END: If an exception occurs or an error is encountered.
    """

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
            print("Error in company_name: There's a third company type")
            return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(
            "An error occurred while saving your company name. Please try again."
        )
        # Optionally log the error for debugging
        print(f"Error in company_name: {e}")
        return ConversationHandler.END


async def trade_license(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the upload of a trade license photo by the user.

    This function checks if the user has sent a photo as a trade license.
    If a photo is not provided, it prompts the user to upload a valid trade
    license. Upon successful photo upload, it stores the file ID in the user's
    context data and prompts the user to select their role as either a general
    manager or recruiter.

    Args:
        update (Update): The update object containing the user's message.
        context (ContextTypes.DEFAULT_TYPE): The context object containing the
            conversation state and user data.

    Returns:
        TRADE_LICENSE: If the user is prompted again to upload a trade license.
        EMPLOYER_TYPE: If the user is prompted to select a role.
        ConversationHandler.END: If an exception occurs during processing.
    """

    try:
        if not update.message.photo:
            await update.message.reply_text(
                "<i>* Invalid format.</i>\n\n<b>Please upload your trade license</b>",
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
    """
    Handles unsupported file uploads for the trade license by notifying the user of an invalid file type.

    This function is triggered when a user uploads a file that is not a photo as a trade license.
    It sends a message to the user indicating the invalid file type and prompts them to upload
    a photo instead.

    Args:
        update (Update): The update object containing the user's message.
        context (ContextTypes.DEFAULT_TYPE): The context object containing the conversation state
            and user data.

    Returns:
        TRADE_LICENSE: The next state of the conversation, prompting the user to upload a photo.
        ConversationHandler.END: If an exception occurs during processing.
    """

    try:
        await update.message.reply_text(
            "<i>* Invalid file type</i>\n\n<b>Please upload a PHOTO</b>",
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
    """
    Handles the callback query to select an employer type and prompts the user to upload a photo of their ID.

    This function extracts the employer type from the callback data, stores it in the user's context data,
    and sends a message to the user to upload a photo of their ID.

    Args:
        update (Update): The update object containing information about the user's interaction.
        context (ContextTypes.DEFAULT_TYPE): The context object containing data related to the conversation.

    Returns:
        EMPLOYER_PHOTO: The next state of the conversation, prompting the user to upload their ID photo.
        ConversationHandler.END: If an exception occurs during processing.
    """

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
    """
    Handles the upload of the employer's ID photo and prompts the user to confirm
    the company details or upload an authorization letter if the employer type is recruiter.

    This function checks if the user has sent a photo of their ID.
    If a photo is not provided, it prompts the user to upload a valid ID photo.
    Upon successful photo upload, it stores the file ID in the user's context data.
    It then checks the employer type and prompts the user to either confirm the company
    details or upload an authorization letter.

    Args:
        update (Update): The update object containing the user's message.
        context (ContextTypes.DEFAULT_TYPE): The context object containing the conversation state
            and user data.

    Returns:
        CONFIRM_COMPANY: If the employer type is a general manager or founder and the user is prompted
            to confirm the company details.
        COMPANY_AUTH_LETTER: If the employer type is a recruiter and the user is prompted to upload
            an authorization letter.
        ConversationHandler.END: If an exception occurs during processing.
    """

    try:
        if not update.message.photo:
            await update.message.reply_text(
                "<i>* Invalid format.</i>\n\n<b>Please upload your ID photo</b>",
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
        company__type = context.user_data["company_type"]
        startup__type = (
            context.user_data["startup_type"] if company__type != "company" else ""
        )
        company_details = (
            f"<b>COMPANY INFO</b>\n\n"
            f"Company Name: {context.user_data["name"]}\n\n"
            # f"Company Type: {context.user_data["company_type"]}\n\n"
            f"{'Type: ' + startup__type.capitalize() + ' Startup \n\n' if company__type == 'startup' else ''}"
            f"{'Trade License Photo: \t✅ \n\n' if startup__type != 'unlicensed' else ''}"
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

        if context.user_data["employer_type"] == "recruiter":
            await update.message.reply_text(
                "<b>Please upload recruiter authorization letter</b>", parse_mode="HTML"
            )
            return COMPANY_AUTH_LETTER

        await update.message.reply_text(
            "An error occurred while uploading your photo. Please try again."
        )
        print("Error in employer_photo: There's a fourth employer type")
        return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(
            "An error occurred while uploading your photo. Please try again."
        )
        print(f"Error in employer_photo: {e}")
        return ConversationHandler.END


async def unsupported_employer_photo(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """
    Handles invalid file types sent by the user during the employer photo upload step.

    This function sends a message to the user, prompting them to upload a valid photo.
    If an exception occurs, it sends an error message to the user and logs the error
    for debugging purposes.

    Args:
        update (Update): The update object containing the user's message.
        context (ContextTypes.DEFAULT_TYPE): The context object containing the
            conversation state and user data.

    Returns:
        EMPLOYER_PHOTO: The next state of the conversation, prompting the user to upload
            their ID photo again.
        ConversationHandler.END: If an exception occurs during processing.
    """

    try:
        await update.message.reply_text(
            "<i>* Invalid file type</i>\n\n<b>Please upload a PHOTO</b>",
            parse_mode="HTML",
        )
        return EMPLOYER_PHOTO
    except Exception as e:
        await update.message.reply_text(
            "An error occurred with your photo. Please try again."
        )
        print(f"Error in unsupported_employer_photo: {e}")
        return ConversationHandler.END


async def company_auth_letter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the upload of a recruiter authorization letter by the user.

    This function checks if the user has sent a valid document as a recruiter authorization letter.
    If a valid document is not provided, it prompts the user to upload a valid document.
    Upon successful document upload, it stores the file ID in the user's context data and prompts
    the user to confirm or cancel their company registration.

    Args:
        update (Update): The update object containing the user's message.
        context (ContextTypes.DEFAULT_TYPE): The context object containing the conversation state
            and user data.

    Returns:
        CONFIRM_COMPANY: If the user is prompted to confirm or cancel their company registration.
        COMPANY_AUTH_LETTER: If the user is prompted again to upload a valid document.
        ConversationHandler.END: If an exception occurs during processing.
    """

    try:
        if update.message.document:
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
            company__type = context.user_data["company_type"]
            startup__type = (
                context.user_data["startup_type"] if company__type != "company" else ""
            )
            auth_letter = context.user_data["auth_letter"]
            company_details = (
                f"<b>COMPANY INFO</b>\n\n"
                f"Company Name: {context.user_data["name"]}\n\n"
                # f"Company Type: {context.user_data["company_type"]}\n\n"
                f"{'Type: ' + startup__type.capitalize() + ' Startup \n\n' if company__type == 'startup' else ''}"
                f"{'Trade License Photo: \t✅ \n\n' if startup__type != 'unlicensed' else ''}"
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
    """
    Handles an unsupported file type during authorization letter upload and prompts the user
    to upload a valid document.

    Args:
        update (Update): The update object containing information about the user's interaction.
        context (ContextTypes.DEFAULT_TYPE): The context object containing the conversation state
            and user data.

    Returns:
        COMPANY_AUTH_LETTER: If an invalid document is uploaded.
        ConversationHandler.END: If an exception occurs during processing.
    """

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
    """
    Confirms the creation of a company by inserting company details into the database.

    This function handles the callback query to confirm the company's creation. It retrieves
    the employer's information and company details from the user's context data and inserts
    this information into the database. If the employer is not found, it starts the registration
    process. Upon successful insertion, it sends a confirmation message to the user.

    Args:
        update (Update): The update object containing the callback query.
        context (ContextTypes.DEFAULT_TYPE): The context object containing conversation
            state and user data.

    Returns:
        ConversationHandler.END: Ends the conversation after processing the confirmation.

    Raises:
        Exception: If an error occurs during the database insertion or message update.
    """

    try:
        query = update.callback_query
        await query.answer()
        data = context.user_data

        employer = get_employer(update, context)

        if not employer:
            await start_command(update, context)
            return

        response = execute_query(
            "INSERT INTO companies (user_id, type, startup_type, name, trade_license, employer_photo, created_by) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (
                employer["user_id"],
                data["company_type"],
                data["startup_type"],
                data["name"],
                data["trade_license"],
                data["employer_photo"],
                data["employer_type"],
            ),
        )

        # Notify the group about the new company creation
        # await notify_group_on_creation(update, context, data)

        await query.edit_message_text(
            "<b>Company created successfully!</b>", parse_mode="HTML"
        )
        return ConversationHandler.END
    except Exception as e:
        await query.edit_message_text(
            "An error occurred while saving your company details. Please try again."
        )
        print(f"Error in confirm_company: {e}")
        return ConversationHandler.END


async def cancel_company_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Cancels the company creation process.

    This function handles a callback query to cancel the company creation process.
    It sends a confirmation message to the user and ends the conversation.

    Args:
        update (Update): The update object containing the callback query.
        context (ContextTypes.DEFAULT_TYPE): The context object containing the
            conversation state and user data.

    Returns:
        ConversationHandler.END: Ends the conversation after processing the cancellation.
    """

    if update.callback_query:
        await update.callback_query.edit_message_text(
            "<b>Company creation canceled</b>", parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            "<b>Company creation canceled</b>", parse_mode="HTML"
        )
    return ConversationHandler.END


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
            CallbackQueryHandler(cancel_company_creation, pattern="cancel_company"),
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel_company_creation)],
)
