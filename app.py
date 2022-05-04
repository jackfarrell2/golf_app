from flask import Flask, render_template
import sqlite3

# Configure application
app = Flask(__name__)

# Configure sqlite3 cursor
con = sqlite3.connect("golf.db")
cur = con.cursor()

@app.route("/")
def homepage():
    return render_template("homepage.html")

