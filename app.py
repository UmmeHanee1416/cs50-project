from cs50 import SQL
from flask import Flask, flash, jsonify, render_template, request, redirect, session
from flask_session import Session
# from flask_socketio import SocketIO, emit
from helpers import login_required, apology, lookup, allowed_file, format_date
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, date, timedelta
from flask_apscheduler import APScheduler
import os
import csv
import base64

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
UPLOAD_PROFILE_FOLDER = os.path.join("static", "uploads/profile")

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SECRET_KEY"] = "secret&"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["UPLOAD_PROFILE_FOLDER"] = UPLOAD_PROFILE_FOLDER

Session(app)

# socketio = SocketIO(app)
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

# @socketio.on('connect')
# def on_connect():
#     user_id = get_user_id_somehow()  # e.g., from auth token
#     join_room(f"user_{user_id}")

db = SQL("sqlite:///project.db")

TRANSACTION_TYPE = ["Income", "Expense"]
TRANSACTION_CATEGORY_EXPENSE = ["Education", "Entertainment", "Food",
                                "Grooming", "Medical", "Rent", "Transport", "Utility Bill", "Others"]
TRANSACTION_CATEGORY_INCOME = [
    "Office", "Business", "Freelancing", "Tuition", "Others"]
PERIOD_TYPE = ['Daily', 'Weekly', 'Monthly', 'Yearly']


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = ["no-cache, no-store, must-revalidate"]
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    try:
        income = db.execute(
            "select category, sum(amount) as total from transactions where user_id = ? and type = 'Income' "
            "group by category", session['user_id'])
        expense = db.execute(
            "select category, sum(amount) as total from transactions where user_id = ? and type = 'Expense' "
            "group by category", session['user_id'])
        transactions = db.execute(
            "select * from transactions where user_id = ? order by date desc limit 5", session['user_id'])
        budgets = db.execute(
            "select * from budgets where user_id = ? order by timestamp desc limit 5", session['user_id'])
        budgetsYearly = db.execute(
            "select distinct b.period_type, b.category, b.amount, t.category as trans_category, "
            "t.amount as trans_amount, (t.amount*1.0/b.amount)*100 as percent from budgets b inner join "
            "transactions t on b.user_id = t.user_id and b.category = t.category and b.user_id = ? "
            "and b.period_type = 'Yearly' order by b.amount asc limit 3", session['user_id'])
        user = db.execute(
            "select * from users where id = ?", session['user_id'])
        percent = budgetsYearly[0]['percent'] if budgetsYearly and budgetsYearly[0]['percent'] is not None else 0
        if 90.0 < int(percent) < 100.0:
            message = budgetsYearly[0]['trans_category'] + \
                " Transaction approaching to budget."
            db.execute("insert into notifications (user_id, message, module) values(?, ?, ?)",
                       session['user_id'], message, "Transactions")
            # socketio.emit("new_notification", {
            #               "message": message, "module": "Transactions", "user_id": session['user_id']})
        if int(percent) > 100.0:
            message = budgetsYearly[0]['trans_category'] + \
                " Transaction exceeding over budget."
            db.execute("insert into notifications (user_id, message, module) values(?, ?, ?)",
                       session['user_id'], message, "Transactions")
            # socketio.emit("new_notification", {
            #               "message": message, "module": "Transactions", "user_id": session['user_id']})
    except:
        return apology("error occurred")
    return render_template("core/index.html", income=income, expense=expense, budgets=budgets,
                           budgetsYearly=budgetsYearly, transactions=transactions, user=user)


