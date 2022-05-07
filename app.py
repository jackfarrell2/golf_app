from __future__ import print_function
import sys
from flask import Flask, render_template, request
import sqlite3
import os
from golf import get_scorecards, get_golfers, get_rounds

# Configure application
app = Flask(__name__)

# Configure sqlite3 cursor
con = sqlite3.connect("golf.db", check_same_thread=False)
cur = con.cursor()

@app.route("/")
def homepage():
    return render_template("homepage.html")

@app.route("/vs", methods=["GET", "POST"])
def vs():
    if request.method == "GET":
        # Provide two list's of golfers as options
        golfers = get_golfers()
        return render_template("vs_request.html", golfers=golfers)
    else:
        return render_template("vs_request.html", golfers=golfers)

@app.route("/rounds", methods=["GET", "POST"])
def rounds():
    if request.method == "GET":
        # Provide a list of golfers as options
        golfers = get_golfers()
        return render_template("round_request.html", golfers=golfers)    
    else:
        # Display scorecards for selected golfer
        golfer_name = request.form.get("golfer_name")
        golfers_rounds = get_rounds(golfer_name)
        scorecards = get_scorecards(golfers_rounds, golfer_name)
        return render_template("rounds.html", scorecards=scorecards)


if __name__ == '__main__':
    app.run(debug=True)
    
