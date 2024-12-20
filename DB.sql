-- LOGIN INTO POSTGRES
  -- 
  -- sudo -i -u postgres
  -- psql
  -- 
  -- sudo -u postgres
  -- psql -d mypgdatabase -U mypguser


CREATE TABLE users (
  user_id SERIAL PRIMARY KEY,
  telegram_id BIGINT UNIQUE NOT NULL,
  role_id INT NOT NULL CHECK (role_id IN (1, 2, 3)),
  name VARCHAR NOT NULL,
  username VARCHAR,
  location VARCHAR,
  city VARCHAR,
  email VARCHAR,
  phone VARCHAR,
  education VARCHAR,
  experience VARCHAR,
  cv VARCHAR,
  skills JSON,
  portfolios JSON,
  subscribed_alerts JSON,
  preferences JSON,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE TABLE companies (
  company_id SERIAL PRIMARY KEY,
  user_id INT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  name TEXT NOT NULL,
  description TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE TABLE jobs (
  job_id SERIAL PRIMARY KEY,
  company_id INT NOT NULL REFERENCES companies(company_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  title TEXT NOT NULL,
  description TEXT,
  requirements TEXT,
  location VARCHAR,
  salary VARCHAR,
  is_promoted BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE TABLE applications (
  application_id SERIAL PRIMARY KEY,
  job_id INT NOT NULL REFERENCES jobs(job_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  user_id INT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  status TEXT CHECK (status IN ('applied', 'shortlisted', 'rejected')) DEFAULT 'applied',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE TABLE saved_jobs (
  save_id SERIAL PRIMARY KEY,
  job_id INT NOT NULL REFERENCES jobs(job_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  user_id INT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP
);














-- Generated 
  CREATE TABLE alerts (
    alert_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR NOT NULL,
    description VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
  );
  CREATE TABLE user_alerts (
    user_alert_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    alert_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
  );
  CREATE TABLE notifications (
    notification_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
  );
  CREATE TABLE messages (
    message_id SERIAL PRIMARY KEY,
    sender_id INT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    receiver_id INT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
  );
  CREATE TABLE feedback (
    feedback_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
  );
  CREATE TABLE reports (
    report_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
  );
  CREATE TABLE settings (
    setting_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    key VARCHAR NOT NULL,
    value VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
  );
