from cs50 import SQL
from flask import Flask, render_template
from flask_session import Session
from helpers import login_required

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///project.db")

@app.after_request
def after_request(response):
    response.headers["Cache-Control"]=["no-cache, no-store, must-revalidate"]
    response.headers["Expires"] = 0
    # response.headres["Pragma"] = "no-cache"
    return response

@app.route("/")
# @login_required
def index():
    return render_template("index.html")
