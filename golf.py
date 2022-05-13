import sqlite3

# Configure SQL connection
con = sqlite3.connect("golf.db", check_same_thread=False)
cur = con.cursor()


def par_shift(score: int) -> str:
    """Turns a stroke count to a readable score"""
    if score == 0:
        return ("E")
    elif score > 0:
        score = round(score)
        return ("+{}".format(score))
    else:
        return str(score)


def par_shift_reverse(score: str) -> int:
    """Turns a readable score to a stroke count"""
    if score == "E":
        return 0
    elif score[0] == "+":
        return int(score[1:])
    else:
        return int(score)


def get_golfers() -> list:
    """Returns all golfers names"""
    golfers = []
    golfer_query = cur.execute("SELECT name FROM golfers ORDER BY name")
    golfer_query = golfer_query.fetchall()
    for golfer in golfer_query:
        golfers.append({"golfer_name": golfer[0]})
    return golfers


def get_courses() -> list:
    """Returns all golfers names"""
    courses = []
    course_query = cur.execute("SELECT name FROM courses ORDER BY name")
    course_query = course_query.fetchall()
    for course in course_query:
        courses.append({"course_name": course[0]})
    return courses


def get_rounds(golfer: str) -> list:
    """Returns all rounds golfer has played"""
    rounds = []
    # Get golfers id
    statement = "SELECT id FROM golfers WHERE name = (?)"
    params = [golfer]
    id_query = cur.execute(statement, params)
    id_query = id_query.fetchone()[0]
    # Get that golfers rounds
    statement = "SELECT * FROM rounds WHERE golfer_id = (?) ORDER BY date DESC"
    params = [id_query]
    round_query = cur.execute(statement, params)
    rounds = round_query.fetchall()
    return rounds


def get_vs_rounds(golfer_one: str, golfer_two: str) -> list:
    """Returns all rounds golfer one has played in a match vs golfer two"""
    rounds = []
    golfer_one_query = cur.execute("SELECT id FROM golfers WHERE name = (?)",
                                   (golfer_one,))
    golfer_one_query = golfer_one_query.fetchone()[0]
    golfer_two_query = cur.execute("SELECT id FROM golfers WHERE name = (?)",
                                   (golfer_two,))
    golfer_two_query = golfer_two_query.fetchone()[0]
    statement = "SELECT * FROM (SELECT * FROM rounds WHERE match_id IN" \
                "(SELECT match_id FROM (SELECT * FROM rounds WHERE golfer_id" \
                "= ? OR golfer_id = ?) as a GROUP BY match_id HAVING COUNT" \
                "(*) > 1) AND golfer_id = ? OR golfer_id = ?) as b WHERE " \
                "golfer_id = ? ORDER BY date DESC"
    params = [golfer_one_query, golfer_two_query, golfer_one_query,
              golfer_two_query, golfer_one_query]
    round_query = cur.execute(statement, params)
    rounds = round_query.fetchall()
    return rounds


def get_holes(course: tuple) -> list:
    """Returns all the hole information for a course"""
    hole_query = cur.execute("SELECT * FROM holes WHERE course_id = (?) "
                             "ORDER BY hole_number", (course[2],))
    holes = hole_query.fetchall()
    return holes


def get_course_info(course: tuple) -> list:
    """Returns information about a given course"""
    course_query = cur.execute("SELECT * FROM courses WHERE id = (?)",
                               (course[2],))
    course_info = course_query.fetchall()
    return course_info


def get_yardages(course_info: list, holes: list) -> list:
    """Returns yardages for a course's holes"""
    yardages = []
    for i in range(len(holes)):
        yardages.append(holes[i][4])
    yardages.append(sum(yardages))
    yardages.insert(9, sum(yardages[:9]))
    yardages.insert(19, sum(yardages[10:19]))
    yardages.insert(0, course_info[0][14])
    return yardages


def get_handicaps(course: list) -> list:
    """Reuturns the handicaps of a given course"""
    handicaps = []
    for i in range(len(course)):
        handicaps.append(course[i][5])
    return handicaps


def get_strokes(match: tuple, golfer: str) -> list:
    """Returns a players strokes on a given round"""
    strokes = []
    for i in range(18):
        strokes.append(match[i + 4])
    strokes.append(round(sum(strokes), 1))
    strokes.insert(9, round(sum(strokes[:9]), 1))
    strokes.insert(19, round(sum(strokes[10:19]), 1))
    strokes.insert(0, golfer)
    return strokes


