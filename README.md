# Telegram Job Board

Telegram bot that allows recruiters to post jobs and job seekers to browse & apply for jobs.



## Features

- Job seekers can search for jobs, apply for jobs, and view their applications.
- Recruiters can post jobs, view job applications, and manage their jobs.
- Users can create an account and log in to the bot.
- Users can view their profile information and update their information.
- Users can view their job applications and manage their applications.


## Roadmap

- [ ] Write tests
  - [ ] Unit tests
  - [ ] Integration tests
  - [ ] End-to-end tests
- [ ] Improve the UX
  - [ ] Add datepicker package for job posting
  - [ ] Add awesome data display package
  - [ ] Add conventional price range picker package
- [ ] Integrate Redis (for blazingly fast experience) - No one is patient
- [ ] Add more features
- [ ] Add more documentation


## Fixes

- [ ] Empty `context.user_data`, `user_data` & `data` variables after you're done with 'em
- [ ] `conn.close()` research this stuff & close every connection
- [ ] Change age to dob in the db (by subtracting it when saving & fetching it)
- [ ] Add the ability to enter city name when registering, if it's not available in the list
- [ ] Remove Reply Keyboard properly, when done using it or user is moved to other steps
- [ ] Edit functionality at confirm_apply stage
- [ ] Go line by line & refine end user messages *(with AI & Grammarly)*
- [x] When user uploads new cv while it only checks for docs & text ... it won't respond to other file types. Just add a check for the rest types & change the filter on `MessageHandler(filters.Document.ALL & ~filters.COMMAND, new_cv),`
- [X] use `get_user(update, context)` helper function whenever you need to get the user object
  - [x] on applicant bot
  - [x] on employer bot
- [ ] use `get_job(update, context)` helper function whenever you need to get a job object
  - [ ] on applicant bot
  - [ ] on employer bot
- [x] current_job_index = 0 & current_saved_job_index = 0; check these vars with returned no. of jobs in the db in `my_applications` and `saved_jobs`
- [ ] Implement input validation for all fields the way you did for the `salary` field when posting a job
  - [x] on applicant bot
  - [ ] on employer bot
- [ ] Add exception handling for ALL DB queries
  - [ ] on applicant bot
  - [ ] on employer bot
- [ ] User check is very very redundant (research a better way to do it) - Possibly if you check user registration status & fetch it's data at the beginning it'll be a whole lot better and faster
- [ ] Fix bugs
- [ ] Add error handling
  - [x] on applicant bot
  - [ ] on employer bot
- [ ] Fix performance issues
- [ ] Fix security vulnerabilities
- [ ] Add "You sure?" kinda prompt before canceling job posting, onboarding, applying, etc.
- [ ] Remove all comments after testing everything (manually & automated)


## Ideas, for the round table
-  [ ] At least salary range should be a must, exact salary is preferred
-  [ ] Once an employer is done selecting his/her perfect candidate, there should be a reply message at the very least an automated replay. Something like "Thanks for participation, we've already chosen our candidate for the job."


# Snippets

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