@app.route("/tracking", methods=['GET', 'POST'])
@login_required
def track():
    progress = 0
    actual_sum = 0
    budget_sum = 0
    actual_row = []
    from_date = ''
    to_date = ''
    if request.method == 'POST':
        type = request.form.get("type")
        category = request.form.get("category")
        fromPeriod = request.form.get("fromPeriod")
        toPeriod = request.form.get("toPeriod")
        fromYear = request.form.get("fromYear")
        toYear = request.form.get("toYear")
        if not type:
            return apology("must provide type")
        if not category:
            return apology("must provide category")
        if category not in TRANSACTION_CATEGORY_EXPENSE:
            return apology("invalid category")
        if not type:
            return apology("must provide type")
        if type not in PERIOD_TYPE:
            return apology("invalid period type")
        if type == 'Weekly' or type == 'Monthly':
            if not fromPeriod:
                return apology("must provide period from")
            if not toPeriod:
                return apology("must provide period to")
            if fromPeriod > toPeriod:
                return apology("period to cannot be earlier than period from")
        if type == 'Yearly':
            if not fromYear:
                return apology("must provide year from")
            if not toYear:
                return apology("must provide year to")
            if fromYear > toYear:
                return apology("year to cannot be earlier than year from")
        if type == 'Weekly':
            from_date = datetime.strptime(fromPeriod + '-1', "%G-W%V-%u")
            to_date = datetime.strptime(toPeriod + '-1', "%G-W%V-%u")
        if type == 'Monthly':
            from_date = datetime.strptime(fromPeriod, "%Y-%m")
            to_date = datetime.strptime(toPeriod, "%Y-%m")
        if type == 'Yearly':
            actual_amount = db.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = 'Expense' AND category = ? AND date BETWEEN ? AND ?",
                                       session['user_id'], category, fromYear, toYear)
            actual_row = db.execute("SELECT * FROM transactions WHERE user_id = ? AND type = 'Expense' AND category = ? AND date BETWEEN ? AND ?",
                                    session['user_id'], category, fromYear, toYear)
            budget_amount = db.execute("SELECT SUM(amount) FROM budgets WHERE user_id = ? AND period_type = ? AND category = ? AND from_period BETWEEN ? AND ?",
                                       session['user_id'], type, category, fromYear, toYear)
        else:
            actual_amount = db.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = 'Expense' AND category = ? AND date BETWEEN ? AND ?",
                                       session['user_id'], category, from_date, to_date)
            actual_row = db.execute("SELECT * FROM transactions WHERE user_id = ? AND type = 'Expense' AND category = ? AND date BETWEEN ? AND ?",
                                    session['user_id'], category, from_date, to_date)
            budget_amount = db.execute("SELECT SUM(amount) FROM budgets WHERE user_id = ? AND period_type = ? AND category = ? AND from_period BETWEEN ? AND ?",
                                       session['user_id'], type, category, fromPeriod, toPeriod)
        actual_sum = actual_amount[0]['SUM(amount)'] or 0
        budget_sum = budget_amount[0]['SUM(amount)'] or 0
        if budget_sum == 0:
            progress = 0
        else:
            progress = (actual_sum / budget_sum) * 100
    return render_template("core/tracking.html", categories=TRANSACTION_CATEGORY_EXPENSE, types=PERIOD_TYPE,
                           progress=progress, actual_sum=actual_sum, budget_sum=budget_sum, actual_row=actual_row)


@app.route("/login", methods=['GET', 'POST'])
def login():
    session.clear()
    if request.method == 'POST':
        name = request.form.get("username")
        password = request.form.get("password")
        if not name:
            return apology("must provide username")
        if not password:
            return apology("must provide password")
        row = db.execute("select * from users where username = ?", name)
        if len(row) != 1 or not check_password_hash(row[0]['hash'], password):
            return apology("invalid username ow password")
        session["user_id"] = row[0]["id"]
        return redirect("/")
    return render_template("security/login.html")


@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get("username")
        password = request.form.get("password")
        confirmPassword = request.form.get("confirmation")
        if not name:
            return apology("must provide name")
        if not password or not confirmPassword:
            return apology("must provide password or confirm password")
        if password != confirmPassword:
            return apology("password and confirm password must be same")
        try:
            hashed = generate_password_hash(password)
            db.execute(
                "insert into users (username, hash) values (?, ?)", name, hashed)
            return redirect("/login")
        except ValueError:
            return apology("username already exist", 500)
        except:
            return apology("error occurred!", 500)
    return render_template("security/register.html")


