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
  first_name VARCHAR NOT NULL,
  last_name VARCHAR NOT NULL,
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
  verified_user BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP,
  deleted_at TIMESTAMP
);

INSERT INTO users (telegram_id, role_id, name, username, gender, dob, email, phone, country, city, education, experience, cv, skills, portfolios, subscribed_alerts, preferences)VALUES (123456789, 1, 'John Doe', 'johndoe', 'Male', '1990-01-01', 'johndoe@example.com', '+1234567890', 'USA', 'New York', 'Bachelor', '5 years', 'cv.pdf', '["Java", "Python"]', '["portfolio1.pdf", "portfolio2.pdf"]', '["alert1", "alert2"]', '{"notifications": true, "email": true, "sms": false}');
INSERT INTO users (telegram_id, role_id, name, username, gender, dob, email, phone, country, city, education, experience, cv, skills, portfolios, subscribed_alerts, preferences)VALUES (987654321, 2, 'Jane Smith', 'janesmith', 'Female', '1995-05-15', 'janesmith@example.com', '+9876543210', 'Canada', 'Toronto', 'Master', '3 years', 'cv.pdf', '["JavaScript", "React"]', '["portfolio3.pdf", "portfolio4.pdf"]', '["alert3", "alert4"]', '{"notifications": false, "email": true, "sms": true}');
INSERT INTO users (telegram_id, role_id, name, username, gender, dob, email, phone, country, city, education, experience, cv, skills, portfolios, subscribed_alerts, preferences)VALUES (111111111, 3, 'Bob Johnson', 'bobjohnson', 'Male', '1985-12-10', 'bobjohnson@example.com', '+1111111111', 'UK', 'London', 'PhD', '10 years', 'cv.pdf', '["C++", "Ruby"]', '["portfolio5.pdf", "portfolio6.pdf"]', '["alert5", "alert6"]', '{"notifications": true, "email": false, "sms": true}');
INSERT INTO users (telegram_id, role_id, name, username, gender, dob, email, phone, country, city, education, experience, cv, skills, portfolios, subscribed_alerts, preferences)VALUES (222222222, 1, 'Alice Brown', 'alicebrown', 'Female', '1992-07-20', 'alicebrown@example.com', '+2222222222', 'Australia', 'Sydney', 'Bachelor', '2 years', 'cv.pdf', '["HTML", "CSS"]', '["portfolio7.pdf", "portfolio8.pdf"]', '["alert7", "alert8"]', '{"notifications": true, "email": true, "sms": false}');
INSERT INTO users (telegram_id, role_id, name, username, gender, dob, email, phone, country, city, education, experience, cv, skills, portfolios, subscribed_alerts, preferences)VALUES (333333333, 2, 'Mike Wilson', 'mikewilson', 'Male', '1988-03-05', 'mikewilson@example.com', '+3333333333', 'Germany', 'Berlin', 'Master', '7 years', 'cv.pdf', '["PHP", "MySQL"]', '["portfolio9.pdf", "portfolio10.pdf"]', '["alert9", "alert10"]', '{"notifications": false, "email": true, "sms": true}');
INSERT INTO users (telegram_id, role_id, name, username, gender, dob, email, phone, country, city, education, experience, cv, skills, portfolios, subscribed_alerts, preferences)VALUES (444444444, 3, 'Sarah Lee', 'sarahlee', 'Female', '1997-11-30', 'sarahlee@example.com', '+4444444444', 'France', 'Paris', 'Bachelor', '1 year', 'cv.pdf', '["Python", "Django"]', '["portfolio11.pdf", "portfolio12.pdf"]', '["alert11", "alert12"]', '{"notifications": true, "email": false, "sms": true}');
INSERT INTO users (telegram_id, role_id, name, username, gender, dob, email, phone, country, city, education, experience, cv, skills, portfolios, subscribed_alerts, preferences)VALUES (555555555, 1, 'David Kim', 'davidkim', 'Male', '1993-09-15', 'davidkim@example.com', '+5555555555', 'Japan', 'Tokyo', 'Master', '4 years', 'cv.pdf', '["JavaScript", "React"]', '["portfolio13.pdf", "portfolio14.pdf"]', '["alert13", "alert14"]', '{"notifications": true, "email": true, "sms": false}');
INSERT INTO users (telegram_id, role_id, name, username, gender, dob, email, phone, country, city, education, experience, cv, skills, portfolios, subscribed_alerts, preferences)VALUES (666666666, 2, 'Emily Chen', 'emilychen', 'Female', '1998-06-25', 'emilychen@example.com', '+6666666666', 'China', 'Shanghai', 'Bachelor', '2 years', 'cv.pdf', '["Java", "Spring"]', '["portfolio15.pdf", "portfolio16.pdf"]', '["alert15", "alert16"]', '{"notifications": false, "email": true, "sms": true}');
INSERT INTO users (telegram_id, role_id, name, username, gender, dob, email, phone, country, city, education, experience, cv, skills, portfolios, subscribed_alerts, preferences)VALUES (777777777, 3, 'Michael Davis', 'michaeldavis', 'Male', '1987-04-10', 'michaeldavis@example.com', '+7777777777', 'Brazil', 'Rio de Janeiro', 'PhD', '8 years', 'cv.pdf', '["C#", "ASP.NET"]', '["portfolio17.pdf", "portfolio18.pdf"]', '["alert17", "alert18"]', '{"notifications": true, "email": false, "sms": true}');
INSERT INTO users (telegram_id, role_id, name, username, gender, dob, email, phone, country, city, education, experience, cv, skills, portfolios, subscribed_alerts, preferences)VALUES (888888888, 1, 'Sophia Martinez', 'sophiamartinez', 'Female', '1994-12-20', 'sophiamartinez@example.com', '+8888888888', 'Mexico', 'Mexico City', 'Master', '5 years', 'cv.pdf', '["Swift", "iOS"]', '["portfolio19.pdf", "portfolio20.pdf"]', '["alert19", "alert20"]', '{"notifications": true, "email": true, "sms": false}');



