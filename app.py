from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
from golf import get_scorecards, get_golfers, get_rounds, get_stats, get_vs_rounds, get_record, get_vs_scorecards, get_courses, commit_golfer, commit_round, get_one_round, get_course_id, get_match_id, get_golfer_id, get_post_scorecard, get_course_rounds, commit_course

# Configure application
app = Flask(__name__)

# Homepage that displays statistics for all golfers rounds
@app.route("/")
def homepage():
    all_golfer_stats = []
    golfers = get_golfers() # Get all golfers
    for golfer in golfers:
        golfer_name = golfer['golfer_name']
        golfers_rounds = get_rounds(golfer_name) # Get golfers rounds
        if len(golfers_rounds) >= 1: # Ensure golfer has played a round
            # Get golfer stats
            stats = get_stats(golfers_rounds, golfer_name)
            stats.insert(1, len(golfers_rounds))
            all_golfer_stats.append(stats)
    # Sort by average round
    def sorter(e): return e[2]
    all_golfer_stats.sort(key=sorter)
    return render_template("homepage.html", all_golfer_stats=all_golfer_stats)


# Tab that dispays all rounds for a given golfer
@app.route("/rounds", methods=["GET", "POST"])
@app.route("/rounds/<golfer_name>", methods=["GET", "POST"]) # Offer alternative rounds link (to click through via homepage)
def rounds(golfer_name="lampsha"):
    if request.method == "POST":
        # Display scorecards for selected golfer
        golfer_name = request.form.get("golfer_name")
        if golfer_name == None:
            return render_template("apology.html", message="Please select a golfer") # Ensure a golfer was selected
        golfers_rounds = get_rounds(golfer_name)
        scorecards = get_scorecards(golfers_rounds, golfer_name)
        return render_template("rounds.html", scorecards=scorecards, golfer_name=golfer_name)
    else:
        golfers = get_golfers()
        for golfer in golfers:
            if golfer['golfer_name'] == golfer_name: # Check if user accessed the page via a legit golfer
                golfers_rounds = get_rounds(golfer_name)
                scorecards = get_scorecards(golfers_rounds, golfer_name)
                return render_template("rounds.html", scorecards=scorecards, golfer_name=golfer_name)
        else:
            return render_template("round_request.html", golfers=golfers) # Offer a list of golfers to select from


# Tab that displays average scores on each hole for a given golfer and course
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
        if golfer_name == None:
            return render_template("apology.html", message="Please select a golfer") # Ensure a golfer was selected
        if course_name == None:
            return render_template("apology.html", message="Please select a course") # Ensure a course was selected
        course_rounds = get_course_rounds(golfer_name, course_name)
        if len(course_rounds) < 1:
            return render_template("apology.html", message="This golfer has not played this course yet") # Ensure golfer has actually played a round
        # Create lists to keep track of hole averages
        current_holes_sum = [0] * 18
        avg_scores = [0] * 18
        course_copy = tuple(course_rounds[0][:4]) # Course information we need to retain to later pass into the scorecard template
        for match in course_rounds:
            match = match[4:22] # The holes (info in the match) that matter to us
            for i in range(len(match)):
                current_holes_sum[i] += match[i] # Adjust running count of that hole
        for i in range(len(avg_scores)):
            avg_scores[i] = round(current_holes_sum[i] / len(course_rounds), 1) # Calculate average score on that hole
        finalized_round = [course_copy + tuple(avg_scores)] # Finalize round to pass into the scorecard template
        scorecards = get_scorecards(finalized_round, golfer_name)
        return render_template("holes.html", scorecards=scorecards)


# Tab that allows a user to view match statistics between only 2 golfers (will only pull info from rounds they played together)
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
        if golfer_one_name == None or golfer_two_name == None: return render_template("apology.html", message="Please select two golfers") # Ensure golfers were selected
        if golfer_one_name == golfer_two_name: return render_template("apology.html", message="Please select two different golfers") # Ensure different golfer
        else:
            # Gets golfers stats for only mutual matches
            golfer_one_rounds = get_vs_rounds(golfer_one_name, golfer_two_name)
            if len(golfer_one_rounds) < 1:
                return render_template("apology.html", message="These golfers have not played each other.") # Ensure golfers have mutual matches
            # Get stats for both golfers
            stats = get_stats(golfer_one_rounds, golfer_one_name)
            all_golfer_stats.append(stats)
            golfer_two_rounds = get_vs_rounds(golfer_two_name, golfer_one_name)
            stats = get_stats(golfer_two_rounds, golfer_two_name)
            all_golfer_stats.append(stats)
            
            # Get current record between the two golfers
            record = get_record(golfer_one_rounds, golfer_two_rounds, golfer_one_name, golfer_two_name)

            # Gets scorecards for each match
            scorecards = get_vs_scorecards(golfer_one_rounds, golfer_two_rounds, golfer_one_name, golfer_two_name)
        
        # Sort stats by average score
        def sorter(e): return e[1]
        all_golfer_stats.sort(key=sorter)
        return render_template("vs.html", record=record, all_golfer_stats=all_golfer_stats, scorecards=scorecards)


