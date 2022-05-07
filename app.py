from __future__ import print_function
import sys
from flask import Flask, render_template, request
import sqlite3
import os
from golf_functions import par_shift

# Configure application
app = Flask(__name__)

# Configure sqlite3 cursor
con = sqlite3.connect("golf.db", check_same_thread=False)
cur = con.cursor()

@app.route("/")
def homepage():
    return render_template("homepage.html")

@app.route("/rounds", methods=["GET", "POST"])
def rounds():
    if request.method == "GET":
        
        # Provide a list of golfers as options
        golfers = []
        golfer_query = cur.execute("SELECT name FROM golfers ORDER BY name")
        golfer_query = golfer_query.fetchall()
        for golfer in golfer_query:
            golfers.append({"golfer_name": golfer[0]})
        return render_template("round_request.html", golfers=golfers)

    else:
        
        # Create lists of the round information to be passed into the template
        rounds = []
        golfer_name = request.form.get("golfer_name") # Retrieve selected golfer & get their id
        id_query = cur.execute("SELECT id FROM golfers WHERE name = (?)", (golfer_name,))
        id_query = id_query.fetchone()[0]
        
        # Grab all rounds played
        round_query = cur.execute("SELECT * FROM rounds WHERE golfer_id = (?) ORDER BY id DESC", (id_query,))
        round_query = round_query.fetchall()
        for round in round_query:
            course_query = cur.execute("SELECT * FROM courses WHERE id = (?)", (round[2],))
            course_info = course_query.fetchall()
            hole_query = cur.execute("SELECT * FROM holes WHERE course_id = (?) ORDER BY hole_number", (round[2],))
            holes = hole_query.fetchall()
            
            # Create yardage list to populate the yardages on each scorecard
            yardages = []
            for i in range(len(holes)):
                yardages.append(holes[i][4])
            yardages.insert(0, course_info[0][14])
            yardages.insert(10, course_info[0][8])
            yardages.append(course_info[0][9])
            yardages.append(course_info[0][10])
            
            # Create handicap list to populate the handicaps on each scorecard
            handicaps = []
            for i in range(len(holes)):
                handicaps.append(holes[i][5])

            # Create a scores list to populate the scores on each scorecard
            scores = []
            for i in range(len(holes)):
                scores.append(round[i+4])
            scores.insert(0, golfer_name)
            front, back = 0, 0
            for i in range(9):
                front += round[i+4]
                back += round[i+13]
            total = front + back
            scores.insert(10, front)
            scores.append(back)
            scores.append(total)        
            
            #Create a pars lists to populate the pars on each scorecard
            pars = []
            for i in range(len(holes)):
                pars.append(holes[i][3])
            pars.insert(9, course_info[0][11])
            pars.append(course_info[0][12])
            pars.append(course_info[0][13])

            # Create a to_par list to populate players relation to par on each scorecard
            par_tracker = 0
            to_par_front = []
            to_par_back = []
            for i in range(9):
                to_this_par = scores[i + 1] - pars[i]
                if to_this_par == 0: # If the par_count should remain unchanged
                    to_par_front.append(par_shift(par_tracker))
                else: # If the par_count should increase or decrease
                    par_tracker += to_this_par
                    to_par_front.append(par_shift(par_tracker))
            to_par_front.append(par_shift(par_tracker))
            par_tracker = 0
            for i in range(9):
                to_this_par = scores[i + 11] - pars[i + 10]
                if to_this_par == 0:  # If the par_count should remain unchanged
                    if par_tracker == 0:
                        to_par_back.append(par_shift(par_tracker))
                    else:
                        to_par_back.append(par_shift(par_tracker))
                else:  # If the par_count should increase or decrease
                    par_tracker += to_this_par
                    to_par_back.append(par_shift(par_tracker))
            to_par_back.append(par_shift(par_tracker))
            to_par_front.extend(to_par_back)
            total_to_par = int(to_par_front[9]) + int(to_par_front[19])
            to_par_front.append(par_shift(total_to_par))
            print(scores, file=sys.stderr)

            rounds.append({"yardages": yardages, "handicaps": handicaps, "scores": scores, "pars": pars, "to_par": to_par_front, "course_name": course_info[0][1], "round_date": round[3]})
        return render_template("rounds.html", rounds=rounds)
    
if __name__ == '__main__':
    app.run(debug=True)
    