CREATE TABLE companies (
  company_id SERIAL PRIMARY KEY,
  user_id INT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  company_type VARCHAR NOT NULL,
  startup_type VARCHAR,
  company_name TEXT NOT NULL,
  trade_license TEXT,
  employer_photo TEXT,
  company_description TEXT,
  company_status VARCHAR CHECK (status IN ('pending', 'approved', 'rejected')) DEFAULT 'pending',
  verified_company BOOLEAN DEFAULT FALSE,
  created_by VARCHAR,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP,
  deleted_at TIMESTAMP
);

INSERT INTO companies (user_id, company_type, startup_type, company_name, trade_license, employer_photo, description, company_status, verified_user, created_by) VALUES (1, 'Startup', 'Yes', 'ABC Company', '1234567890', 'employer_photo.jpg', 'We are a leading company in the industry.', 'approved', TRUE, 'John Doe');
INSERT INTO companies (user_id, company_type, startup_type, company_name, trade_license, employer_photo, description, company_status, verified_user, created_by) VALUES (2, 'Startup', 'Yes', 'XYZ Corporation', '9876543210', 'employer_photo.jpg', 'We are a leading company in the industry.', 'approved', TRUE, 'Jane Smith');
INSERT INTO companies (user_id, company_type, startup_type, company_name, trade_license, employer_photo, description, company_status, verified_user, created_by) VALUES (3, 'Startup', 'Yes', '123 Industries', '5678901234', 'employer_photo.jpg', 'We are a leading company in the industry.', 'approved', TRUE, 'John Doe');
INSERT INTO companies (user_id, company_type, startup_type, company_name, trade_license, employer_photo, description, company_status, verified_user, created_by) VALUES (4, 'Startup', 'Yes', '456 Enterprises', '9012345678', 'employer_photo.jpg', 'We are a leading company in the industry.', 'approved', TRUE, 'Jane Smith');
INSERT INTO companies (user_id, company_type, startup_type, company_name, trade_license, employer_photo, description, company_status, verified_user, created_by) VALUES (5, 'Startup', 'Yes', '789 Solutions', '3456789012', 'employer_photo.jpg', 'We are a leading company in the industry.', 'approved', TRUE, 'John Doe');
INSERT INTO companies (user_id, company_type, startup_type, company_name, trade_license, employer_photo, description, company_status, verified_user, created_by) VALUES (6, 'Startup', 'Yes', '012 Tech', '7890123456', 'employer_photo.jpg', 'We are a leading company in the industry.', 'approved', TRUE, 'Jane Smith');
INSERT INTO companies (user_id, company_type, startup_type, company_name, trade_license, employer_photo, description, company_status, verified_user, created_by) VALUES (7, 'Startup', 'Yes', '345 Innovations', '1234567890', 'employer_photo.jpg', 'We are a leading company in the industry.', 'approved', TRUE, 'John Doe');
INSERT INTO companies (user_id, company_type, startup_type, company_name, trade_license, employer_photo, description, company_status, verified_user, created_by) VALUES (8, 'Startup', 'Yes', '678 Ventures', '9876543210', 'employer_photo.jpg', 'We are a leading company in the industry.', 'approved', TRUE, 'Jane Smith');
INSERT INTO companies (user_id, company_type, startup_type, company_name, trade_license, employer_photo, description, company_status, verified_user, created_by) VALUES (9, 'Startup', 'Yes', '901 Solutions', '5678901234', 'employer_photo.jpg', 'We are a leading company in the industry.', 'approved', TRUE, 'John Doe');
INSERT INTO companies (user_id, company_type, startup_type, company_name, trade_license, employer_photo, description, company_status, verified_user, created_by) VALUES (10, 'Startup', 'Yes', '234 Tech', '9012345678', 'employer_photo.jpg', 'We are a leading company in the industry.', 'approved', TRUE, 'Jane Smith');