@app.route("/forgotPass", methods=['POST', 'GET'])
def passReset():
    if request.method == 'POST':
        name = request.form.get("username")
        password = request.form.get("password")
        confirmPassword = request.form.get("confirmPassword")
        if not name or not password or not confirmPassword:
            return apology("must provide all data")
        if password != confirmPassword:
            return apology("password and confirm password must be same")
        row = db.execute("select * from users where username = ?", name)
        if len(row) != 1:
            return apology("data not found", 404)
        try:
            hash = generate_password_hash(password)
            db.execute(
                "update users set hash = ? where username = ?", hash, name)
            message = "Password updated."
            db.execute("insert into notifications (user_id, message, module) values(?, ?, ?)",
                    row[0]['id'], message, "profile")
            # socketio.emit("new_notification", {
            #               "message": message, "module": "profile", "user_id": row[0]['id']})
            return redirect("/login")
        except:
            return apology("error occurred!", 500)
    return render_template("security/password_reset.html")


@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect("/")


@app.route("/saveOrUpdateTransaction", methods=['POST', 'GET'])
@login_required
def saveOrUpdateTransaction():
    user = db.execute("select * from users where id = ?", session["user_id"])
    if request.method == 'POST':
        id = request.form.get("id")
        type = request.form.get("type")
        dateWM = request.form.get("date")
        dateY = request.form.get("dateY")
        date_type = request.form.get("date_type")
        amount = float(request.form.get("amount"))
        category = request.form.get("category")
        description = request.form.get("description")
        userCash = int(user[0]['cash'])
        if not type:
            return apology("must provide transaction type")
        if type not in TRANSACTION_TYPE:
            return apology("invalid transaction type")
        if not amount:
            return apology("must provide amount")
        if type == 'Income':
            userCash += int(amount)
        if type == 'Expense':
            if amount > int(user[0]['cash']):
                return apology("insufficient balance")
            userCash -= int(amount)
        if not category:
            return apology("must provide transaction category")
        if category not in TRANSACTION_CATEGORY_EXPENSE and category not in TRANSACTION_CATEGORY_INCOME:
            return apology("invalid transaction category")
        if not date_type:
            return apology("must provide type")
        if date_type not in PERIOD_TYPE:
            return apology("invalid type")
        if date_type == 'Weekly' or date_type == 'Monthly':
            if not dateWM:
                return apology("must provide week or month")
        if date_type == 'Yearly':
            if not dateY:
                return apology("must provide year")
        if not id:
            try:
                if date_type == 'Yearly':
                    db.execute("insert into transactions (user_id, type, amount, category, date_type, date, description) values (?, ?, ?, ?, ?, ?, ?)",
                               session['user_id'], type, amount, category, date_type, dateY, description)
                else:
                    db.execute("insert into transactions (user_id, type, amount, category, date_type, date, description) values (?, ?, ?, ?, ?, ?, ?)",
                               session['user_id'], type, amount, category, date_type, dateWM, description)
                message = "One transaction added."
                db.execute("insert into notifications (user_id, message, module) values(?, ?, ?)",
                           session['user_id'], message, "Transactions")
                # socketio.emit("new_notification", {
                #               "message": message, "module": "Transactions", "user_id": session['user_id']})
                db.execute("update users set cash = ? where id = ?",
                           userCash, session['user_id'])
                return redirect("/getAllTransactions")
            except:
                return apology("error occurred in add")
        if id:
            try:
                if date_type == 'Yearly':
                    db.execute("update transactions set type = ?, amount = ?, category = ?, date_type = ?, date = ?, description = ? where id = ?",
                               type, amount, category, date_type, dateY, description, id)
                else:
                    db.execute("update transactions set type = ?, amount = ?, category = ?, date_type = ?, date = ?, description = ? where id = ?",
                               type, amount, category, date_type, dateWM, description, id)
                message = "One transaction updated."
                db.execute("insert into notifications (user_id, message, module) values(?, ?, ?)",
                           session['user_id'], message, "Transactions")
                # socketio.emit("new_notification", {
                #               "message": message, "module": "Transactions", "user_id": session['user_id']})
                db.execute("update users set cash = ? where id = ?",
                           userCash, session['user_id'])
                return redirect("/getAllTransactions")
            except:
                return apology("error occurred in update")
    return render_template("transaction/add.html", types=TRANSACTION_TYPE, user=user, period_type=PERIOD_TYPE)


@app.route("/getAllTransactions")
@login_required
def getAllTransactions():
    list = db.execute(
        "select * from transactions where user_id = ? order by timestamp desc", session['user_id'])
    return render_template("transaction/list.html", list=list)


