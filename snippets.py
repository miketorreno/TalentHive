# Check if user is registered
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



# PostgreSQL
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



# MongoDB
import pymongo

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["telegram_job_board"]
collection = db["users"]



# Redis
import redis

redis_client = redis.Redis(host="localhost", port=6379, db=0)

redis_client.set("key", "value")
value = redis_client.get("key")

redis_client.delete("key")

