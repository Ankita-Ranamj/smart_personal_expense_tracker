"""
Smart Personal Expense Tracker
------------------------------
A beginner-friendly but feature-rich Flask + SQL web app.

Run:
    pip install -r requirements.txt
    python app.py

Then open http://127.0.0.1:5000 in your browser.
"""

import os
import csv
import io
from datetime import date, datetime, timedelta

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify, Response
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# ---------------------------------------------------------------------
# APP SETUP
# ---------------------------------------------------------------------
app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-secret-key"

basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "expense_tracker.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

CATEGORY_EMOJI = {
    "Food": "🍕", "Shopping": "🛒", "Travel": "✈️", "Bills": "⚡",
    "Education": "📚", "Health": "❤️", "Entertainment": "🎬", "Other": "🗂️"
}
INCOME_SOURCES = ["Salary", "Pocket Money", "Freelance", "Scholarship", "Others"]

# ---------------------------------------------------------------------
# DATABASE MODELS  (this is our SQL schema, defined in Python)
# ---------------------------------------------------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    currency = db.Column(db.String(10), default="₹")
    daily_limit = db.Column(db.Float, default=0)
    savings_goal_name = db.Column(db.String(120), default="")
    savings_goal_amount = db.Column(db.Float, default=0)
    savings_saved = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    transactions = db.relationship("Transaction", backref="user", lazy=True, cascade="all, delete")


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    type = db.Column(db.String(10), nullable=False)   # 'income' or 'expense'
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    note = db.Column(db.String(200))
    txn_date = db.Column(db.Date, nullable=False, default=date.today)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------
def current_user():
    uid = session.get("user_id")
    return User.query.get(uid) if uid else None


def login_required(view):
    from functools import wraps
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def emoji_for(category):
    return CATEGORY_EMOJI.get(category, "🗂️")