CREATE TABLE categories (
  category_id SERIAL PRIMARY KEY,
  parent_id INT REFERENCES categories(category_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  category_name TEXT NOT NULL,
  category_description TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP,
  deleted_at TIMESTAMP
);

INSERT INTO categories (parent_id, category_name, category_description) VALUES (NULL, 'Administrative', 'Jobs involving office management, clerical work, and administrative support.');
INSERT INTO categories (parent_id, category_name, category_description) VALUES (NULL, 'Accounting', 'Positions in bookkeeping, auditing, and financial reporting.');
INSERT INTO categories (parent_id, category_name, category_description) VALUES (NULL, 'Business Development', 'Jobs focused on identifying growth opportunities and building client relationships.');
INSERT INTO categories (parent_id, category_name, category_description) VALUES (NULL, 'Consulting', 'Positions providing expert advice in various fields such as management, IT, and finance.');
INSERT INTO categories (parent_id, category_name, category_description) VALUES (NULL, 'Customer Support', 'Jobs that involve assisting customers with inquiries and resolving issues.');
INSERT INTO categories (parent_id, category_name, category_description) VALUES (NULL, 'Data Entry', 'Positions focused on inputting and managing data in various systems.');
INSERT INTO categories (parent_id, category_name, category_description) VALUES (NULL, 'Graphic Design', 'Jobs involving visual communication and design for print and digital media.');
INSERT INTO categories (parent_id, category_name, category_description) VALUES (NULL, 'IT Support', 'Positions providing technical assistance and support for computer systems and networks.');
INSERT INTO categories (parent_id, category_name, category_description) VALUES (NULL, 'Legal Assistant', 'Jobs supporting lawyers with research, documentation, and case management.');
INSERT INTO categories (parent_id, category_name, category_description) VALUES (NULL, 'Network Administration', 'Positions focused on managing and maintaining computer networks.');
INSERT INTO categories (parent_id, category_name, category_description) VALUES (NULL, 'Public Relations', 'Jobs managing communication between organizations and the public.');
INSERT INTO categories (parent_id, category_name, category_description) VALUES (NULL, 'Quality Assurance', 'Positions focused on ensuring products and services meet quality standards.');
INSERT INTO categories (parent_id, category_name, category_description) VALUES (NULL, 'Social Media Management', 'Jobs involving the management and strategy of social media platforms.');
INSERT INTO categories (parent_id, category_name, category_description) VALUES (NULL, 'Technical Support', 'Positions providing assistance with technical products and services.');
INSERT INTO categories (parent_id, category_name, category_description) VALUES (NULL, 'Training and Development', 'Jobs focused on employee training, skill development, and organizational learning.');
INSERT INTO categories (parent_id, category_name, category_description) VALUES (NULL, 'Web Development', 'Positions involving the design and development of websites and web applications.');
INSERT INTO categories (parent_id, category_name, category_description) VALUES (NULL, 'Event Planning', 'Jobs focused on organizing and coordinating events, conferences, and meetings.');
INSERT INTO categories (parent_id, category_name, category_description) VALUES (NULL, 'Insurance Sales', 'Positions involving selling insurance products and managing client relationships.');
INSERT INTO categories (parent_id, category_name, category_description) VALUES (NULL, 'Manufacturing Operations', 'Jobs related to overseeing production processes and managing manufacturing teams.');
INSERT INTO categories (parent_id, category_name, category_description) VALUES (NULL, 'Medical Billing and Coding', 'Positions focused on processing healthcare claims and managing patient records.');
INSERT INTO categories (parent_id, category_name, category_description) VALUES (NULL, 'Real Estate Sales', 'Jobs involving the buying, selling, and leasing of properties.');
INSERT INTO categories (parent_id, category_name, category_description) VALUES (NULL, 'Retail Management', 'Positions overseeing retail operations, staff management, and customer service.');
INSERT INTO categories (parent_id, category_name, category_description) VALUES (NULL, 'Sales Management', 'Jobs focused on leading sales teams and developing sales strategies.');
INSERT INTO categories (parent_id, category_name, category_description) VALUES (NULL, 'Supply Chain Logistics', 'Positions managing the flow of goods and services from suppliers to customers.');
INSERT INTO categories (parent_id, category_name, category_description) VALUES (NULL, 'Technical Writing', 'Jobs involving creating manuals, guides, and documentation for technical products.');
INSERT INTO categories (parent_id, category_name, category_description) VALUES (NULL, 'User Experience (UX) Design', 'Positions focused on enhancing user satisfaction through improved usability and accessibility.');
INSERT INTO categories (parent_id, category_name, category_description) VALUES (NULL, 'Virtual Assistance', 'Jobs providing administrative support remotely to businesses and entrepreneurs.');
INSERT INTO categories (parent_id, category_name, category_description) VALUES (NULL, 'Warehouse Operations', 'Positions related to inventory management, shipping, and receiving in warehouses.');
INSERT INTO categories (parent_id, category_name, category_description) VALUES (NULL, 'Content Management', 'Jobs involving the creation, editing, and management of digital content.');
INSERT INTO categories (parent_id, category_name, category_description) VALUES (NULL, 'Health and Safety', 'Positions focused on ensuring workplace safety and compliance with regulations.');
INSERT INTO categories (parent_id, category_name, category_description) VALUES (NULL, 'Product Management', 'Jobs overseeing the development and marketing of products throughout their lifecycle.');
INSERT INTO categories (parent_id, category_name, category_description) VALUES (NULL, 'Translation and Interpretation', 'Positions providing language translation and interpretation services.');
INSERT INTO categories (parent_id, category_name, category_description) VALUES (NULL, 'Research and Development', 'Positions focused on innovation, product development, and scientific research.');
INSERT INTO categories (parent_id, category_name, category_description) VALUES (NULL, 'Project Management', 'Jobs that involve planning, executing, and closing projects across various industries.');
INSERT INTO categories (parent_id, category_name, category_description) VALUES (NULL, 'Information Security', 'Positions dedicated to protecting information systems and data from cyber threats.');
INSERT INTO categories (parent_id, category_name, category_description) VALUES (NULL, 'Data Science', 'Careers involving data analysis, machine learning, and statistical modeling.');
INSERT INTO categories (parent_id, category_name, category_description) VALUES (NULL, 'Telecommunications', 'Jobs in the field of communication technologies and network management.');
INSERT INTO categories (parent_id, category_name, category_description) VALUES (NULL, 'Non-Profit', 'Positions in organizations focused on social causes and community service.');
INSERT INTO categories (parent_id, category_name, category_description) VALUES (NULL, 'Government', 'Jobs in federal, state, and local government agencies.');
INSERT INTO categories (parent_id, category_name, category_description) VALUES (NULL, 'Environmental Services', 'Positions related to environmental protection, sustainability, and conservation.');



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
  salary_currency VARCHAR,
  skills_expertise TEXT,
  job_status VARCHAR CHECK (status IN ('pending', 'approved', 'rejected')) DEFAULT 'pending',
  job_promoted BOOLEAN DEFAULT FALSE,
  job_closed BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP,
  deleted_at TIMESTAMP
);

