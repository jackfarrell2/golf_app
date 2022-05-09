from __future__ import print_function
import sys
from flask import Flask, render_template, request
import sqlite3
import os
from golf import get_scorecards, get_golfers, get_rounds, get_stats, apology

# Configure application
app = Flask(__name__)

# Configure sqlite3 cursor
con = sqlite3.connect("golf.db", check_same_thread=False)
cur = con.cursor()

@app.route("/")
def homepage():
    # Display statistics for all golfers
    all_golfer_stats = []
    golfers = get_golfers()
    for golfer in golfers:
        golfer_name = golfer['golfer_name']
        golfers_rounds = get_rounds(golfer_name)
        if len(golfers_rounds) >= 1: 
            stats = get_stats(golfers_rounds, golfer_name)
            all_golfer_stats.append(stats)
    return render_template("homepage.html", all_golfer_stats=all_golfer_stats)


@app.route("/vs", methods=["GET", "POST"])
def vs():
    if request.method == "GET":
        # Provide two list's of golfers as options
        golfers = get_golfers()
        return render_template("vs_request.html", golfers=golfers)
    else:
        all_golfer_stats = []
        golfer_one_name = request.form.get("golfer_one_name")
        golfer_two_name = request.form.get("golfer_two_name")
        if golfer_one_name == golfer_two_name : return render_template("apology.html", message="Can't Compare The Same Golfer")
            
        golfers = [{'golfer_name':golfer_one_name}, {'golfer_name': golfer_two_name}]
        for golfer in golfers:
            golfer_name = golfer['golfer_name']
            golfers_rounds = get_rounds(golfer_name)
            if len(golfers_rounds) >= 1:
                stats = get_stats(golfers_rounds, golfer_name)
                all_golfer_stats.append(stats)
        return render_template("homepage.html", all_golfer_stats=all_golfer_stats)

@app.route("/rounds", methods=["GET", "POST"])
@app.route("/rounds/<golfer_name>", methods=["GET", "POST"])
def rounds(golfer_name="lampsha"):
    if request.method == "POST":
        # Display scorecards for selected golfer
        golfer_name = request.form.get("golfer_name")
        golfers_rounds = get_rounds(golfer_name)
        scorecards = get_scorecards(golfers_rounds, golfer_name)
        return render_template("rounds.html", scorecards=scorecards)
    else:
        golfers = get_golfers()
        for golfer in golfers:
            if golfer['golfer_name'] == golfer_name:
                golfers_rounds = get_rounds(golfer_name)
                scorecards = get_scorecards(golfers_rounds, golfer_name)
                return render_template("rounds.html", scorecards=scorecards)  
        else:
            return render_template("round_request.html", golfers=golfers)


if __name__ == '__main__':
    app.run(debug=True)
    