@app.route("/getTransactionById")
@login_required
def getTransactionById():
    id = request.args.get('id')
    transaction = db.execute("select * from transactions where id = ?", id)
    user = db.execute("select * from users where id = ?", session["user_id"])
    if transaction[0]['type'] == 'Income':
        categories = TRANSACTION_CATEGORY_INCOME
    else:
        categories = TRANSACTION_CATEGORY_EXPENSE
    return render_template("transaction/edit.html", transaction=transaction, types=TRANSACTION_TYPE, categories=categories, user=user, period_type=PERIOD_TYPE)


@app.route("/deleteTransaction")
@login_required
def deleteTransaction():
    id = request.args.get("id")
    try:
        db.execute("delete from transactions where id = ?", id)
        message = "One transaction deleted."
        db.execute("insert into notifications (user_id, message, module) values(?, ?, ?)",
                   session['user_id'], message, "Transactions")
        # socketio.emit("new_notification", {
        #               "message": message, "module": "Transactions", "user_id": session['user_id']})
        return redirect("/getAllTransactions")
    except:
        return apology("error occurred in delete")


@app.route("/uploadCsv", methods=['POST', 'GET'])
@login_required
def uploadCsv():
    user = db.execute("select * from users where id = ?", session["user_id"])
    if request.method == 'POST':
        if 'csvFile' not in request.files:
            return apology("must provide file")
        file = request.files['csvFile']
        if file.filename == '' or not allowed_file(file.filename):
            return apology("invalid file")
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        userCash = int(user[0]['cash'])
        with open(filepath, newline='', encoding='utf-8') as csvFile:
            reader = csv.DictReader(csvFile)
            for row in reader:
                try:
                    date_type = row['Date_type'] if row['Date_type'] and row['Date_type'] != "" else 'Daily'
                    date = format_date(row['Date'])
                    description = row['Description']
                    amount = float(row['Amount'].replace(',', ''))
                    category_type = row['Type']
                    category = row['Category']
                    db.execute("insert into transactions (user_id, amount, type, category, description, date_type, date) "
                               "values (?, ?, ?, ?, ?, ?, ?)", session['user_id'], amount, category_type, category, description, date_type, date)
                    if category_type == 'Income':
                        userCash += amount
                    if category_type == 'Expense':
                        userCash -= amount
                except:
                    return apology("error occurred")
            db.execute("update users set cash = ? where id = ?", userCash, session['user_id'])
            message = "Transactions added from file"
            db.execute("insert into notifications (user_id, message, module) values(?, ?, ?)",
                       session['user_id'], message, "Transactions")
    return render_template("transaction/csv_upload.html")


@app.route("/getCategory")
@login_required
def getCategories():
    trType = request.args.get('type')
    if trType == 'Income':
        categories = TRANSACTION_CATEGORY_INCOME
    else:
        categories = TRANSACTION_CATEGORY_EXPENSE
    return jsonify(categories)