def get_pars(holes: list) -> list:
    """Returns the pars for a given course"""
    pars = []
    for i in range(18):
        pars.append(holes[i][3])
    pars.insert(9, sum(pars[:9]))
    pars.append(sum(pars[10:19]))
    pars.append(pars[9])
    return pars


def get_to_pars(strokes: list, pars: list) -> list:
    """Returns a players scores as a relation to par for each hole"""
    par_tracker = 0
    to_par_front = []
    to_par_back = []
    for i in range(9):
        to_this_par = round(strokes[i + 1] - pars[i], 2)
        # If the par_count should remain unchanged
        if to_this_par == 0:
            to_par_front.append(par_shift(par_tracker))
        # If the par_count should increase or decrease
        else:
            par_tracker += to_this_par
            to_par_front.append(par_shift(par_tracker))
    to_par_front.append(par_shift(par_tracker))
    par_tracker = 0
    for i in range(9):
        to_this_par = round(strokes[i + 11] - pars[i + 10], 2)
        # If the par_count should remain unchanged
        if to_this_par == 0:
            if par_tracker == 0:
                to_par_back.append(par_shift(par_tracker))
            else:
                to_par_back.append(par_shift(par_tracker))
        # If the par_count should increase or decrease
        else:
            par_tracker += to_this_par
            to_par_back.append(par_shift(par_tracker))
    to_par_back.append(par_shift(par_tracker))
    to_par_front.extend(to_par_back)
    total_to_par = (int(par_shift_reverse(to_par_front[9])) +
                    int(par_shift_reverse(to_par_front[19])))
    to_par_front.append(par_shift(total_to_par))
    return to_par_front


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
        scorecard = {"yardages": yardages, "handicaps": handicaps,
                     "strokes": strokes, "pars": pars,
                     "to_pars": to_pars, "course_name": course_info[0][1],
                     "round_date": match[3]}
        scorecards.append(scorecard)
    return scorecards


def get_stats(rounds: list, golfer: str) -> list:
    """Returns all current statistics for a given golfer"""
    to_par_counter = 0  # Track the lifetime to-par score
    best_score_checker = 200  # Track lifetime best score
    made_counts = [0, 0, 0, 0, 0, 0, 0]  # Lifetime eagles to maxes
    pars_played = [0, 0, 0]  # Lifetime par 3's to par 5's plated
    pars_strokes = [0, 0, 0]  # Lifetime strokes on each type of par
    # Update players stats for each round played
    for match in rounds:
        # Get round information
        holes = get_holes(match)
        strokes = get_strokes(match, golfer)
        pars = get_pars(holes)
        to_pars = get_to_pars(strokes, pars)
        mades = count_mades(strokes, pars)
        # Update lifetime to par score
        to_par_counter += par_shift_reverse(to_pars[-1])
        # Update best round
        if to_par_counter < best_score_checker:
            best_score_checker = to_par_counter
        # Update lifetimes eagles to maxes in that order
        for count, made in enumerate(made_counts):
            made_counts[count] += mades[count + 1]
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
    best_score_checker = "{} ({})".format(par_shift(best_score_checker),
                                          best_score_checker + 72)
    avg_makes = [round(made / len(rounds), 2) for made in made_counts]
    stats = ([golfer, avg_score, par_shift(avg_par), best_score_checker] +
             avg_makes[1:] + [par_three_avg, par_four_avg, par_five_avg,
             made_counts[0]])
    return stats


def count_mades(strokes: list, pars: list) -> list:
    """Gets a list of how many albatrosses - maxes are made in that order"""
    # How many albatrosses - maxes made in that order
    made_counter = [0, 0, 0, 0, 0, 0, 0, 0]
    strokes = strokes[1:10] + strokes[11:20]
    pars = pars[:9] + pars[10:19]
    for par, stroke in enumerate(strokes):
        if stroke - pars[par] == -3:
            made_counter[0] += 1
        if stroke - pars[par] == -2:
            made_counter[1] += 1
        if stroke - pars[par] == -1:
            made_counter[2] += 1
        if stroke - pars[par] == 0:
            made_counter[3] += 1
        if stroke - pars[par] == 1:
            made_counter[4] += 1
        if stroke - pars[par] == 2:
            made_counter[5] += 1
        if stroke - pars[par] == 3:
            made_counter[6] += 1
        if stroke - pars[par] == 4:
            made_counter[7] += 1
    return made_counter


