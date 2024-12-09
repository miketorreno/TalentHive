-- sudo -i -u postgres

CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  role INT NOT NULL,
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
