# Telegram Job Board

Telegram bot that allows recruiters to post jobs and job seekers to browse & apply for jobs.

## Features

- Job seekers can search for jobs, apply for jobs, and view their applications.
- Recruiters can post jobs, view job applications, and manage their jobs.
- Users can create an account and log in to the bot.
- Users can view their profile information and update their information.
- Users can view their job applications and manage their applications.

## Roadmap

- [ ] Improve the UX
  - [ ] Add datepicker package for job posting
  - [ ] Add awesome data display package
  - [ ] Add conventional price range picker package
- [ ] Add tests
- [ ] Integrate Redis (for blazingly fast experience) - No one is patient
- [ ] Add more features
- [ ] Add more documentation

## Fixes

- [ ] Add exception handling for DB queries
- [ ] User check is very very redundant (research a better way to do it) - Possibly if you check user registration status & fetch it's data at the beginning it'll be a whole lot better and faster
- [ ] Fix bugs
- [ ] Add error handling
- [ ] Fix performance issues
- [ ] Fix security vulnerabilities

```py
# Example of exception handling

import psycopg2

try:
    # Your database operations here
    cursor.execute("YOUR SQL COMMAND")
    connection.commit()
except psycopg2.Error as e:
    print("An error occurred:", e)
    connection.rollback()  # Rollback the transaction
finally:
    cursor.close()
    connection.close()

```