import os
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters, ApplicationBuilder, ContextTypes

# Define states
CHOOSING_ROLE, REGISTER_NAME, REGISTER_EMAIL, COMPLETED = range(4)


# Start onboarding
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the onboarding process."""
    keyboard = [
        [InlineKeyboardButton("I'm a Job Seeker 🧑‍💼", callback_data='job_seeker')],
        [InlineKeyboardButton("I'm an Employer 🏢", callback_data='employer')],
    ]
    await update.message.reply_text(
        "👋 Welcome to HulumJobs!\n\n"
        "Let’s get started. Are you a job seeker or an employer?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CHOOSING_ROLE


# Handle role selection
async def choose_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle role selection."""
    query = update.callback_query
    query.answer()
    role = query.data
    context.user_data['role'] = role

    await query.edit_message_text(
        f"Great! You've selected: *{'Job Seeker' if role == 'job_seeker' else 'Employer'}*\n\n"
        "Now, let's register your details. First, what's your name?",
        parse_mode='Markdown'
    )
    return REGISTER_NAME


# Collect user's name
async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Register user's name."""
    name = update.message.text
    context.user_data['name'] = name

    await update.message.reply_text(
        f"Thanks, {name}! Now, please provide your email address."
    )
    return REGISTER_EMAIL


# Collect user's email
async def register_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Register user's email."""
    email = update.message.text
    context.user_data['email'] = email

    role = context.user_data.get('role')
    name = context.user_data.get('name')

    await update.message.reply_text(
        f"🎉 Registration Complete!\n\n"
        f"Name: {name}\n"
        f"Email: {email}\n"
        f"Role: {'Job Seeker' if role == 'job_seeker' else 'Employer'}\n\n"
        f"You can now access the main menu to get started.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Go to Dashboard 🚀", callback_data='dashboard')]
        ])
    )
    return COMPLETED


# Show dashboard
async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the user dashboard."""
    query = update.callback_query
    query.answer()

    role = context.user_data.get('role')
    if role == 'job_seeker':
        keyboard = [
            [InlineKeyboardButton("🔍 Browse Jobs", callback_data='browse_jobs')],
            [InlineKeyboardButton("📝 Create Profile", callback_data='create_profile')],
            [InlineKeyboardButton("📂 Saved Jobs", callback_data='saved_jobs')],
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("📝 Post a Job", callback_data='post_job')],
            [InlineKeyboardButton("📄 View Applicants", callback_data='view_applicants')],
            [InlineKeyboardButton("🏢 Manage Companies", callback_data='manage_companies')],
        ]

    await query.edit_message_text(
        "Here’s your dashboard. Choose an option to get started:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END


# Cancel command
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the conversation."""
    await update.message.reply_text("Onboarding canceled. Type /start to restart.")
    return ConversationHandler.END


# Main function
def main():
    # updater = Updater(os.getenv("TOKEN"))
    # dp = updater.dispatcher
    app = ApplicationBuilder().token(os.getenv('TOKEN')).build()
    

    onboarding_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING_ROLE: [CallbackQueryHandler(choose_role)],
            REGISTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)],
            REGISTER_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_email)],
            COMPLETED: [CallbackQueryHandler(dashboard)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    app.add_handler(onboarding_handler)

    app.run_polling()
    # app.idle()

if __name__ == '__main__':
    main()
