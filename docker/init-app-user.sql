-- Runs once on first database initialisation: creates the non-superuser
-- role the app connects as, so PostgreSQL row-level security is enforced.
CREATE ROLE app_user WITH LOGIN PASSWORD 'app_user_dev_pw' CREATEDB;
CREATE DATABASE taxplanner OWNER app_user;
