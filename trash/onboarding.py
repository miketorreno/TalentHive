from trash.mini import (main, start_command, help_command, cancel_command)
from telegram import (
  Update,
  InlineKeyboardButton,
  InlineKeyboardMarkup,
  ReplyKeyboardMarkup,
  ReplyKeyboardRemove,
)
from telegram.ext import (
  filters,
  Application,
  ContextTypes,
  CommandHandler,
  MessageHandler,
  ConversationHandler,
  CallbackQueryHandler,
)

J_NAME, J_EMAIL, R_NAME, ROLE_DECISION = range(4)

async def role_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  await query.answer()
  decision = query.data
  
  if decision == 'jobseeker':
    print("job seekerrrrr")
    await query.edit_message_text(
      text=f"<b>Job Seeker Registration</b>\n\n"
            "<b>Please enter your name: </b>",
      parse_mode="HTML"
    )
    return J_NAME
  elif decision == 'recruiter':
    print("recruiterrrrr")
    await query.edit_message_text(
      text=f"<b>Recruiter Registration</b>\n\n"
            "<b>Please enter your name: </b>",
      parse_mode="HTML"
    )
    return R_NAME
  else:
    print("who the ...")
    await query.edit_message_text(
      text="<b>Invalid choice. Please try again.</b>"
    )
    return ROLE_DECISION

async def j_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
  context.user_data['j_id'] = update.message.chat.id
  context.user_data['j_name'] = update.message.text
  
  await update.message.reply_html(f"<b>Please enter your email: </b>")
  
  return J_EMAIL

async def j_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
  context.user_data['j_email'] = update.message.text
  
  await update.message.reply_html(f"<b>Please enter your skills (separate each by comma): </b>")
  
  return


onboarding_handler = ConversationHandler(
  entry_points=[CommandHandler('start', start_command)],
  states={
    ROLE_DECISION: [CallbackQueryHandler(role_decision)],
    J_NAME: [MessageHandler(filters.TEXT & (~filters.COMMAND), j_name)],
    J_EMAIL: [MessageHandler(filters.TEXT & (~filters.COMMAND), j_email)],
    # J_SKILLS: [MessageHandler(filters.TEXT & (~filters.COMMAND), j_skills)],
    # J_EXPERIENCE: [MessageHandler(filters.TEXT & (~filters.COMMAND), j_experience)],
    # J_LOCATION: [MessageHandler(filters.TEXT & (~filters.COMMAND), j_location)],
    # J_REGISTER: [MessageHandler(filters.TEXT & (~filters.COMMAND), j_register)],      
    # R_NAME: [MessageHandler(filters.TEXT & (~filters.COMMAND), r_name)],
    # R_EMAIL: [MessageHandler(filters.TEXT & (~filters.COMMAND), r_email)],
    # R_LOCATION: [MessageHandler(filters.TEXT & (~filters.COMMAND), r_location)],
  },
  fallbacks=[CommandHandler("cancel", cancel_command)],
)

main.app.add_handler(onboarding_handler)
