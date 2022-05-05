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
    # Create lists of the round information to be passed into the template
    rounds = []
        
    # Query rounds
    round_query = cur.execute("SELECT * FROM rounds WHERE golfer_id = (?)", (1,))
    
    for round in round_query:
        name_query = cur.execute("SELECT name from golfers WHERE id = (?)", (1,))
        golfer_name = name_query.fetchall()[0][0]
        course_query = cur.execute("SELECT name FROM courses WHERE id = (?)", (round[2],))
        course_name = course_query.fetchall()[0][0]
        hole_query = cur.execute("SELECT * FROM holes WHERE course_id = (?) ORDER BY hole_number", (round[2],))
        holes = hole_query.fetchall()
        rounds.append({"golfer_name": golfer_name, "course_name": course_name, "round_date": round[3], "one": round[4], "two": round[5], "three": round[6], "four": round[7], 
                      "five": round[8], "six": round[9], "seven": round[10], "eight": round[11], "nine": round[12], "ten": round[13], "eleven": round[14], "twelve": round[15], 
                      "thirteen": round[16], "fourteen": round[17], "fifteen": round[18], "sixteen": round[19], "seventeen": round[20], "eighteen": round[21],
                      "one_yard": holes[0][4], "two_yard": holes[1][4], "three_yard": holes[2][4], "four_yard": holes[3][4], "five_yard": holes[4][4],
                      "six_yard": holes[5][4], "seven_yard": holes[6][4], "eight_yard": holes[7][4], "nine_yard": holes[8][4], "ten_yard": holes[9][4],
                      "eleven_yard": holes[10][4], "twelve_yard": holes[11][4], "thirteen_yard": holes[12][4], "fourteen_yard": holes [13][4], "fifteen_yard": holes[14][4],
                      "sixteen_yard": holes[15][4], "seventeen_yard": holes[16][4], "eighteen_yard": holes[17][4], "one_handicap": holes[0][5], "two_handicap": holes[1][5], 
                      "three_handicap": holes[2][5], "four_handicap": holes[3][5], "five_handicap": holes[4][5], "six_handicap": holes[5][5], "seven_handicap": holes[6][5],
                      "eight_handicap": holes[7][5], "nine_handicap": holes[8][5], "ten_handicap": holes[9][5], "eleven_handicap": holes[10][5], 
                      "twelve_handicap": holes[11][5], "thirteen_handicap": holes[12][5], "fourteen_handicap": holes[13][5], "fifteen_handicap": holes[14][5], 
                        "sixteen_handicap": holes[15][5], "seventeen_handicap": holes[16][5], "eighteen_handicap": holes[17][5], "one_par": holes[0][3], "two_par": holes[1][3],
                       "three_par": holes[2][3], "four_par": holes[3][3], "five_par": holes[4][3], "six_par": holes[5][3], "seven_par": holes[6][3],
                       "eight_par": holes[7][3], "nine_par": holes[8][3], "ten_par": holes[9][3], "eleven_par": holes[10][3], "twelve_par": holes[11][3], 
                       "thirteen_par": holes[12][3], "fourteen_par": holes[13][3], "fifteen_par": holes[14][3], "sixteen_par": holes[15][3], 
                       "seventeen_par": holes[16][3], "eighteen_par": holes[17][3]})

    return render_template("rounds.html", rounds=rounds)