CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS urls (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    short_code VARCHAR(10) UNIQUE NOT NULL,
    original_url TEXT NOT NULL,
    title VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    url_id INTEGER NOT NULL REFERENCES urls(id),
    user_id INTEGER REFERENCES users(id),
    event_type VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    details TEXT
);

\COPY users(id,username,email,created_at) FROM '/seed/users.csv' CSV HEADER;
SELECT setval(pg_get_serial_sequence('users','id'), (SELECT MAX(id) FROM users));

\COPY urls(id,user_id,short_code,original_url,title,is_active,created_at,updated_at) FROM '/seed/urls.csv' CSV HEADER;
SELECT setval(pg_get_serial_sequence('urls','id'), (SELECT MAX(id) FROM urls));

\COPY events(id,url_id,user_id,event_type,timestamp,details) FROM '/seed/events.csv' CSV HEADER;
SELECT setval(pg_get_serial_sequence('events','id'), (SELECT MAX(id) FROM events));