def get_record(golfer_one_rounds: list, golfer_two_rounds: list,
               golfer_one_name: str, golfer_two_name: str) -> str:
    """Returns a record between two golfers given rounds"""
    record = {"golfer_one_wins": 0, "golfer_two_wins": 0, "draws": 0}
    for i in range(len(golfer_one_rounds)):
        # Update running record
        if sum(golfer_one_rounds[i][4:23]) < sum(golfer_two_rounds[i][4:23]):
            record["golfer_one_wins"] += 1
        elif sum(golfer_two_rounds[i][4:23]) < sum(golfer_one_rounds[i][4:23]):
            record["golfer_two_wins"] += 1
        else:
            record["draws"] += 1
    # Format a string depending on the record
    if record["golfer_one_wins"] > record["golfer_two_wins"]:
        record = "{} is {}-{}-{}".format(golfer_one_name,
                                         record["golfer_one_wins"],
                                         record["golfer_two_wins"],
                                         record["draws"])
    elif record["golfer_two_wins"] > record["golfer_one_wins"]:
        record = "{} is {}-{}-{}".format(golfer_two_name,
                                         record["golfer_two_wins"],
                                         record["golfer_one_wins"],
                                         record["draws"])
    else:
        record = "It is tied {}-{}-{}".format(record["golfer_two_wins"],
                                              record["golfer_one_wins"],
                                              record["draws"])
    return record


def get_vs_scorecards(golfer_one_rounds: list, golfer_two_rounds: list,
                      golfer_one_name: str, golfer_two_name: str) -> list:
    """Returns match scorecards for a given pair of golfers"""
    scorecards = []
    for i in range(len(golfer_one_rounds)):
        course_info = get_course_info(golfer_one_rounds[i])
        holes = get_holes(golfer_one_rounds[i])
        course_info = get_course_info(golfer_one_rounds[i])
        holes = get_holes(golfer_one_rounds[i])
        yardages = get_yardages(course_info, holes)  # Populate yardages
        handicaps = get_handicaps(holes)  # Populate handicaps
        # Populate golfer one strokes
        one_strokes = get_strokes(golfer_one_rounds[i], golfer_one_name)
        # Populate golfer two strokes
        two_strokes = get_strokes(golfer_two_rounds[i], golfer_two_name)
        pars = get_pars(holes)  # Populate pars
        # Populate golfer one to pars
        one_to_pars = get_to_pars(one_strokes, pars)
        # Populate golfer two to pars
        two_to_pars = get_to_pars(two_strokes, pars)
        scorecard = {"yardages": yardages, "handicaps": handicaps,
                     "one_strokes": one_strokes, "two_strokes": two_strokes,
                     "pars": pars, "one_to_pars": one_to_pars,
                     "two_to_pars": two_to_pars,
                     "course_name": course_info[0][1],
                     "round_date": golfer_one_rounds[i][3]}
        scorecards.append(scorecard)
    return scorecards


def commit_course(course: str, rating: str, slope: str, city: str, state: str,
                  yardages: list, handicaps: list, pars: list) -> None:
    """Adds a course to the database"""
    # Strip parts of the course info that matter for the courses db table
    par = pars[-1]
    yards = yardages[-1]
    front = yardages[9]
    back = yardages[-2]
    total = yardages[-1]
    par_front = pars[9]
    par_back = pars[-2]
    par_total = pars[-1]
    tees = "White"  # Default white tees
    # Add the course to the courses table
    statement = "INSERT INTO courses (name, par, rating, slope, yards, " \
                "city, state, front, back, total, par_front, par_back, " \
                "par_total, tees) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, " \
                "?, ?, ?, ?)"
    params = [course, par, rating, slope, yards, city, state,
              front, back, total, par_front, par_back, par_total, tees]
    cur.execute(statement, params)
    con.commit()

    # Add the course's holes to the holes table
    course_id = get_course_id(course)
    # Strip the hole data that matters for the holes db table
    yardages = yardages[:9] + yardages[10:-2]
    pars = pars[:9] + pars[10:-2]
    # Update holes table
    for i in range(18):
        statement = "INSERT INTO holes (course_id, hole_number, par, " \
                    "yardage, handicap) VALUES (?, ?, ?, ?, ?)"
        params = [course_id, i + 1, pars[i], yardages[i], handicaps[i]]
        cur.execute(statement, params)
        con.commit()

    # Add dummy round (for creating scorecards before a round has been played)
    statement = "INSERT INTO rounds (golfer_id, course_id, date, one, two, " \
                "three, four, five, six, seven, eight, nine, ten, eleven, " \
                "twelve, thirteen, fourteen, fifteen, sixteen, seventeen, " \
                "eighteen, match_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, " \
                "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    empty_strokes = [0] * 18  # Dummy strokes
    # Golfer_id = -1 so we can filter the rounds out if needed elsewhere
    params = [-1, course_id, "2020-01-01"] + empty_strokes + [-1]
    cur.execute(statement, params)
    con.commit()


