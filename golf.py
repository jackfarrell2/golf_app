import sqlite3
import itertools

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

def par_shift_reverse(score:str) -> int:
    """Turns a readable score to a stroke count"""
    if score == "E":
        return 0
    elif score[0] == "+":
        return int(score[1:])
    else:
        return int(score)

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

def get_vs_rounds(golfer_one: str, golfer_two:str) -> list:
    """Returns all rounds golfer one has played in a match vs golfer two"""
    rounds = []
    golfer_one_query = cur.execute("SELECT id FROM golfers WHERE name = (?)", (golfer_one,))
    golfer_one_query = golfer_one_query.fetchone()[0]
    golfer_two_query = cur.execute("SELECT id FROM golfers WHERE name = (?)", (golfer_two,))
    golfer_two_query = golfer_two_query.fetchone()[0]
    # round_query = cur.execute("SELECT * FROM (SELECT * FROM rounds WHERE match_id IN (SELECT match_id FROM rounds GROUP BY match_id HAVING COUNT (*) > 1) AND golfer_id = (?) OR golfer_id = (?)) as a WHERE golfer_id = (?)", (golfer_one, golfer_one, golfer_two,))
    statement = "SELECT * FROM (SELECT * FROM rounds WHERE match_id IN (SELECT match_id FROM rounds GROUP BY match_id HAVING COUNT (*) > 1) AND golfer_id = ? OR golfer_id = ?) as a WHERE golfer_id = ?"
    params = [golfer_one_query, golfer_two_query, golfer_one_query]
    round_query = cur.execute(statement, params)
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

def get_scorecards(matches:list, golfer_name:str) -> list:
    """Returns scorecards for a given golfer"""
    scorecards = []
    for match in matches:
        course_info = get_course_info(match)
        holes = get_holes(match)
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

def get_stats(rounds:list, golfer:str) -> list:
    """Returns all current statistics for a given golfer"""
    to_par_counter = 0 # Track the lifetime to-par score to output a score that can be adjusted for par 72
    best_score_checker = 200 # To check if a round should replace golfers current best score
    made_counts = [0, 0, 0, 0, 0, 0, 0] # How many llifetime eagles to maxes made in that order
    pars_played = [0, 0, 0] # How many lifetime par 3's to par 5's played
    pars_strokes = [0, 0, 0] # How many total strokes on each type of par beginning with par 3
    
    # Update players stats for each round played
    for match in rounds:
        # Get round information
        holes = get_holes(match) 
        strokes = get_strokes(match, golfer)
        pars = get_pars(holes)
        to_pars = get_to_pars(strokes, pars)
        mades = count_mades(strokes, pars)

        to_par_counter += par_shift_reverse(to_pars[-1]) # Update lifetime to par score
        if to_par_counter < best_score_checker: best_score_checker = to_par_counter # Update best round
        for count, made in enumerate(made_counts): made_counts[count] += mades[count + 1] # Update lifetimes eagles to maxes in that order
        
        # Calculate lifetime scores on each type of par
        strokes = strokes[1:10] + strokes[11:20]
        pars = pars[:9] + pars[10:19]
        for count, par in enumerate(pars):
            if par == 3:
                pars_played[0] += 1
                pars_strokes[0] += strokes[count]
            elif par == 4:
                pars_played[1] += 1
                pars_strokes[1] += strokes[count]
            else:
                pars_played[2] += 1
                pars_strokes[2] += strokes[count]
    
    # Pass results back        
    par_three_avg = round(pars_strokes[0] / pars_played[0], 2)   
    par_four_avg = round(pars_strokes[1] / pars_played[1], 2)
    par_five_avg = round(pars_strokes[2] / pars_played[2], 2)
    avg_par = to_par_counter / len(rounds)
    avg_score = round(avg_par + 72)
    avg_par = avg_score - 72
    best_score_checker = "{} ({})".format(par_shift(best_score_checker), best_score_checker + 72)
    avg_makes = [round(made / len(rounds), 2) for made in made_counts]
    stats = [golfer, avg_score, par_shift(avg_par), best_score_checker] + avg_makes[1:] + [par_three_avg, par_four_avg, par_five_avg, made_counts[1]]
    return stats

def count_mades(strokes:list, pars:list) -> list:
    """Returns a list of how many albatrosses - maxes are made in that order"""
    made_counter = [0, 0, 0, 0, 0, 0, 0, 0] # How many albatrosses - maxes made in that order
    strokes = strokes[1:10] + strokes[11:20]
    pars = pars[:9] + pars[10:19]
    for par, stroke in enumerate(strokes):
        if stroke - pars[par] == -3: made_counter[0] += 1
        if stroke - pars[par] == -2: made_counter[1] += 1
        if stroke - pars[par] == -1: made_counter[2] += 1
        if stroke - pars[par] == 0: made_counter[3] += 1
        if stroke - pars[par] == 1: made_counter[4] += 1
        if stroke - pars[par] == 2: made_counter[5] += 1
        if stroke - pars[par] == 3: made_counter[6] += 1
        if stroke - pars[par] == 4: made_counter[7] += 1
    return made_counter        


def apology(message, code=400):
    """Render message as an apology to user."""
    return render_template("apology.html", code=code, message=message),
    
    
