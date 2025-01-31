import os
import logging
from telegram.ext import CommandHandler, ApplicationBuilder

from applicants.handlers.profile import applicant_profile, profile_handler
from applicants.handlers.general import start, cancel, help_command

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,  # level=logging.INFO | logging.DEBUG
)
logging.getLogger("httpx").setLevel(
    logging.WARNING
)  # avoid all GET and POST requests from being logged
logger = logging.getLogger(__name__)

# Constants
CURRENT_JOB_INDEX = 0
TOTAL_JOBS = 0
CURRENT_APPLICATION_INDEX = 0
TOTAL_APPLICATIONS = 0


# async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     choice = update.message.text
#     choice = choice.lower()
#     user = get_user(update, context)

#     if not user:
#         await start(update, context)
#         return

#     if choice == "browse jobs":
#         await browse_jobs(update, context)
#     elif choice == "saved jobs":
#         await saved_jobs(update, context)
#     elif choice == "my profile":
#         await my_profile(update, context)
#     elif choice == "my applications":
#         await my_applications(update, context)
#     elif choice == "job notifications":
#         await job_notifications(update, context)
#     elif choice == "help":
#         await help(update, context)
#     else:
#         await update.message.reply_text("Please use the buttons below to navigate.")


def main() -> None:
    app = ApplicationBuilder().token(os.getenv("APPLICANT_BOT_TOKEN")).build()

    # * For DEBUG purposes ONLY
    # app.add_handler(MessageHandler(filters.ALL, capture_group_topics))

    # app.add_handler(CallbackQueryHandler(register_country, pattern="^citypage_.*"))

    # Callback Query Handlers
    # app.add_handler(CallbackQueryHandler(next_job, pattern="^job_.*"))
    # app.add_handler(CallbackQueryHandler(next_application, pattern="^application_.*"))

    # app.add_handler(CallbackQueryHandler(my_profile, pattern="^my_profile$"))
    # app.add_handler(CallbackQueryHandler(edit_profile, pattern="^edit_profile$"))
    # app.add_handler(CallbackQueryHandler(done_profile, pattern="^done_profile$"))
    # app.add_handler(CallbackQueryHandler(update_username, pattern="^update_username$"))
    # app.add_handler(CallbackQueryHandler(view_jobseeker_profile, pattern="^view_jobseeker_.*"))

    # app.add_handler(CallbackQueryHandler(edit_name, pattern="^edit_name$"))

    # app.add_handler(apply_job_handler)
    app.add_handler(profile_handler)
    # app.add_handler(onboarding_handler)

    # * main menu handler (general)
    # app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu))

    # * command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CommandHandler("my_profile", applicant_profile))
    # app.add_handler(CommandHandler('browse_jobs', browse_jobs))
    # app.add_handler(CommandHandler('saved_jobs', saved_jobs))
    # app.add_handler(CommandHandler('my_applications', my_applications))

    print("Bot is running...")
    app.run_polling(timeout=60)


if __name__ == "__main__":
    main()