def get_course_rounds(golfer: str, course: str) -> list:
    """Returns rounds at a given course for a given golfer"""
    rounds = []
    id_query = cur.execute(
        "SELECT id FROM golfers WHERE name = (?)", (golfer,))
    id_query = id_query.fetchone()[0]
    course_id_query = cur.execute(
        "SELECT id from courses WHERE name = (?)", (course,))
    course_id_query = course_id_query.fetchone()[0]
    params = [id_query, course_id_query]
    statement = "SELECT * FROM rounds WHERE golfer_id = ? " \
                "AND course_id = ? ORDER BY id DESC"
    round_query = cur.execute(statement, params)
    rounds = round_query.fetchall()
    return rounds


def get_course_rounds(golfer: str, course: str) -> list:
    """Returns rounds at a given course for a given golfer"""
    rounds = []
    id_query = cur.execute(
        "SELECT id FROM golfers WHERE name = (?)", (golfer,))
    id_query = id_query.fetchone()[0]
    course_id_query = cur.execute(
        "SELECT id from courses WHERE name = (?)", (course,))
    course_id_query = course_id_query.fetchone()[0]
    params = [id_query, course_id_query]
    statement = "SELECT * FROM rounds WHERE golfer_id = ? " \
                "AND course_id = ? ORDER BY id DESC"
    round_query = cur.execute(statement, params)
    rounds = round_query.fetchall()
    return rounds


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
        scorecard = {"yardages": yardages, "handicaps": handicaps,
                     "strokes": strokes, "pars": pars, "to_pars": to_pars,
                     "course_name": course_info[0][1],
                     "round_date": match[3]}
        scorecards.append(scorecard)
    return scorecards


def get_post_scorecard(matches: list) -> dict:
    """Gets a scorecard with no strokes, for adding rounds"""
    for match in matches:
        course_info = get_course_info(match)
        holes = get_holes(match)
        yardages = get_yardages(course_info, holes)
        handicaps = get_handicaps(holes)
        pars = get_pars(holes)
        scorecard = {"yardages": yardages, "handicaps": handicaps,
                     "pars": pars, "course_name": course_info[0][1]}
        return scorecard


def get_one_round(course_name: str) -> list:
    """Gets one round at a given course"""
    course_query = cur.execute("SELECT * FROM courses WHERE name = (?)",
                               (course_name,))
    course_id = course_query.fetchone()[0]
    one_round_query = cur.execute("SELECT * FROM rounds WHERE course_id = (?)",
                                  (course_id,))
    one_round = one_round_query.fetchall()
    return one_round


def get_golfer_id(golfer: str) -> int:
    """Finds golfer id for a given golfers name"""
    golfer_id_query = cur.execute(
        "SELECT id FROM golfers WHERE name = (?)", (golfer, ))
    golfer_id = golfer_id_query.fetchone()[0]
    return golfer_id


def get_course_id(course: str) -> int:
    """Finds course id for a given course name"""
    course_id_query = cur.execute(
        "SELECT id FROM courses WHERE name = (?)", (course, ))
    course_id = course_id_query.fetchone()[0]
    return course_id


def commit_golfer(golfer: str) -> None:
    """Adds a golfer to the database"""
    statement = "INSERT INTO golfers (name) VALUES (?)"
    params = [golfer]
    cur.execute(statement, params)
    con.commit()
    return


def commit_round(golfer_round: list) -> None:
    """Adds a golfer round to the database"""
    statement = "INSERT INTO rounds (golfer_id, course_id, date, one, two, " \
                "three, four, five, six, seven, eight, nine, ten, eleven, " \
                "twelve, thirteen, fourteen, fifteen, sixteen, seventeen, " \
                "eighteen, match_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, " \
                "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    params = golfer_round
    cur.execute(statement, params)
    con.commit()
    return


def get_match_id() -> int:
    """Returns a unique match id"""
    match_id_query = cur.execute("SELECT MAX(match_id) FROM rounds")
    match_id = match_id_query.fetchone()[0]
    match_id += 1
    return match_id