@app.route("/saveOrUpdateBudget", methods=['POST', 'GET'])
@login_required
def saveOrUpdateBudget():
    user = db.execute("select * from users where id = ?", session["user_id"])
    if request.method == 'POST':
        id = request.form.get('id')
        amount = request.form.get('amount')
        category = request.form.get('category')
        period_type = request.form.get('period_type')
        fromPeriod = request.form.get('fromPeriod')
        toPeriod = request.form.get('toPeriod')
        fromYear = request.form.get('fromYear')
        toYear = request.form.get('toYear')
        if not amount:
            return apology("must provide amount")
        if not category:
            return apology("must provide category")
        if category not in TRANSACTION_CATEGORY_EXPENSE:
            return apology("invalid category")
        if not period_type:
            return apology("must provide type")
        if period_type not in PERIOD_TYPE:
            return apology("invalid period type")
        if period_type == 'Weekly' or period_type == 'Monthly':
            if not fromPeriod:
                return apology("must provide period from")
            if not toPeriod:
                return apology("must provide period to")
            if fromPeriod > toPeriod:
                return apology("period to cannot be earlier than period from")
        if period_type == 'Yearly':
            if not fromYear:
                return apology("must provide year from")
            if not toYear:
                return apology("must provide year to")
            if fromYear > toYear:
                return apology("year to cannot be earlier than year from")
        if period_type == 'Weekly':
            from_date = datetime.strptime(fromPeriod + '-1', "%G-W%V-%u")
            to_date = datetime.strptime(toPeriod + '-1', "%G-W%V-%u")
            period = (to_date - from_date).days // 7
        if period_type == 'Monthly':
            from_date = datetime.strptime(fromPeriod, "%Y-%m")
            to_date = datetime.strptime(toPeriod, "%Y-%m")
            period = (to_date.year - from_date.year) * \
                12 + (to_date.month - from_date.month)
        if period_type == 'Yearly':
            period = int(toYear) - int(fromYear)
        if not id:
            try:
                if period_type == 'Yearly':
                    db.execute("insert into budgets (user_id, category, period_type, from_period, to_period, period, amount) values(?, ?, ?, ?, ?, ?, ?)",
                               session['user_id'], category, period_type, fromYear, toYear, period, amount)
                else:
                    db.execute("insert into budgets (user_id, category, period_type, from_period, to_period, period, amount) values(?, ?, ?, ?, ?, ?, ?)",
                               session['user_id'], category, period_type, fromPeriod, toPeriod, period, amount)
                message = "One Budget added."
                db.execute("insert into notifications (user_id, message, module) values(?, ?, ?)",
                           session['user_id'], message, "Budgets")
                # socketio.emit("new_notification", {
                #               "message": message, "module": "Budgets", "user_id": session['user_id']})
                return redirect("/getAllBudgets")
            except:
                return apology("error in budget creating")
        if id:
            try:
                if period_type == 'Yearly':
                    db.execute("update budgets set category = ?, period_type = ?, from_period = ?, to_period = ?, period = ?, amount = ? where id = ?",
                               category, period_type, fromYear, toYear, period, amount, id)
                else:
                    db.execute("update budgets set category = ?, period_type = ?, from_period = ?, to_period = ?, period = ?, amount = ? where id = ?",
                               category, period_type, fromPeriod, toPeriod, period, amount, id)
                message = "One budget updated."
                db.execute("insert into notifications (user_id, message, module) values(?, ?, ?)",
                           session['user_id'], message, "Budgets")
                # socketio.emit("new_notification", {
                #               "message": message, "module": "Budgets", "user_id": session['user_id']})
                return redirect("/getAllBudgets")
            except:
                return apology("error in budget updating")
    return render_template("budget/add.html", user=user, categories=TRANSACTION_CATEGORY_EXPENSE, types=PERIOD_TYPE)


@app.route("/getAllBudgets")
@login_required
def getAllBudgets():
    try:
        list = db.execute(
            "select * from budgets where user_id = ? order by timestamp desc", session['user_id'])
    except:
        return apology("error occurred!")
    return render_template("budget/list.html", list=list)


@app.route("/getBudgetById")
@login_required
def getBudgetById():
    id = request.args.get('id')
    budget = db.execute("select * from budgets where id = ?", id)
    user = db.execute("select * from users where id = ?", session["user_id"])
    return render_template("budget/edit.html", budget=budget, categories=TRANSACTION_CATEGORY_EXPENSE,
                           user=user, types=PERIOD_TYPE)


@app.route("/deleteBudget")
@login_required
def deleteBudget():
    id = request.args.get("id")
    try:
        db.execute("delete from budgets where id = ?", id)
        message = "One budget deleted."
        db.execute("insert into notifications (user_id, message, module) values(?, ?, ?)",
                   session['user_id'], message, "Budgets")
        # socketio.emit("new_notification", {
        #               "message": message, "module": "Budgets", "user_id": session['user_id']})
        return redirect("/getAllBudgets")
    except:
        return apology("error occurred in delete")


