CREATE SCHEMA IF NOT EXISTS login;

CREATE TABLE IF NOT EXISTS login.user
(
    user_id uuid PRIMARY KEY,
    username varchar(255) not null UNIQUE,
    hashed_password bytea not null
);

CREATE TABLE IF NOT EXISTS login.role
(
    user_id uuid PRIMARY KEY,
    role varchar(255) not null
);
