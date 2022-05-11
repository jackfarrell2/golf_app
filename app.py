from __future__ import print_function
import sys
from flask import Flask, render_template, request
from datetime import datetime
import sqlite3
import os
from golf import get_scorecards, get_golfers, get_rounds, get_stats, get_vs_rounds, get_record, get_vs_scorecards, get_courses, get_course_info, get_yardages, get_handicaps, get_holes, get_pars, get_strokes, get_to_pars

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
        # Print the two users statistics
        all_golfer_stats = []
        golfer_one_name = request.form.get("golfer_one_name")
        golfer_two_name = request.form.get("golfer_two_name")
        if golfer_one_name == golfer_two_name: return render_template("apology.html", message="Can't Compare The Same Golfer") # Ensure different golfer
        else:
            # Gets golfers stats for only mutual matches
            golfer_one_rounds = get_vs_rounds(golfer_one_name, golfer_two_name)
            stats = get_stats(golfer_one_rounds, golfer_one_name)
            all_golfer_stats.append(stats)
            golfer_two_rounds = get_vs_rounds(golfer_two_name, golfer_one_name)
            stats = get_stats(golfer_two_rounds, golfer_two_name)
            all_golfer_stats.append(stats)
            
            # Gets current record between the two golfers
            record = get_record(golfer_one_rounds, golfer_two_rounds, golfer_one_name, golfer_two_name)

            # Gets scorecards for each match
            scorecards = get_vs_scorecards(golfer_one_rounds, golfer_two_rounds, golfer_one_name, golfer_two_name)
        return render_template("vs.html", record=record, all_golfer_stats=all_golfer_stats, scorecards=scorecards)


@app.route("/post", methods=["GET", "POST"])
def post():
    if request.method == "GET":
        # Display a list of options for courses and number of golfers
        courses = get_courses()
        return render_template("post_request.html", courses=courses)
    else:
        # Get default date for input
        now = datetime.now()
        date = now.strftime("%Y-%m-%d")
        golfer_amount = int(request.form.get("number_of_golfers"))
        course_name = request.form.get("course_name")
        golfers = get_golfers()
        single_round = get_one_round(course_name)
        scorecard = get_post_scorecard(single_round)
        return render_template("post.html", date=date, scorecard=scorecard, golfer_amount=golfer_amount, golfers=golfers)

@app.route("/posted", methods=["POST"])
def posted():
    # Create id for this match
    match_id = get_match_id()
    
    # Get course_id 
    course_name = request.form.get("course_name")
    course_id = get_course_id(course_name)

    # Get match date
    round_date = request.form.get("round_date")

    # Create a list of golfers entered
    golfer_one = request.form.get("golfer_name_1")
    golfer_two = request.form.get("golfer_name_2")
    golfer_three = request.form.get("golfer_name_3")
    golfer_four = request.form.get("golfer_name_4") 
    golfers = [golfer_one, golfer_two, golfer_three, golfer_four]
    for i in range(len(golfers)):
        if golfers[i] == None: 
            golfers = golfers[:i]
            break   
    golfer_scores = []
    for i in range(len(golfers)):
        scores = [0] * 18
        for j in range(len(scores)):
            golfer_temp = "golfer_"+ str(i + 1) +"_"+ str(j + 1)
            scores[j] = request.form.get(golfer_temp) 
        golfer_scores.append(scores)
    
    for i, golfer in enumerate(golfers):
        golfer_id = get_golfer_id(golfer)
        golfer_scores[i] = [str(golfer_id), str(course_id), round_date] + golfer_scores[i] + [str(match_id)]
    
    for i in range(len(golfers)):
        commit_round(golfer_scores[i])

    return render_template("homepage.html")

def commit_round(golfer_round):
    statement = "INSERT INTO rounds (golfer_id, course_id, date, one, two, three, four, five, six, seven, eight, nine, ten, eleven, twelve, thirteen, fourteen, fifteen, sixteen, seventeen, eighteen, match_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)" 
    params = golfer_round
    cur.execute(statement, params)
    con.commit()