# Tab to post a new match (and add a course of golfer if necessary)
@app.route("/post", methods=["GET", "POST"])
def post():
    if request.method == "GET":
        # Display a list of options for courses and number of golfers
        courses = get_courses()
        return render_template("post_request.html", courses=courses)
    else:
        # Create default date as a placeholder date
        now = datetime.now()
        date = now.strftime("%Y-%m-%d")

        # Get form info to create proper scorecard
        golfer_amount = request.form.get("number_of_golfers")
        if golfer_amount == None: return render_template("apology.html", message="Please select a number of golfers") # Ensure user selected a number of golfers
        golfer_amount = int(golfer_amount)
        course_name = request.form.get("course_name")
        if course_name == None: return render_template("apology.html", message="Please select a course") # Ensure user selected a course
        golfers = get_golfers()
        single_round = get_one_round(course_name) # Get a dummy round from the course to populate the componenents of the scorecard other than strokes
        scorecard = get_post_scorecard(single_round) # Cut out the strokes / part of the scorecard we don't need
        return render_template("post.html", date=date, scorecard=scorecard, golfer_amount=golfer_amount, golfers=golfers)


# Provides the user an option to add a course to the database
@app.route("/add_course", methods=["GET", "POST"])
def add_course():
    if request.method == "GET":
        return render_template("add_course.html")
    else: 
        # Get all course information that was inputted
        course_name = request.form.get("course_name")
        if course_name == '': return render_template("apology.html", message="Please enter a valid course name")
        rating = request.form.get("rating")
        if float(rating) >= 1000 or float(rating) <= 0: return render_template("apology.html", message="Please enter a valid rating")
        slope = request.form.get("slope")
        if int(slope) >= 1000 or int(slope) <= 0: return render_template("apology.html", message="Please enter a valid slope")
        city = request.form.get("city")
        if city == None: return render_template("apology.html", message="Please enter a valid city")
        state = request.form.get("state")
        if state == None: return render_template("apology.html", message="Please enter a valid state")
        # Create lists of yardages, handicaps, pars to populate with the form info and then pass into the database
        yardages = [0] * 21
        handicaps = [0] * 18
        pars = [0] * 21
        # Populate yardages
        for i in range(len(yardages)):
            yardages_temp = "yardages_" + str(i)
            yardages[i] = request.form.get(yardages_temp)
            if int(yardages[i]) >= 10000 or int(yardages[i]) <= 0: return render_template("Please check the yardages you inputted") # Error check yardages
        # Populate handicaps
        for i in range(len(handicaps)):
            handicaps_temp = "handicaps_" + str(i)
            handicaps[i] = request.form.get(handicaps_temp)
            if int(handicaps[i]) >= 100 or int(handicaps[i]) <= 0: return render_template("Please check the handicaps you inputted") # Error check handicaps
        # Populate pars
        for i in range(len(pars)):
            pars_temp = "pars_" + str(i)
            pars[i] = request.form.get(pars_temp)
            if int(pars[i]) >= 100 or int(pars[i]) <= 0: return render_template("Please check the pars you inputted") # Error check pars
        # Add the course and redirect the user to the homepage
        commit_course(course_name, rating, slope, city, state, yardages, handicaps, pars)
        return redirect(url_for('homepage'))


# Provides the user an option to add a golfer
@app.route("/add_golfer", methods=["GET", "POST"])
def add_golfer():
    if request.method == "GET":
        return render_template("add_golfer.html")
    else:
        golfer_name = request.form.get("golfer_name")
        if golfer_name == '': return render_template("apology.html", message="Please type in a golfer name") # Ensure the user typed in a name
        # Check if golfer already exists
        golfers = get_golfers()
        # Ensure the golfer name does not already exist
        for golfer in golfers:
            if golfer['golfer_name'] == golfer_name:
                return render_template("apology.html", message="Golfer name already exists")  
        # Add golfer to database and redirect user to homepage
        commit_golfer(golfer_name)
        return redirect(url_for('homepage'))


# Posts a round to the database
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
    # Truncate list to have only golfers entered
    for i in range(len(golfers)):
        if golfers[i] == None:
            golfers = golfers[:i]
            break
    # Collect golfer scores to pass into database
    golfer_scores = []
    for i in range(len(golfers)):
        scores = [0] * 18 # Empty list to populate
        for j in range(len(scores)):
            golfer_temp = "golfer_" + str(i + 1) + "_" + str(j + 1) # To match name in jinja template
            scores[j] = request.form.get(golfer_temp) # Populate strokes for specific golfers specific hole
        golfer_scores.append(scores)

    for i, golfer in enumerate(golfers):
        golfer_id = get_golfer_id(golfer)
        golfer_scores[i] = [str(golfer_id), str(course_id), round_date] + golfer_scores[i] + [str(match_id)] # Finalize list to pass into database

    # Add each golfers round and redirect user to the homepage
    for i in range(len(golfers)):
        commit_round(golfer_scores[i])
    return redirect(url_for('homepage'))
    
if __name__ == '__main__':
    app.run(debug=True)
    
