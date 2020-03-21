CREATE TABLE helper(
    id SERIAL PRIMARY KEY,
    phone TEXT NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL,
    lon REAL NOT NULL,
    lat REAL NOT NULL,
);