def get_golfer_id(golfer):
    golfer_id_query = cur.execute("SELECT id FROM golfers WHERE name = (?)", (golfer, ))
    golfer_id = golfer_id_query.fetchone()[0]
    return golfer_id

def get_course_id(course):
    course_id_query = cur.execute("SELECT id FROM courses WHERE name = (?)", (course, ))
    course_id = course_id_query.fetchone()[0]
    return course_id


def get_match_id():
    match_id_query = cur.execute("SELECT MAX(match_id) FROM rounds")
    match_id = match_id_query.fetchone()[0]
    match_id += 1
    return match_id

def get_post_scorecard(matches):
    for match in matches:
        course_info = get_course_info(match)
        holes = get_holes(match)
        yardages = get_yardages(course_info, holes)
        handicaps = get_handicaps(holes)
        pars = get_pars(holes) 
        scorecard = {"yardages": yardages, "handicaps": handicaps, "pars": pars, "course_name": course_info[0][1]}
        return scorecard


def get_scorecards(matches: list, golfer_name: str) -> list:
    """Returns scorecards for a given golfer"""
    scorecards = []
    for match in matches:
        course_info = get_course_info(match)
        holes = get_holes(match)
        yardages = get_yardages(course_info, holes)  # Populate yardages
        handicaps = get_handicaps(holes)  # Populate handicaps
        strokes = get_strokes(match, golfer_name)  # Populate strokes
        pars = get_pars(holes)  # Populate pars
        to_pars = get_to_pars(strokes, pars)  # Populate to pars
        scorecard = {"yardages": yardages, "handicaps": handicaps, "strokes": strokes, "pars": pars, "to_pars": to_pars, "course_name": course_info[0][1],
                     "round_date": match[3]}
        scorecards.append(scorecard)
    return scorecards

def get_one_round(course_name):
    rounds = []
    course_query = cur.execute("SELECT * FROM courses WHERE name = (?)", (course_name,))
    course_id = course_query.fetchone()[0]
    one_round_query = cur.execute("SELECT * FROM rounds WHERE course_id = (?)", (course_id,))
    one_round = one_round_query.fetchall()
    return one_round



    


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

@app.route("/holes", methods=["GET", "POST"])
def holes():
    if request.method == "GET":
        # Display a list of options for golfers and courses
        golfers = get_golfers()
        courses = get_courses()
        return render_template("holes_request.html", golfers=golfers, courses=courses)
    else: 
        golfer_name = request.form.get("golfer_name")
        course_name = request.form.get("course_name")
        course_rounds = get_course_rounds(golfer_name, course_name)
        current_holes_sum = [0] * 18
        avg_scores = [0] * 18
        course_copy = tuple(course_rounds[0][:4])
        for round in course_rounds:
            round = round[4:22]
            for i in range(len(round)):
                current_holes_sum[i] += round[i]
        for i in range(len(avg_scores)):
            avg_scores[i] = current_holes_sum[i] / len(course_rounds)
        avg_scores.append(1)
        finalized_round = [course_copy + tuple(avg_scores)]
        scorecards = get_scorecards(finalized_round, golfer_name)
        return render_template("holes.html", scorecards=scorecards)


def get_course_rounds(golfer, course):
    """Returns rounds at a given course for a given golfer"""
    rounds = []
    id_query = cur.execute("SELECT id FROM golfers WHERE name = (?)", (golfer,))
    id_query = id_query.fetchone()[0]
    course_id_query = cur.execute("SELECT id from courses WHERE name = (?)", (course,))
    course_id_query = course_id_query.fetchone()[0]
    params = [id_query, course_id_query]
    statement = "SELECT * FROM rounds WHERE golfer_id = ? AND course_id = ? ORDER BY id DESC"
    round_query = cur.execute(statement, params)
    rounds = round_query.fetchall()
    return rounds

if __name__ == '__main__':
    app.run(debug=True)
    
