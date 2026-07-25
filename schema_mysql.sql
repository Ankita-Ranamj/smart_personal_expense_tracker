-- OPTIONAL: If you want to use MySQL instead of the built-in SQLite database,
-- run this in MySQL Workbench, then change SQLALCHEMY_DATABASE_URI in app.py to:
--   mysql+pymysql://username:password@localhost/expense_tracker
-- and install: pip install pymysql

CREATE DATABASE IF NOT EXISTS expense_tracker;
USE expense_tracker;

CREATE TABLE user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(80) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(200) NOT NULL,
    currency VARCHAR(10) DEFAULT '₹',
    daily_limit FLOAT DEFAULT 0,
    savings_goal_name VARCHAR(120) DEFAULT '',
    savings_goal_amount FLOAT DEFAULT 0,
    savings_saved FLOAT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE transaction (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    type VARCHAR(10) NOT NULL,
    category VARCHAR(50) NOT NULL,
    amount FLOAT NOT NULL,
    note VARCHAR(200),
    txn_date DATE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);
