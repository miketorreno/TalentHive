CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  telegram_id BIGINT NOT NULL,
  role_id INT NOT NULL CHECK (role_id IN (1, 2, 3)),
  first_name VARCHAR NOT NULL,
  last_name VARCHAR NOT NULL,
  username VARCHAR,
  gender VARCHAR,
  dob VARCHAR,
  phone VARCHAR,
  email VARCHAR,
  password VARCHAR,
  country VARCHAR,
  city VARCHAR,
  education VARCHAR,
  experience VARCHAR,
  cv_url VARCHAR,
  skills JSON,
  portfolios JSON,
  user_preferences JSON,
  subscribed_alerts JSON,
  verified_user BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP,
  deleted_at TIMESTAMP
);


CREATE TABLE categories (
  category_id SERIAL PRIMARY KEY,
  parent_id INT REFERENCES categories(category_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  category_name TEXT NOT NULL,
  category_description TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP,
  deleted_at TIMESTAMP
);


CREATE TABLE companies (
  company_id SERIAL PRIMARY KEY,
  user_id INT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  company_type VARCHAR NOT NULL,
  startup_type VARCHAR,
  company_name TEXT NOT NULL,
  company_description TEXT,
  trade_license TEXT,
  employer_photo TEXT,
  company_website VARCHAR,
  company_industry VARCHAR,
  company_status VARCHAR CHECK (status IN ('pending', 'approved', 'rejected')) DEFAULT 'pending',
  verified_company BOOLEAN DEFAULT FALSE,
  created_by VARCHAR,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP,
  deleted_at TIMESTAMP
);


CREATE TABLE jobs (
  job_id SERIAL PRIMARY KEY,
  company_id INT NOT NULL REFERENCES companies(company_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  user_id INT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  category_id INT NOT NULL REFERENCES categories(category_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  job_title VARCHAR NOT NULL,
  job_type VARCHAR NOT NULL,
  job_site VARCHAR NOT NULL,
  job_sector VARCHAR NOT NULL,
  education_qualification VARCHAR NOT NULL,
  experience_level VARCHAR NOT NULL,
  gender_preference VARCHAR,
  job_deadline DATE,
  job_vacancies VARCHAR,
  job_description TEXT,
  job_requirements TEXT,
  job_city VARCHAR,
  job_country VARCHAR,
  salary_type VARCHAR,
  salary_amount NUMERIC CHECK (salary_amount >= 0) DEFAULT 0,
  salary_range JSON,
  salary_currency VARCHAR,
  skills_expertise TEXT,
  job_status VARCHAR CHECK (status IN ('pending', 'approved', 'rejected')) DEFAULT 'pending',
  job_promoted BOOLEAN DEFAULT FALSE,
  job_closed BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP,
  deleted_at TIMESTAMP
);


CREATE TABLE applications (
  application_id SERIAL PRIMARY KEY,
  job_id INT NOT NULL REFERENCES jobs(job_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  user_id INT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  cover_letter TEXT,
  resume VARCHAR,
  portfolio JSON,
  application_note TEXT,
  application_status VARCHAR CHECK (status IN ('applied', 'seen', 'shortlisted', 'rejected')) DEFAULT 'applied',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP,
  deleted_at TIMESTAMP
);


CREATE TABLE saved_jobs (
  saved_job_id SERIAL PRIMARY KEY,
  job_id INT NOT NULL REFERENCES jobs(job_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  user_id INT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP,
  deleted_at TIMESTAMP
);










-- Not so urgent



-- Generated 
  CREATE TABLE alerts (
    alert_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR NOT NULL,
    description VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP
  );
  CREATE TABLE user_alerts (
    user_alert_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    alert_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP
  );
  CREATE TABLE notifications (
    notification_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP
  );
  CREATE TABLE messages (
    message_id SERIAL PRIMARY KEY,
    sender_id INT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    receiver_id INT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP
  );
  CREATE TABLE feedback (
    feedback_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP
  );
  CREATE TABLE reports (
    report_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP
  );
  CREATE TABLE settings (
    setting_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    key VARCHAR NOT NULL,
    value VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP
  );
