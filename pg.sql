-- LOGIN INTO POSTGRES
-- sudo -i -u postgres
-- psql
-- 
-- 

CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  telegram_id BIGINT NOT NULL,
  role_id INT NOT NULL,
  name VARCHAR NOT NULL,
  email VARCHAR,
  username VARCHAR,
  phone VARCHAR,
  education VARCHAR,
  experience VARCHAR,
  location VARCHAR,
  resume VARCHAR,
  skills JSON,
  portfolios JSON,
  subscribed_alerts JSON,
  preferences JSON
);
