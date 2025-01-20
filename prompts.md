# Generating tests

this is my profile function, add inline buttons to edit it. make sure it has great ux

start with just a single "edit" button and when the user click on it show the rest of edit buttons. Also users should be able to edit one field at a time, if the chose to they can continue 

```python
async def my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update, context)
    
    await update.message.reply_text(
        text=f"<b>My Profile</b> \n\n"
            f"<b>👤 \tName</b>: \t{(user[3].split()[0]).capitalize()} {(user[3].split()[1]).capitalize()} \n\n"
            f"<b>\t&#64; \t\tUsername</b>: \t{user[4]} \n\n"
            f"<b>👫 \tGender</b>: \t{user[5]} \n\n"
            f"<b>🎂 \tAge</b>: \t{user[6]} \n\n"
            f"<b>🌐 \tCountry</b>: \t{user[9]} \n\n"
            f"<b>🏙️ \tCity</b>: \t{user[10]} \n\n"
            f"<b>📧 \tEmail</b>: \t{user[7]} \n\n"
            f"<b>📞 \tPhone</b>: \t{user[8]} \n\n",
        parse_mode='HTML'
    )
    return
```

