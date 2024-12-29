-- LOGIN INTO POSTGRES
  -- 
  -- sudo -i -u postgres
  -- psql
  -- 
  -- sudo -u postgres
  -- psql -d mypgdatabase -U mypguser


CREATE TABLE users (
  user_id SERIAL PRIMARY KEY,
  telegram_id BIGINT NOT NULL,
  role_id INT NOT NULL CHECK (role_id IN (1, 2, 3)),
  name VARCHAR NOT NULL,
  username VARCHAR,
  gender VARCHAR,
  dob VARCHAR,
  email VARCHAR,
  phone VARCHAR,
  country VARCHAR,
  city VARCHAR,
  education VARCHAR,
  experience VARCHAR,
  cv VARCHAR,
  skills JSON,
  portfolios JSON,
  subscribed_alerts JSON,
  preferences JSON,
  verified BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP,
  deleted_at TIMESTAMP
);

INSERT INTO users (telegram_id, role_id, name, username, gender, dob, email, phone, country, city, education, experience, cv, skills, portfolios, subscribed_alerts, preferences)
VALUES (123456789, 1, 'John Doe', 'johndoe', 'Male', '1990-01-01', 'johndoe@example.com', '+1234567890', 'USA', 'New York', 'Bachelor', '5 years', 'cv.pdf', '["Java", "Python"]', '["portfolio1.pdf", "portfolio2.pdf"]', '["alert1", "alert2"]', '{"notifications": true, "email": true, "sms": false}');



CREATE TABLE companies (
  company_id SERIAL PRIMARY KEY,
  user_id INT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  name TEXT NOT NULL,
  description TEXT,
  status VARCHAR CHECK (status IN ('pending', 'approved', 'rejected')) DEFAULT 'pending',
  verified BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP,
  deleted_at TIMESTAMP
);

INSERT INTO companies (user_id, name, description)
VALUES (1, 'ABC Company', 'We are a leading company in the industry.');
INSERT INTO companies (user_id, name, description)
VALUES (1, 'XYZ Corporation', 'We are a leading company in the industry.');
INSERT INTO companies (user_id, name, description)
VALUES (1, '123 Industries', 'We are a leading company in the industry.');
INSERT INTO companies (user_id, name, description)
VALUES (1, '456 Enterprises', 'We are a leading company in the industry.');



CREATE TABLE categories (
  category_id SERIAL PRIMARY KEY,
  parent_id INT REFERENCES categories(category_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  name TEXT NOT NULL,
  description TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP,
  deleted_at TIMESTAMP
);

INSERT INTO categories (parent_id, name, description)
VALUES (NULL, 'Technology', 'Technology category');
INSERT INTO categories (parent_id, name, description)
VALUES (1, 'Data Science', 'Data science category');
INSERT INTO categories (parent_id, name, description)
VALUES (1, 'AI', 'Artificial intelligence category');
INSERT INTO categories (parent_id, name, description)
VALUES (1, 'App Development', 'App development category');



CREATE TABLE jobs (
  job_id SERIAL PRIMARY KEY,
  company_id INT NOT NULL REFERENCES companies(company_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  user_id INT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  category_id INT NOT NULL REFERENCES categories(category_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  type VARCHAR,
  title TEXT NOT NULL,
  description TEXT,
  requirements TEXT,
  city VARCHAR,
  country VARCHAR,
  salary VARCHAR,
  deadline DATE,
  status VARCHAR CHECK (status IN ('pending', 'approved', 'rejected')) DEFAULT 'pending',
  promoted BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP,
  deleted_at TIMESTAMP
);

INSERT INTO jobs (company_id, user_id, category_id, type, title, description, requirements, city, country, salary, deadline, promoted)
VALUES (1, 1, 1, 'Remote', 'Data Scientist', 'We are looking for a data scientist to join our team.', 'Requirements for the data scientist:', 'Remote', 'Anywhere', '$100,000', '2024-12-31', true);
INSERT INTO jobs (company_id, user_id, category_id, type, title, description, requirements, city, country, salary, deadline, promoted)
VALUES (2, 1, 2, 'On-site - Permanent', 'Machine Learning Engineer', 'We are looking for a machine learning engineer to join our team.', 'Requirements for the machine learning engineer:', 'Hawassa', 'Ethiopia', '$80,000', '2024-12-31', false);
INSERT INTO jobs (company_id, user_id, category_id, type, title, description, requirements, city, country, salary, deadline, promoted)
VALUES (3, 1, 3, 'Remote - Full-time', 'Software Engineer', 'We are looking for a software engineer to join our team.', 'Requirements for the software engineer:', 'Remote', 'Anywhere', '$90,000', '2024-12-31', true);
INSERT INTO jobs (company_id, user_id, category_id, type, title, description, requirements, city, country, salary, deadline, promoted)
VALUES (3, 1, 4, 'On-site - Part-time', 'Full Stack Developer', 'We are looking for a full stack developer to join our team.', 'Requirements for the full stack developer:', 'Addis Ababa', 'Ethiopia', '$110,000', '2024-12-31', false);
INSERT INTO jobs (company_id, user_id, category_id, type, title, description, requirements, city, country, salary, deadline, promoted)
VALUES (4, 1, 2, 'Remote - Contract', 'Data Analyst', 'We are looking for a data analyst to join our team.', 'Requirements for the data analyst:', 'Remote', 'Anywhere', '$70,000', '2024-12-31', true);
INSERT INTO jobs (company_id, user_id, category_id, type, title, description, requirements, city, country, salary, deadline, promoted)
VALUES (4, 1, 2, 'On-site - Full-time', 'DevOps Engineer', 'We are looking for a DevOps engineer to join our team.', 'Requirements for the DevOps engineer:', 'Addis Ababa', 'Ethiopia', '$120,000', '2024-12-31', false);



CREATE TABLE applications (
  application_id SERIAL PRIMARY KEY,
  job_id INT NOT NULL REFERENCES jobs(job_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  user_id INT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  cover_letter TEXT,
  note TEXT,
  cv VARCHAR,
  status VARCHAR CHECK (status IN ('applied', 'shortlisted', 'rejected')) DEFAULT 'applied',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP,
  deleted_at TIMESTAMP
);













-- Not so urgent
  CREATE TABLE saved_jobs (
    save_id SERIAL PRIMARY KEY,
    job_id INT NOT NULL REFERENCES jobs(job_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP
  );


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