INSERT INTO jobs (company_id, user_id, category_id, job_title, job_type, job_site, job_sector, education_qualification, experience_level, gender_preference, job_deadline, job_vacancies, job_description, job_requirements, job_city, job_country, salary_type, salary_amount, salary_currency, skills_expertise, job_status, job_promoted)
VALUES (1, 1, 1, 'Data Scientist', 'Full-time', 'LinkedIn', 'Technology', 'Bachelor', 'Mid-level', 'Male', '2024-12-31', '10', 'We are looking for a data scientist to join our team.', 'Requirements for the data scientist:', 'New York', 'USA', 'Hourly', 50, 'USD', '{"Python", "Machine Learning"}', 'approved', true);
INSERT INTO jobs (company_id, user_id, category_id, job_title, job_type, job_site, job_sector, education_qualification, experience_level, gender_preference, job_deadline, job_vacancies, job_description, job_requirements, job_city, job_country, salary_type, salary_amount, salary_currency, skills_expertise, job_status, job_promoted)
VALUES (2, 2, 2, 'Software Engineer', 'Full-time', 'LinkedIn', 'Technology', 'Bachelor', 'Mid-level', 'Male', '2024-12-31', '10', 'We are looking for a software engineer to join our team.', 'Requirements for the software engineer:', 'New York', 'USA', 'Hourly', 50, 'USD', '{"Python", "Machine Learning"}', 'approved', true);
INSERT INTO jobs (company_id, user_id, category_id, job_title, job_type, job_site, job_sector, education_qualification, experience_level, gender_preference, job_deadline, job_vacancies, job_description, job_requirements, job_city, job_country, salary_type, salary_amount, salary_currency, skills_expertise, job_status, job_promoted)
VALUES (3, 3, 3, 'UI/UX Designer', 'Full-time', 'LinkedIn', 'Technology', 'Bachelor', 'Mid-level', 'Male', '2024-12-31', '10', 'We are looking for a UI/UX designer to join our team.', 'Requirements for the UI/UX designer:', 'New York', 'USA', 'Hourly', 50, 'USD', '{"Python", "Machine Learning"}', 'approved', true);
INSERT INTO jobs (company_id, user_id, category_id, job_title, job_type, job_site, job_sector, education_qualification, experience_level, gender_preference, job_deadline, job_vacancies, job_description, job_requirements, job_city, job_country, salary_type, salary_amount, salary_currency, skills_expertise, job_status, job_promoted)
VALUES (4, 4, 4, 'Marketing Manager', 'Full-time', 'LinkedIn', 'Technology', 'Bachelor', 'Mid-level', 'Male', '2024-12-31', '10', 'We are looking for a marketing manager to join our team.', 'Requirements for the marketing manager:', 'New York', 'USA', 'Hourly', 50, 'USD', '{"Python", "Machine Learning"}', 'approved', true);
INSERT INTO jobs (company_id, user_id, category_id, job_title, job_type, job_site, job_sector, education_qualification, experience_level, gender_preference, job_deadline, job_vacancies, job_description, job_requirements, job_city, job_country, salary_type, salary_amount, salary_currency, skills_expertise, job_status, job_promoted)
VALUES (5, 5, 5, 'Product Manager', 'Full-time', 'LinkedIn', 'Technology', 'Bachelor', 'Mid-level', 'Male', '2024-12-31', '10', 'We are looking for a product manager to join our team.', 'Requirements for the product manager:', 'New York', 'USA', 'Hourly', 50, 'USD', '{"Python", "Machine Learning"}', 'approved', true);
INSERT INTO jobs (company_id, user_id, category_id, job_title, job_type, job_site, job_sector, education_qualification, experience_level, gender_preference, job_deadline, job_vacancies, job_description, job_requirements, job_city, job_country, salary_type, salary_amount, salary_currency, skills_expertise, job_status, job_promoted)
VALUES (6, 6, 6, 'Data Analyst', 'Full-time', 'LinkedIn', 'Technology', 'Bachelor', 'Mid-level', 'Male', '2024-12-31', '10', 'We are looking for a data analyst to join our team.', 'Requirements for the data analyst:', 'New York', 'USA', 'Hourly', 50, 'USD', '{"Python", "Machine Learning"}', 'approved', true);
INSERT INTO jobs (company_id, user_id, category_id, job_title, job_type, job_site, job_sector, education_qualification, experience_level, gender_preference, job_deadline, job_vacancies, job_description, job_requirements, job_city, job_country, salary_type, salary_amount, salary_currency, skills_expertise, job_status, job_promoted)
VALUES (7, 7, 7, 'Sales Manager', 'Full-time', 'LinkedIn', 'Technology', 'Bachelor', 'Mid-level', 'Male', '2024-12-31', '10', 'We are looking for a sales manager to join our team.', 'Requirements for the sales manager:', 'New York', 'USA', 'Hourly', 50, 'USD', '{"Python", "Machine Learning"}', 'approved', true);
INSERT INTO jobs (company_id, user_id, category_id, job_title, job_type, job_site, job_sector, education_qualification, experience_level, gender_preference, job_deadline, job_vacancies, job_description, job_requirements, job_city, job_country, salary_type, salary_amount, salary_currency, skills_expertise, job_status, job_promoted)
VALUES (8, 8, 8, 'Customer Support', 'Full-time', 'LinkedIn', 'Technology', 'Bachelor', 'Mid-level', 'Male', '2024-12-31', '10', 'We are looking for a customer support to join our team.', 'Requirements for the customer support:', 'New York', 'USA', 'Hourly', 50, 'USD', '{"Python", "Machine Learning"}', 'approved', true);
INSERT INTO jobs (company_id, user_id, category_id, job_title, job_type, job_site, job_sector, education_qualification, experience_level, gender_preference, job_deadline, job_vacancies, job_description, job_requirements, job_city, job_country, salary_type, salary_amount, salary_currency, skills_expertise, job_status, job_promoted)
VALUES (9, 9, 9, 'Customer Support', 'Full-time', 'LinkedIn', 'Technology', 'Bachelor', 'Mid-level', 'Male', '2024-12-31', '10', 'We are looking for a customer support to join our team.', 'Requirements for the customer support:', 'New York', 'USA', 'Hourly', 50, 'USD', '{"Python", "Machine Learning"}', 'approved', true);
INSERT INTO jobs (company_id, user_id, category_id, job_title, job_type, job_site, job_sector, education_qualification, experience_level, gender_preference, job_deadline, job_vacancies, job_description, job_requirements, job_city, job_country, salary_type, salary_amount, salary_currency, skills_expertise, job_status, job_promoted)
VALUES (10, 10, 10, 'Customer Support', 'Full-time', 'LinkedIn', 'Technology', 'Bachelor', 'Mid-level', 'Male', '2024-12-31', '10', 'We are looking for a customer support to join our team.', 'Requirements for the customer support:', 'New York', 'USA', 'Hourly', 50, 'USD', '{"Python", "Machine Learning"}', 'approved', true);



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

