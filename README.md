# 💸 Smart Personal Expense Tracker

A full-stack web app to record and manage income/expenses, with categorization,
monthly tracking, charts, savings goals, streaks, and badges — built with
**HTML, CSS, JavaScript, Python (Flask), and SQL**.

---

## 1. Tech Stack

| Layer     | Technology                          |
|-----------|--------------------------------------|
| Frontend  | HTML5, CSS3 (glassmorphism), JavaScript, Chart.js |
| Backend   | Python + Flask                       |
| Database  | SQLite (default, zero setup) — MySQL script included for upgrade |
| Auth      | Session-based login, hashed passwords (Werkzeug) |

## 2. Features

- **Auth**: Signup, Login, Forgot Password, Logout
- **Dashboard**: Today's expense, month expense, income, balance, recent transactions
- **Expense/Income CRUD**: Add, edit, delete, search, filter by date/category/type
- **Categories**: Food, Shopping, Travel, Bills, Education, Health, Entertainment (with emoji)
- **Charts**: Pie (by category), Bar (6-month trend), Line (weekly), Doughnut (income vs expense)
- **Reports**: Top category, monthly report, yearly report
- **Export**: Download all transactions as CSV
- **Settings**: Dark mode, currency symbol, daily spending limit, profile
- **Smart Insight**: Rule-based "AI-style" spending comparison (no external API/key needed)
- **Savings Goal** with progress bar
- **Daily Spending Limit** with warning banner
- **Streak system** (🔥 consecutive days under budget)
- **Achievement badges** (🏆💰🎯)
- **Calendar view** — click a date to see that day's transactions

---

## 3. Project Structure

```
expense-tracker/
├── app.py                  # Flask app: routes, models, logic
├── requirements.txt        # Python dependencies
├── schema_mysql.sql        # Optional MySQL schema (upgrade path)
├── expense_tracker.db      # SQLite database (auto-created on first run)
├── templates/               # Jinja2 HTML templates
│   ├── base.html
│   ├── login.html / signup.html / forgot_password.html
│   ├── dashboard.html
│   ├── add_edit.html
│   ├── transactions.html
│   ├── reports.html
│   ├── calendar.html
│   └── settings.html
└── static/
    ├── css/style.css       # Glassmorphism + dark mode styling
    └── js/script.js        # Dark mode toggle
```

---

## 4. How to Run on Your System (VS Code)

### Step 1 — Prerequisites
Install **Python 3.9+** from [python.org](https://python.org) (check "Add to PATH" during install).
Install **VS Code** and the **Python extension** (from the Extensions tab).

### Step 2 — Get the project
Download/unzip this project folder, then open it in VS Code:
```
File → Open Folder → select "expense-tracker"
```

### Step 3 — Open a terminal in VS Code
`Terminal → New Terminal` (or `` Ctrl+` ``)

### Step 4 — Create a virtual environment (recommended)
```bash
python -m venv venv

# Activate it:
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### Step 5 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 6 — Run the app
```bash
python app.py
```

### Step 7 — Open in browser
Go to: **http://127.0.0.1:5000**

The SQLite database (`expense_tracker.db`) is created automatically on first run —
no manual database setup needed. Sign up for an account and start adding transactions!

---

## 5. (Optional) Switch to MySQL

If you want to demonstrate MySQL specifically (e.g., for a resume/interview):

1. Install MySQL and open **MySQL Workbench**.
2. Run the script in `schema_mysql.sql` to create the database and tables.
3. Install the MySQL driver: `pip install pymysql`
4. In `app.py`, change:
   ```python
   app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "expense_tracker.db")
   ```
   to:
   ```python
   app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:yourpassword@localhost/expense_tracker"
   ```
5. Remove `db.create_all()` from `app.py` since tables are created by the SQL script (or keep it — SQLAlchemy will skip existing tables).

---

## 6. How This Maps to Your Resume Bullet

> **Personal Expense Tracker** | HTML, CSS, JavaScript, SQL
> - Developed a web-based application to record and manage daily income and expenses.
> - Implemented transaction categorization and monthly expense tracking features.
> - Integrated SQL database for efficient storage and retrieval of financial records.

- "Record and manage income/expenses" → `add_transaction`, `edit_transaction`, `delete_transaction` routes in `app.py`
- "Transaction categorization" → `CATEGORY_EMOJI` dict + category dropdown in `add_edit.html`
- "Monthly expense tracking" → `month_expense` calculation in the `dashboard()` route + Reports page
- "SQL database" → `User` and `Transaction` models (SQLAlchemy ORM → SQLite/MySQL tables) in `app.py`

You can genuinely explain every part of this in an interview because it's simple,
readable Flask code — no hidden magic.

---

## 7. How to Explain the Architecture (quick interview pitch)

1. **Frontend**: Server-rendered HTML templates (Jinja2) styled with custom CSS
   (glassmorphism cards, dark mode via CSS variables) and Chart.js for graphs.
2. **Backend**: Flask handles routing, authentication (hashed passwords + sessions),
   and business logic (streaks, insights, badges are computed in Python).
3. **Database**: SQLAlchemy ORM maps Python classes (`User`, `Transaction`) to SQL
   tables. Works with SQLite out of the box; swappable to MySQL with one line change.
4. **Data flow**: Browser form → Flask route → SQLAlchemy → SQL database → query
   results rendered back into HTML, or returned as JSON for charts (`/api/chart-data`).

---

## 8. Next Steps / Ideas to Extend

- Add PDF export (using `reportlab` or `weasyprint`)
- Add real email-based password reset (using `Flask-Mail`)
- Convert frontend to React for a full SPA experience
- Add recurring transactions (subscriptions, rent)
- Deploy for free on Render/Railway/PythonAnywhere