@app.route("/saveOrUpdateInvestment", methods=['POST', 'GET'])
@login_required
def saveOrUpdateInvestment():
    user = db.execute("select * from users where id = ?", session["user_id"])
    if request.method == 'POST':
        id = request.form.get("id")
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")
        date = request.form.get("date")
        if not symbol:
            return apology("must provide symbol")
        if not shares:
            return apology("must provide shares")
        row = lookup(symbol)
        if not row:
            return apology("symbol not found")
        price = row['price']
        total_price = int(shares)*int(price)
        if not date:
            return apology("must provide purchase date")
        if not id:
            try:
                db.execute("insert into investments (user_id, symbol, shares, price, total_price, purchase_date) "
                           "values (?, ?, ?, ?, ?, ?)", session['user_id'], symbol, shares, price, total_price, date)
                message = "One investment added."
                db.execute("insert into notifications (user_id, message, module) values(?, ?, ?)",
                           session['user_id'], message, "Investments")
                # socketio.emit("new_notification", {
                #               "message": message, "module": "Investments", "user_id": session['user_id']})
                return redirect("/getAllInvestments")
            except:
                return apology("error occurred")
        if id:
            try:
                db.execute("update investments set symbol = ?, shares = ?, price = ?, total_price = ?, purchase_date = ?",
                           symbol, shares, price, total_price, date)
                message = "One investment updated."
                db.execute("insert into notifications (user_id, message, module) values(?, ?, ?)",
                           session['user_id'], message, "Investments")
                # socketio.emit("new_notification", {
                #               "message": message, "module": "Investments", "user_id": session['user_id']})
                return redirect("/getAllInvestments")
            except:
                return apology("error occurred")
    return render_template("investment/add.html", user=user)


@app.route("/symbol", methods=['Post', 'GET'])
@login_required
def symbol():
    symbol = request.form.get("symbol")
    row = []
    if request.method == 'POST':
        if not symbol:
            return apology("must provide symbol")
        row = lookup(symbol)
    return render_template("investment/search.html", row=row)


@app.route("/getAllInvestments")
@login_required
def getAllInvestments():
    rows = db.execute(
        "select * from investments where user_id = ? order by timestamp desc", session['user_id'])
    return render_template("investment/list.html", rows=rows)


@app.route("/getInvestmentById")
@login_required
def getInvestmentById():
    id = request.args.get('id')
    investment = db.execute("select * from investments where id = ?", id)
    user = db.execute("select * from users where id = ?", session["user_id"])
    return render_template("investment/edit.html", investment=investment, categories=TRANSACTION_CATEGORY_EXPENSE,
                           user=user, types=PERIOD_TYPE)


@app.route("/deleteInvestment")
@login_required
def deleteInvestment():
    id = request.args.get("id")
    try:
        db.execute("delete from investments where id = ?", id)
        message = "One investment deleted."
        db.execute("insert into notifications (user_id, message, module) values(?, ?, ?)",
                   session['user_id'], message, "Investments")
        # socketio.emit("new_notification", {
        #               "message": message, "module": "Investments", "user_id": session['user_id']})
        return redirect("/getAllInvestments")
    except:
        return apology("error occurred in delete")


@app.route("/getNotifications")
@login_required
def getNotifications():
    notifications = db.execute("select * from notifications where user_id = ? "
                               "order by timestamp desc", session['user_id'])
    return jsonify(notifications)


@app.route("/markReadNotification")
@login_required
def readNotification():
    id = request.args.get("id")
    try:
        db.execute("update notifications set read = ? where id = ?", 1, id)
    except:
        return apology("error occurred")
    return jsonify({"status": 200})