# ---------------------------------------------------------------------
# AUTH ROUTES
# ---------------------------------------------------------------------
@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "error")
            return redirect(url_for("signup"))

        user = User(name=name, email=email,
                    password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        flash("Account created! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            flash(f"Welcome back, {user.name}!", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "error")

    return render_template("login.html")


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    # Simplified: lets the user reset password directly (no email server needed)
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        new_password = request.form["new_password"]
        user = User.query.filter_by(email=email).first()
        if user:
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            flash("Password updated. Please log in.", "success")
            return redirect(url_for("login"))
        flash("No account found with that email.", "error")
    return render_template("forgot_password.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    today = date.today()
    month_start = today.replace(day=1)

    txns = Transaction.query.filter_by(user_id=user.id).order_by(Transaction.txn_date.desc()).all()

    today_expense = sum(t.amount for t in txns if t.type == "expense" and t.txn_date == today)
    month_expense = sum(t.amount for t in txns if t.type == "expense" and t.txn_date >= month_start)
    month_income = sum(t.amount for t in txns if t.type == "income" and t.txn_date >= month_start)
    total_income = sum(t.amount for t in txns if t.type == "income")
    total_expense = sum(t.amount for t in txns if t.type == "expense")
    balance = total_income - total_expense

    recent = txns[:8]

    # --- Streak: consecutive days (ending today) where spend <= daily_limit
    streak = 0
    if user.daily_limit and user.daily_limit > 0:
        day_cursor = today
        while True:
            day_total = sum(t.amount for t in txns if t.type == "expense" and t.txn_date == day_cursor)
            if day_cursor == today and day_total == 0 and streak == 0:
                # today not over yet; still count if within limit (0 <= limit)
                pass
            if day_total <= user.daily_limit:
                streak += 1
                day_cursor -= timedelta(days=1)
            else:
                break
            if streak > 365:
                break

    # --- Badges
    badges = []
    if streak >= 7:
        badges.append(("🔥", "Budget Master", f"{streak}-day streak under budget"))
    if user.savings_goal_amount and user.savings_saved >= user.savings_goal_amount > 0:
        badges.append(("🎯", "Goal Achiever", "Reached your savings goal"))
    if balance > 0 and total_income > 0 and (balance / total_income) >= 0.2:
        badges.append(("💰", "Saving Hero", "Saved 20%+ of your income"))

    # --- AI-style insight (rule-based, no external API needed)
    insight = generate_insight(user.id)

    # --- Daily limit warning
    limit_warning = None
    if user.daily_limit and today_expense > user.daily_limit:
        over = today_expense - user.daily_limit
        limit_warning = f"⚠ You've exceeded today's ₹{user.daily_limit:.0f} limit by {user.currency}{over:.0f}."

    goal_progress = 0
    if user.savings_goal_amount and user.savings_goal_amount > 0:
        goal_progress = min(100, round((user.savings_saved / user.savings_goal_amount) * 100))

    return render_template(
        "dashboard.html",
        user=user,
        today_expense=today_expense,
        month_expense=month_expense,
        month_income=month_income,
        balance=balance,
        recent=recent,
        emoji_for=emoji_for,
        streak=streak,
        badges=badges,
        insight=insight,
        limit_warning=limit_warning,
        goal_progress=goal_progress,
    )


def generate_insight(user_id):
    """A simple rule-based 'AI-style' spending insight (no external API needed)."""
    today = date.today()
    this_month_start = today.replace(day=1)
    last_month_end = this_month_start - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)

    this_month = Transaction.query.filter(
        Transaction.user_id == user_id, Transaction.type == "expense",
        Transaction.txn_date >= this_month_start
    ).all()
    last_month = Transaction.query.filter(
        Transaction.user_id == user_id, Transaction.type == "expense",
        Transaction.txn_date >= last_month_start, Transaction.txn_date <= last_month_end
    ).all()

    def totals_by_category(txns):
        d = {}
        for t in txns:
            d[t.category] = d.get(t.category, 0) + t.amount
        return d

    this_totals = totals_by_category(this_month)
    last_totals = totals_by_category(last_month)

    if not this_totals:
        return "Add a few transactions to see personalized spending insights here."

    best_cat, best_pct = None, 0
    for cat, amt in this_totals.items():
        prev = last_totals.get(cat, 0)
        if prev > 0:
            pct = ((amt - prev) / prev) * 100
            if pct > best_pct:
                best_pct, best_cat = pct, cat

    if best_cat and best_pct > 10:
        return (f"You spent {best_pct:.0f}% more on {best_cat} {emoji_for(best_cat)} this month "
                f"compared to last month. Try trimming it by 15% to stay on track.")

    top_cat = max(this_totals, key=this_totals.get)
    return f"Your top spending category this month is {top_cat} {emoji_for(top_cat)}. Keep an eye on it!"


# ---------------------------------------------------------------------
# EXPENSE / INCOME CRUD
# ---------------------------------------------------------------------
@app.route("/transactions")
@login_required
def transactions():
    user = current_user()
    q = Transaction.query.filter_by(user_id=user.id)

    search = request.args.get("search", "").strip()
    category = request.args.get("category", "")
    ttype = request.args.get("type", "")
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")

    if search:
        q = q.filter(Transaction.note.ilike(f"%{search}%"))
    if category:
        q = q.filter(Transaction.category == category)
    if ttype:
        q = q.filter(Transaction.type == ttype)
    if date_from:
        q = q.filter(Transaction.txn_date >= datetime.strptime(date_from, "%Y-%m-%d").date())
    if date_to:
        q = q.filter(Transaction.txn_date <= datetime.strptime(date_to, "%Y-%m-%d").date())

    txns = q.order_by(Transaction.txn_date.desc()).all()
    categories = list(CATEGORY_EMOJI.keys())

    return render_template("transactions.html", txns=txns, emoji_for=emoji_for,
                            categories=categories, income_sources=INCOME_SOURCES,
                            user=user)


@app.route("/add", methods=["GET", "POST"])
@login_required
def add_transaction():
    user = current_user()
    if request.method == "POST":
        ttype = request.form["type"]
        category = request.form["category"]
        amount = float(request.form["amount"])
        note = request.form.get("note", "")
        txn_date = datetime.strptime(request.form["txn_date"], "%Y-%m-%d").date()

        txn = Transaction(user_id=user.id, type=ttype, category=category,
                           amount=amount, note=note, txn_date=txn_date)
        db.session.add(txn)

        if ttype == "income":
            # count part of new income automatically toward savings tracker (simple rule)
            pass
        db.session.commit()
        flash("Transaction added!", "success")
        return redirect(url_for("dashboard"))

    categories = list(CATEGORY_EMOJI.keys())
    return render_template("add_edit.html", txn=None, categories=categories,
                            income_sources=INCOME_SOURCES, today=date.today().isoformat())


@app.route("/edit/<int:txn_id>", methods=["GET", "POST"])
@login_required
def edit_transaction(txn_id):
    user = current_user()
    txn = Transaction.query.filter_by(id=txn_id, user_id=user.id).first_or_404()

    if request.method == "POST":
        txn.type = request.form["type"]
        txn.category = request.form["category"]
        txn.amount = float(request.form["amount"])
        txn.note = request.form.get("note", "")
        txn.txn_date = datetime.strptime(request.form["txn_date"], "%Y-%m-%d").date()
        db.session.commit()
        flash("Transaction updated!", "success")
        return redirect(url_for("transactions"))

    categories = list(CATEGORY_EMOJI.keys())
    return render_template("add_edit.html", txn=txn, categories=categories,
                            income_sources=INCOME_SOURCES, today=txn.txn_date.isoformat())


@app.route("/delete/<int:txn_id>", methods=["POST"])
@login_required
def delete_transaction(txn_id):
    user = current_user()
    txn = Transaction.query.filter_by(id=txn_id, user_id=user.id).first_or_404()
    db.session.delete(txn)
    db.session.commit()
    flash("Transaction deleted.", "success")
    return redirect(url_for("transactions"))


# ---------------------------------------------------------------------
# CHART DATA (JSON APIs consumed by Chart.js)
# ---------------------------------------------------------------------
@app.route("/api/chart-data")
@login_required
def chart_data():
    user = current_user()
    txns = Transaction.query.filter_by(user_id=user.id).all()

    # Pie: expense by category
    pie = {}
    for t in txns:
        if t.type == "expense":
            pie[t.category] = pie.get(t.category, 0) + t.amount

    # Bar: last 6 months expense totals
    months = []
    bar_values = []
    today = date.today()
    cursor = today.replace(day=1)
    month_list = []
    for i in range(5, -1, -1):
        y, mo = cursor.year, cursor.month - i
        while mo <= 0:
            mo += 12
            y -= 1
        month_list.append((y, mo))
    for y, mo in month_list:
        total = sum(t.amount for t in txns if t.type == "expense" and t.txn_date.year == y and t.txn_date.month == mo)
        months.append(f"{mo:02d}/{y}")
        bar_values.append(total)

    # Weekly trend: last 7 days
    week_labels, week_values = [], []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        total = sum(t.amount for t in txns if t.type == "expense" and t.txn_date == d)
        week_labels.append(d.strftime("%a"))
        week_values.append(total)

    total_income = sum(t.amount for t in txns if t.type == "income")
    total_expense = sum(t.amount for t in txns if t.type == "expense")

    return jsonify({
        "pie_labels": list(pie.keys()),
        "pie_values": list(pie.values()),
        "bar_labels": months,
        "bar_values": bar_values,
        "week_labels": week_labels,
        "week_values": week_values,
        "income_vs_expense": {"income": total_income, "expense": total_expense},
    })


# ---------------------------------------------------------------------
# REPORTS
# ---------------------------------------------------------------------
@app.route("/reports")
@login_required
def reports():
    user = current_user()
    txns = Transaction.query.filter_by(user_id=user.id).all()

    by_cat = {}
    for t in txns:
        if t.type == "expense":
            by_cat[t.category] = by_cat.get(t.category, 0) + t.amount
    top_category = max(by_cat, key=by_cat.get) if by_cat else None

    today = date.today()
    month_start = today.replace(day=1)
    year_start = today.replace(month=1, day=1)

    monthly_expense = sum(t.amount for t in txns if t.type == "expense" and t.txn_date >= month_start)
    monthly_income = sum(t.amount for t in txns if t.type == "income" and t.txn_date >= month_start)
    yearly_expense = sum(t.amount for t in txns if t.type == "expense" and t.txn_date >= year_start)
    yearly_income = sum(t.amount for t in txns if t.type == "income" and t.txn_date >= year_start)

    return render_template("reports.html", user=user, top_category=top_category,
                            emoji_for=emoji_for, by_cat=by_cat,
                            monthly_expense=monthly_expense, monthly_income=monthly_income,
                            yearly_expense=yearly_expense, yearly_income=yearly_income)


# ---------------------------------------------------------------------
# EXPORT
# ---------------------------------------------------------------------
@app.route("/export/csv")
@login_required
def export_csv():
    user = current_user()
    txns = Transaction.query.filter_by(user_id=user.id).order_by(Transaction.txn_date.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Type", "Category", "Amount", "Note"])
    for t in txns:
        writer.writerow([t.txn_date, t.type, t.category, t.amount, t.note or ""])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions.csv"}
    )


# ---------------------------------------------------------------------
# CALENDAR VIEW
# ---------------------------------------------------------------------
@app.route("/calendar")
@login_required
def calendar_view():
    user = current_user()
    txns = Transaction.query.filter_by(user_id=user.id).all()
    by_date = {}
    for t in txns:
        key = t.txn_date.isoformat()
        by_date.setdefault(key, []).append(t)
    totals_by_date = {k: sum(t.amount for t in v if t.type == "expense") for k, v in by_date.items()}
    return render_template("calendar.html", totals_by_date=totals_by_date, user=user)


@app.route("/api/day/<day>")
@login_required
def day_transactions(day):
    user = current_user()
    d = datetime.strptime(day, "%Y-%m-%d").date()
    txns = Transaction.query.filter_by(user_id=user.id, txn_date=d).all()
    return jsonify([
        {"type": t.type, "category": t.category, "amount": t.amount,
         "note": t.note, "emoji": emoji_for(t.category)}
        for t in txns
    ])


# ---------------------------------------------------------------------
# SETTINGS / PROFILE
# ---------------------------------------------------------------------
@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    user = current_user()
    if request.method == "POST":
        user.name = request.form.get("name", user.name)
        user.currency = request.form.get("currency", user.currency)
        user.daily_limit = float(request.form.get("daily_limit") or 0)
        user.savings_goal_name = request.form.get("savings_goal_name", "")
        user.savings_goal_amount = float(request.form.get("savings_goal_amount") or 0)
        user.savings_saved = float(request.form.get("savings_saved") or 0)
        db.session.commit()
        flash("Settings updated!", "success")
        return redirect(url_for("settings"))
    return render_template("settings.html", user=user)


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
