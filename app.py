from __future__ import print_function
import sys
from flask import Flask, render_template
import sqlite3
import os

# Configure application
app = Flask(__name__)

# Configure sqlite3 cursor
con = sqlite3.connect("golf.db", check_same_thread=False)
cur = con.cursor()

@app.route("/")
def homepage():
    return render_template("homepage.html")

@app.route("/rounds")
def rounds():
    # Create a list of the round information to be passed into the template
    rounds = []

    # Query rounds
    round_query = cur.execute("SELECT * FROM rounds WHERE golfer_id = (?)", (1,))
    for round in round_query:
        course_query = cur.execute("SELECT name FROM courses WHERE id = (?)", (round[2],))
        course_name = course_query.fetchall()[0][0]
        round_date = round[3]
        one = round[4]
        two = round[5]
        three = round[6]
        four = round[7]
        five = round[8]
        six = round[9]
        seven = round[10]
        eight = round[11]
        nine = round[12]
        ten = round[13]
        eleven = round[14]
        twelve = round[15]
        thirteen = round[16]
        fourteen = round[17]
        fifteen = round[18]
        sixteen = round[19]
        seventeen = round[20]
        eighteen = round[21]
        rounds.append({"course_name": course_name, "round_date": round_date, "one": one, "two": two, "three": three, "four": four, "five": five, "six": six, "seven": seven, "eight": eight, "nine": nine, "ten": ten, "eleven": eleven, "twelve": twelve, "thirteen": thirteen, "fourteen":fourteen, "fifteen": fifteen, "sixteen": sixteen, "seventeen": seventeen, "eighteen": eighteen})

    return render_template("rounds.html", rounds=rounds)