import requests
from flask import redirect, render_template, session
from functools import wraps
from datetime import datetime

ALLOWED_EXT = {'csv', 'xlsx'}

formats = [
    "%Y-%m-%d",   # 2020-08-20
    "%d-%b-%Y",   # 20-Aug-2020
    "%d/%m/%Y",   # 20/08/2020
    "%m/%d/%Y",   # 08/20/2020 (US style)
    "%d-%m-%Y",   # 20-08-2020
    "%d-%b-%y",   # 20-Aug-20
]

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def apology(message, code=400):
    def escape(s):
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s
    return render_template("core/error.html", top=code, bottom=escape(message)), code


def lookup(symbol):
    """Look up quote for symbol."""
    url = f"https://finance.cs50.io/quote?symbol={symbol.upper()}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        quote_data = response.json()
        return {
            "name": quote_data["companyName"],
            "price": quote_data["latestPrice"],
            "symbol": symbol.upper()
        }
    except requests.RequestException as e:
        print(f"Request error: {e}")
    except (KeyError, ValueError) as e:
        print(f"Data parsing error: {e}")
    return None


def allowed_file(name):
    return '.' in name and name.rsplit('.', 1)[1].lower() in ALLOWED_EXT

def format_date(date):
    for fmt in formats:
        try:
            return datetime.strptime(date.strip(), fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unsupported date format: {date_str}")
