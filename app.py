from flask import Flask, render_template
import sqlite3

# Configure application
app = Flask(__name__)

# Configure sqlite3 cursor
con = sqlite3.connect("golf.db")
cur = con.cursor()

@app.route("/")
def homepage():
    return render_template("homepage.html")

@app.route("/rounds")
def rounds():
    # Create a list of the round information to be passed into the template
    rounds = []
    for row in cur.execute("SELECT * FROM rounds WHERE user_id = 1"):
        # To Do
    return render_template("rounds.html", rounds=rounds)