@app.route("/saveOrUpdateRecursion", methods=['POST', 'GET'])
@login_required
def saveOrUpdateRecursion():
    user = db.execute(
        "select * from users where id = ?", session['user_id'])
    if request.method == 'POST':
        id = request.form.get("id")
        type = request.form.get("type")
        category = request.form.get("category")
        amount = request.form.get("amount")
        start_date = request.form.get("start_date")
        frequency = request.form.get("frequency")
        frequency_count = request.form.get("frequency_count")
        next_due = request.form.get("next_due")
        end_date = request.form.get("end_date")
        description = request.form.get("description")
        auto_apply = request.form.get("auto_apply")
        if not type:
            return apology("must provide transaction type")
        if type not in TRANSACTION_TYPE:
            return apology("invalid transaction type")
        if not category:
            return apology("must provide category")
        if category not in TRANSACTION_CATEGORY_EXPENSE and category not in TRANSACTION_CATEGORY_INCOME:
            return apology("invalid transaction category")
        if not amount:
            return apology("must provide amount")
        if not start_date:
            return apology("must provide start date")
        if not frequency:
            return apology("must provide frequency")
        if frequency not in PERIOD_TYPE:
            return apology("invalid frequency")
        if not frequency_count:
            return apology("must provide frequency count")
        apply = 1 if auto_apply == 'on' else 0
        try:
            if not id:
                db.execute("insert into recurring_transaction (user_id, type, category, amount, start_date, "
                           "frequency, frequency_count, next_due, end_date, auto_apply, last_process, description) values "
                           "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", session[
                               'user_id'], type, category, amount, start_date,
                           frequency, frequency_count, next_due, end_date, apply, start_date, description)
                message = "One Periodic Transaction Added."
                db.execute("insert into notifications (user_id, message, module) values(?, ?, ?)",
                           session['user_id'], message, "Recursions")
                # socketio.emit("new_notification", {
                #               "message": message, "module": "Investments", "user_id": session['user_id']})
            if id:
                db.execute("update recurring_transaction set user_id = ?, type = ?, category = ?, amount = ?, start_date = ?, "
                           "frequency = ?, frequency_count = ?, next_due = ?, end_date = ?, auto_apply=  ?, last_process = ?, description = ? "
                           "where id = ?", session['user_id'], type, category, amount, start_date,
                           frequency, frequency_count, next_due, end_date, apply, start_date, description, id)
                message = "One Periodic Transaction Updated."
                db.execute("insert into notifications (user_id, message, module) values(?, ?, ?)",
                           session['user_id'], message, "Recursions")
                # socketio.emit("new_notification", {
                #               "message": message, "module": "Investments", "user_id": session['user_id']})
            return redirect("/getAllRecursions")
        except:
            return apology("error occurred!")
    return render_template("recursive_transaction/add.html", types=TRANSACTION_TYPE,
                           period_type=PERIOD_TYPE, user=user)


@app.route("/getAllRecursions")
@login_required
def getAllRecursions():
    try:
        transactions = db.execute(
            "select * from recurring_transaction where user_id = ? order by timestamp desc", session['user_id'])
    except:
        return apology("error occurred")
    return render_template("recursive_transaction/list.html", list=transactions)


@app.route("/getRecursionById")
@login_required
def getRecursionById():
    id = request.args.get('id')
    transaction = db.execute(
        "select * from recurring_transaction where id = ?", id)
    user = db.execute("select * from users where id = ?", session["user_id"])
    if transaction[0]['type'] == 'Income':
        categories = TRANSACTION_CATEGORY_INCOME
    else:
        categories = TRANSACTION_CATEGORY_EXPENSE
    return render_template("recursive_transaction/edit.html", transaction=transaction, types=TRANSACTION_TYPE,
                           period_type=PERIOD_TYPE, user=user, categories=categories)


@app.route("/deleteRecursion")
@login_required
def deleteRecursion():
    id = request.args.get("id")
    try:
        db.execute("delete from recurring_transaction where id = ?", id)
        message = "One investment deleted."
        db.execute("insert into notifications (user_id, message, module) values(?, ?, ?)",
                   session['user_id'], message, "Recursions")
        # socketio.emit("new_notification", {
        #               "message": message, "module": "Recursions", "user_id": session['user_id']})
        return redirect("/getAllRecursions")
    except:
        return apology("error occurred in delete")


@app.route("/profile", methods=['POST', 'GET'])
@login_required
def profile():
    user = db.execute("select * from users where id = ?", session['user_id'])
    year = str(datetime.now().year)
    income = db.execute("SELECT sum(amount) FROM transactions WHERE type = 'Income'  AND ((length(date) = 10 "
                        "AND substr(date, 1, 4) = ?) OR (length(date) = 7  AND substr(date, 1, 4) = ?) OR (length(date) = 7  "
                        "AND substr(date, 1, 4) = ?) OR (length(date) = 4 AND substr(date, 1, 4) = ?)) and user_id = ?", year, year, year, year, session['user_id'])
    expense = db.execute("SELECT sum(amount) FROM transactions WHERE type = 'Expense'  AND ((length(date) = 10 "
                         "AND substr(date, 1, 4) = ?) OR (length(date) = 7  AND substr(date, 1, 4) = ?) OR (length(date) = 7  "
                         "AND substr(date, 1, 4) = ?) OR (length(date) = 4 AND substr(date, 1, 4) = ?)) and user_id = ?", year, year, year, year, session['user_id'])
    if request.method == 'POST':
        name = request.form.get("prUsername")
        mail = request.form.get("prEmail")
        contact = request.form.get("prContact_no")
        image = request.files['prImage']
        filename = secure_filename(image.filename)
        filepath = os.path.join(app.config['UPLOAD_PROFILE_FOLDER'], filename)
        image.save(filepath)
        if not name:
            return apology("must provide name")
        try:
            db.execute("update users set username = ?, email = ?, contact_no = ?, images = ? where id = ?",
                        name, mail, contact, f"/{filepath}", session['user_id'])
            message = "Profile Updated."
            db.execute("insert into notifications (user_id, message, module) values(?, ?, ?)",
                        session['user_id'], message, "profile")
            return redirect("/profile")
        except:
            return apology("error occurred")
    return render_template("core/profile.html", user=user, income=income, expense=expense)


