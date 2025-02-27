import os
import logging
from telegram import Update
from telegram.ext import (
    CommandHandler,
    ApplicationBuilder,
    CallbackQueryHandler,
    filters,
    MessageHandler,
    ContextTypes,
)
from telegram.error import TelegramError

from employers.handlers.general import cancel_command, help_command, start_command
from employers.handlers.company import (
    my_companies,
    next_mycompany,
    company_creation_handler,
)
from employers.handlers.onboarding import onboarding_handler
from employers.handlers.job import (
    my_job_posts,
    next_myjob,
    view_applicants,
    next_applicant,
    post_job_handler,
)
from employers.handlers.profile import (
    employer_profile,
    done_profile,
    edit_profile,
    update_username,
    profile_handler,
)
from utils.helpers import view_employer_profile


# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,  # level=logging.INFO | logging.DEBUG
)
logging.getLogger("httpx").setLevel(
    logging.WARNING
)  # avoid all GET and POST requests from being logged
logger = logging.getLogger(__name__)


async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    choice = choice.lower()

    # * "post a job" is handled by another
    if choice == "my job posts":
        await my_job_posts(update, context)
    elif choice == "my companies":
        await my_companies(update, context)
    elif choice == "notifications":
        await update.message.reply_text("Notifications")
    elif choice == "my profile":
        await employer_profile(update, context)
    elif choice == "help":
        await help_command(update, context)
    else:
        await update.message.reply_text("Please use the buttons below to navigate.")


def main():
    token = os.getenv("EMPLOYER_BOT_TOKEN")
    if not token:
        logger.error("EMPLOYER_BOT_TOKEN environment variable is not set.")
        raise ValueError("EMPLOYER_BOT_TOKEN environment variable is not set.")

    app = ApplicationBuilder().token(token).build()

    # * For DEBUG purposes ONLY
    # app.add_handler(MessageHandler(filters.ALL, capture_group_topics))

    # Callback Query Handlers
    app.add_handler(CallbackQueryHandler(next_mycompany, pattern="^mycompany_.*"))

    app.add_handler(CallbackQueryHandler(my_job_posts, pattern="^my_job_posts$"))
    app.add_handler(CallbackQueryHandler(next_myjob, pattern="^myjob_.*"))

    app.add_handler(
        CallbackQueryHandler(view_applicants, pattern="^view_applicants_.*")
    )
    app.add_handler(CallbackQueryHandler(next_applicant, pattern="^applicant_.*"))

    app.add_handler(
        CallbackQueryHandler(employer_profile, pattern="^employer_profile$")
    )
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

    # * command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    app.add_handler(CommandHandler("my_job_posts", my_job_posts))
    app.add_handler(CommandHandler("my_profile", employer_profile))
    app.add_handler(CommandHandler("my_companies", my_companies))

    logger.info("Employer Bot running...")

    try:
        app.run_polling(timeout=60)
    except TimeoutError as e:
        logger.error("Timeout error occurred: %s", e)
    except ConnectionError as e:
        logger.error("Connection error occurred: %s", e)
    except TelegramError as e:
        logger.error("Telegram error occurred: %s", e)
    except Exception as e:
        logger.error("A general error occurred: %s", e)


if __name__ == "__main__":
    main()
