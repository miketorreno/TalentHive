# Snippets

## Telegram HTML supported tags

```HTML
  <b>bold</b>, <strong>bold</strong>
  <i>italic</i>, <em>italic</em>
  <u>underline</u>, <ins>underline</ins>
  <s>strikethrough</s>, <strike>strikethrough</strike>, <del>strikethrough</del>
  <span class="tg-spoiler">spoiler</span>, <tg-spoiler>spoiler</tg-spoiler>
  <b>bold <i>italic bold <s>italic bold strikethrough <span class="tg-spoiler">italic bold strikethrough spoiler</span></s> <u>underline italic bold</u></i> bold</b>
  <a href="http://www.example.com/">inline URL</a>
  <a href="tg://user?id=123456789">inline mention of a user</a>
  <tg-emoji emoji-id="5368324170671202286">👍</tg-emoji>
  <code>inline fixed-width code</code>
  <pre>pre-formatted fixed-width code block</pre>
  <pre><code class="language-python">pre-formatted fixed-width code block written in the Python programming language</code></pre>
  <blockquote>Block quotation started\nBlock quotation continued\nThe last line of the block quotation</blockquote>
  <blockquote expandable>Expandable block quotation started\nExpandable block quotation continued\nExpandable block quotation continued\nHidden by default part of the block quotation started\nExpandable block quotation continued\nThe last line of the block quotation</blockquote>
```


## Check if user is registered
```py
async def is_registered(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user_id = update.effective_user.id
  cur = conn.cursor()
  cur.execute("SELECT user_id FROM users WHERE telegram_id = %s", (user_id,))
  result = cur.fetchone()

  if not result:
    if update.callback_query:
      query = update.callback_query
      await query.edit_message_text("You need to register as a user first!")
    else:
      await update.message.reply_text("You need to register as a user first!")
    return

  user_id = result[0]


# Save user ID in context for later use
context.user_data['user_id'] = result[0]
```


## PostgreSQL
```py
import psycopg2

conn = psycopg2.connect(
  host="localhost",
  database="telegram_job_board",
  user="postgres",
  password="postgres",
  port="5432"
)

cur = conn.cursor()
cur.execute("SELECT user_id FROM users WHERE telegram_id = %s", (user_id,))
result = cur.fetchone()

cur = conn.cursor()
cur.execute("SELECT job_id, title FROM jobs ORDER BY created_at DESC LIMIT 5")
jobs = cur.fetchall()

cur = conn.cursor()
cur.execute(
  "INSERT INTO jobs (company_id, title, description, salary) VALUES (%s, %s, %s, %s)",
  (2, job_title, job_description, job_salary),
)
conn.commit()
```


## MongoDB
```py
import pymongo

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["telegram_job_board"]
collection = db["users"]
```


## Redis
```py
import redis

redis_client = redis.Redis(host="localhost", port=6379, db=0)

redis_client.set("key", "value")
value = redis_client.get("key")

redis_client.delete("key")
```


## Prompts

Want to create a job listing platform as a Telegram bot, here's my setup
Bot Framework: python-telegram-bot
Database: PostgreSQL
Cache: Redis
Bots: Applicant Bot, Employer Bot, Admin Bot (separate)

Use these as a guideline when generating the code for the bot:
- Use latest and greatest practices when generating the code for (python-telegram-bot, postgresql, and redis)
- Avoid outdated code at all costs
- The bot should be able to handle multiple users at the same time
- All interactions should be through reply buttons (or text inputs when receiving a message). Only use inline buttons when it's necessary
- Always validate data before saving it to the database

We gonna work on applicant bot first, and one feature at a time.
registration feature: user must register as a job seeker to use the bot with (name, gender, dob or age, country, city, phone number, email) fields

<!--  -->

Applicant bot
Features:
- Registration
- CV Builder
- Saved Jobs
- Application Tracking
- Job search
- Job alerts
- Job application
- 

User must register as a job seeker to use the bot with (name, gender, dob or age, country, city, phone number, email) fields, 







with the following features. All employers, job seekers & admin must be registered 

For Employers:
Company Creation
Post Job Listings
View Applicants
Promoted Listings

For Job Seekers:
Job Search
Job Alerts
Profile Creation
Saved Jobs
Application Tracking
CV Builder

For Admins:
Moderation Tools
Analytics
Revenue Tracking

Use python-telegram-bot library and postgresql database