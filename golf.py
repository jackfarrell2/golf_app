import sqlite3

con = sqlite3.connect("golf.db", check_same_thread=False)
cur = con.cursor()

def par_shift(score:int) -> str:
    """Turns a stroke count to a readable score"""
    if score == 0:
        return ("E")
    elif score > 0:
        return ("+{}".format(score))
    else:
        return str(score)

def get_golfers() -> list:
    """Returns all golfers names"""
    con = sqlite3.connect("golf.db", check_same_thread=False)
    cur = con.cursor()
    golfers = []
    golfer_query = cur.execute("SELECT name FROM golfers ORDER BY name")
    golfer_query = golfer_query.fetchall()
    for golfer in golfer_query:
        golfers.append({"golfer_name": golfer[0]})
    return golfers

def get_rounds(golfer:str) -> list: 
    """Returns all rounds golfer has played"""
    rounds = []
    id_query = cur.execute("SELECT id FROM golfers WHERE name = (?)", (golfer,))
    id_query = id_query.fetchone()[0]
    round_query = cur.execute("SELECT * FROM rounds WHERE golfer_id = (?) ORDER BY id DESC", (id_query,))
    rounds = round_query.fetchall()
    return rounds

def get_holes(course:tuple) -> list:
    """Returns all the hole information for a course"""
    hole_query = cur.execute("SELECT * FROM holes WHERE course_id = (?) ORDER BY hole_number", (course[2],))
    holes = hole_query.fetchall()
    return holes

def get_course_info(course:tuple) -> list:
    """Returns information about a given course"""
    course_query = cur.execute("SELECT * FROM courses WHERE id = (?)", (course[2],))
    course_info = course_query.fetchall()
    return course_info

def get_yardages(course_info:list, holes:list) -> list:
    """Returns yardages for a course's holes"""
    yardages = []
    for i in range(len(holes)):
        yardages.append(holes[i][4])
    yardages.append(sum(yardages))
    yardages.insert(9, sum(yardages[:9]))
    yardages.insert(19, sum(yardages[10:19]))
    yardages.insert(0, course_info[0][14])
    return yardages

def get_handicaps(course:list) -> list:
    """Reuturns the handicaps of a given course"""
    handicaps = []
    for i in range(len(course)):
        handicaps.append(course[i][5])
    return handicaps

def get_strokes(round:tuple, golfer:str) -> list:
    """Returns a players strokes on a given round"""
    strokes = []
    for i in range(18):
        strokes.append(round[i + 4])
    strokes.append(sum(strokes))
    strokes.insert(9, sum(strokes[:9]))
    strokes.insert(19, sum(strokes[10:19]))
    strokes.insert(0, golfer)
    return strokes

def get_pars(holes:list) -> list:
    """Returns the pars for a given course"""
    pars = []
    for i in range(18):
        pars.append(holes[i][3])
    pars.insert(9, sum(pars[:9]))
    pars.append(sum(pars[10:19]))
    pars.append(pars[9])
    return pars

def get_to_pars(strokes:list, pars:list) -> list:
    """Returns a players scores as a relation to par for each hole"""
    par_tracker = 0
    to_par_front = []
    to_par_back = []
    for i in range(9):
        to_this_par = strokes[i + 1] - pars[i]
        if to_this_par == 0:  # If the par_count should remain unchanged
            to_par_front.append(par_shift(par_tracker))
        else:  # If the par_count should increase or decrease
            par_tracker += to_this_par
            to_par_front.append(par_shift(par_tracker))
    to_par_front.append(par_shift(par_tracker))
    par_tracker = 0
    for i in range(9):
        to_this_par = strokes[i + 11] - pars[i + 10]
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
    return to_par_front

def get_scorecards(rounds:list, golfer_name:str) -> list:
    """Returns scorecards for a given golfer"""
    scorecards = []
    for round in rounds:
        course_info = get_course_info(round)
        holes = get_holes(round)
        course_info = get_course_info(round)
        holes = get_holes(round)
        yardages = get_yardages(course_info, holes)  # Populate yardages
        handicaps = get_handicaps(holes)  # Populate handicaps
        strokes = get_strokes(round, golfer_name)  # Populate strokes
        pars = get_pars(holes)  # Populate pars
        to_pars = get_to_pars(strokes, pars)  # Populate to pars
        scorecard = {"yardages": yardages, "handicaps": handicaps, "strokes": strokes, "pars": pars, "to_pars": to_pars, "course_name": course_info[0][1],
                        "round_date": round[3]}
        scorecards.append(scorecard)
    return scorecards


    
    