@app.route("/passwordReset", methods=['POST'])
@login_required
def passwordReset():
        # data = request.get_json()
        curr = request.form.get("curr")
        newPass = request.form.get("newPass")
        newCon = request.form.get("newCon")
        row = db.execute("select * from users where id  = ?", session['user_id'])
        if not check_password_hash(row[0]['hash'], curr):
            return apology("incorrect information")
        if newPass != newCon:
            return apology("passwords don't match")
        try:
            db.execute("update users set hash = ? where id = ?",
                        generate_password_hash(newPass), session['user_id'])
            message = "Password changed."
            db.execute("insert into notifications (user_id, message, module) values(?, ?, ?)",
                    row[0]['id'], message, "profile")
            return redirect("/profile")
        except:
            return apology("error occurred")


def automateTransaction():
    with app.app_context():
        today = date.today()
        users = db.execute("SELECT id FROM users")
        for u in users:
            u_id = u['id']
            user = db.execute("SELECT * FROM users WHERE id = ?", u_id)
            transactions = db.execute(
                "SELECT * FROM recurring_transaction WHERE user_id = ?", u_id
            )
            for transaction in transactions:
                try:
                    dt = datetime.strptime(
                        transaction['next_due'], "%Y-%m-%d").date()
                    if dt <= today:
                        type_ = transaction['type']
                        amount = float(transaction['amount'])
                        category = transaction['category']
                        frequency = transaction['frequency']
                        description = transaction['description']
                        if frequency == 'Yearly':
                            date_val = str(dt.year)
                        elif frequency == 'Monthly':
                            date_val = dt.strftime("%Y-%m")
                        else:
                            date_val = f"{dt.isocalendar().year}-W{dt.isocalendar().week:02d}"
                        db.execute("""
                            INSERT INTO transactions
                            (user_id, type, amount, category, date_type, date, description)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, u_id, type_, amount, category, frequency, date_val, description)
                        db.execute("""
                            INSERT INTO notifications (user_id, message, module)
                            VALUES (?, ?, ?)
                        """, u_id, "One transaction added from periodic transaction.", "Transactions")
                        userCash = float(user[0]['cash'])
                        if type_ == 'Income':
                            userCash += amount
                        elif type_ == 'Expense':
                            userCash -= amount
                        db.execute(
                            "UPDATE users SET cash = ? WHERE id = ?", userCash, u_id)
                        if frequency == 'Yearly':
                            new_due = date(dt.year + 1, dt.month, dt.day)
                        elif frequency == 'Monthly':
                            month = dt.month + 1 if dt.month < 12 else 1
                            year = dt.year if dt.month < 12 else dt.year + 1
                            day = min(dt.day, 28)
                            new_due = date(year, month, day)
                        elif frequency == 'Weekly':
                            new_due = dt + timedelta(weeks=1)
                        db.execute("""
                            UPDATE recurring_transaction
                            SET next_due = ?, last_process = ?
                            WHERE id = ?
                        """, new_due.isoformat(), today, transaction['id'])
                except Exception as e:
                    print(
                        f"Error processing transaction {transaction['id']}: {e}")


scheduler.add_job(id="apply_requrring",
                  func=automateTransaction, trigger='interval', hours=24)


# if __name__ == "__main__":
#     socketio.run(app, debug=True)
