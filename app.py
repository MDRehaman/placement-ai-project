from flask import Flask, render_template, request, redirect, session
from flask_mysqldb import MySQL

app = Flask(__name__)
app.secret_key = "placement_secret"

# MySQL Config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Rehman@123'
app.config['MYSQL_DB'] = 'placement_ai'

mysql = MySQL(app)

# ================= AUTH =================

@app.route('/')
def home():
    return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        student_id = request.form['student_id']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM students WHERE student_id=%s AND password=%s", (student_id, password))
        user = cur.fetchone()
        cur.close()

        if user:
            session['student_id'] = student_id
            return redirect('/dashboard')
        else:
            return "Invalid Login"

    return render_template('login.html')


@app.route('/register')
def register():
    return render_template("register.html")
from flask import Flask, request, render_template,flash, redirect, url_for
from werkzeug.security import generate_password_hash

from flask import flash, redirect, url_for

@app.route('/register_user', methods=['POST'])
def register_user():

    student_id = request.form.get('student_id')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')

    if not student_id or not password:
        return "Missing data, please fill all fields"

    if password != confirm_password:
        return "Passwords do not match"

    cur = mysql.connection.cursor()

    # ✅ CHECK DUPLICATE
    cur.execute("SELECT * FROM students WHERE student_id=%s", (student_id,))
    existing_user = cur.fetchone()

    if existing_user:
        flash('This ID is already registered', 'danger')
        cur.close()
        return redirect(url_for('register'))

    # ✅ INSERT NEW USER
    cur.execute(
        "INSERT INTO students(student_id, password) VALUES(%s, %s)",
        (student_id, password)
    )

    mysql.connection.commit()
    cur.close()

    return redirect('/login')


@app.route('/logout')
def logout():
    session.pop('student_id', None)
    return redirect('/login')

# ================= DASHBOARD =================

@app.route('/dashboard')
def dashboard():
    return render_template("dashboard.html", active_page="dashboard")


@app.route('/companies')
def companies():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM companies")
    data = cur.fetchall()
    cur.close()
    return render_template("companies.html", companies=data)

# ================= QUESTIONS =================

@app.route('/questions')
def questions():
    cur = mysql.connection.cursor()
    cur.execute("SELECT DISTINCT company_name FROM questions")
    companies = cur.fetchall()
    cur.close()
    return render_template("questions.html", companies=companies)


@app.route('/questions/<company>')
def company_questions(company):

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT id, question,
        CASE 
            WHEN LOWER(type)='technical' THEN 'tech'
            WHEN LOWER(type)='aptitude' THEN 'apt'
            WHEN LOWER(type)='hr' THEN 'hr'
            ELSE LOWER(type)
        END as type
        FROM questions
        WHERE LOWER(company_name) = LOWER(%s)
    """, (company,))

    questions = cur.fetchall()

    print("FINAL QUESTIONS:", questions)

    cur.close()

    return render_template(
        'company_questions.html',
        questions=questions,
        company=company
    )


# ================= TEST =================

@app.route('/test')
def test():
    cur = mysql.connection.cursor()
    cur.execute("SELECT DISTINCT company_name FROM test_questions")
    companies = cur.fetchall()
    cur.close()
    return render_template("test.html", companies=companies, active_page="test")

from flask import session
import random

@app.route('/start_test/<company>')
def start_test(company):

    company = company.lower()   # 🔥 FIX

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT id, question, option1, option2, option3, option4, answer
        FROM questions
        WHERE LOWER(company_name)=%s
        LIMIT 10
    """, (company,))

    questions = cur.fetchall()

    print("DEBUG QUESTIONS:", questions)  # 🔥 DEBUG

    cur.close()

    return render_template('exam.html', questions=questions, company=company)


@app.route('/submit_test', methods=['POST'])
def submit_test():

    questions = session.get('questions', [])

    score = 0
    total = len(questions)

    correct = 0
    wrong = 0
    unanswered = 0

    tech = apt = hr = 0   # 🔥 ADD
    tech_total = apt_total = hr_total = 0

    for q in questions:
        q_id = q[0]
        correct_ans = q[6]
        q_type = q[7]   # 🔥 MAKE SURE type is included in session

        user_ans = request.form.get(f'q{q_id}')

        # Count totals
        if q_type == "tech":
            tech_total += 1
        elif q_type == "apt":
            apt_total += 1
        elif q_type == "hr":
            hr_total += 1

        if not user_ans:
            unanswered += 1
        elif user_ans == correct_ans:
            correct += 1
            score += 1

            if q_type == "tech":
                tech += 1
            elif q_type == "apt":
                apt += 1
            elif q_type == "hr":
                hr += 1
        else:
            wrong += 1

    # 🔥 PERCENTAGE CALCULATION
    percentage = (score / total) * 100 if total > 0 else 0

    # 🔥 AI ANALYSIS
    if percentage >= 80:
        level = "Excellent 🚀"
    elif percentage >= 60:
        level = "Good 👍"
    else:
        level = "Needs Improvement ⚠️"

    strengths = []
    weaknesses = []

    if tech >= apt and tech >= hr:
        strengths.append("Technical Skills")
    else:
        weaknesses.append("Technical Skills")

    if apt >= tech and apt >= hr:
        strengths.append("Aptitude")
    else:
        weaknesses.append("Aptitude")

    if hr >= tech and hr >= apt:
        strengths.append("Communication")
    else:
        weaknesses.append("Communication")

    suggestions = []

    if tech_total > 0 and tech / tech_total < 0.5:
        suggestions.append("Practice DSA & core subjects")

    if apt_total > 0 and apt / apt_total < 0.5:
        suggestions.append("Improve aptitude speed & accuracy")

    if hr_total > 0 and hr / hr_total < 0.5:
        suggestions.append("Work on communication & HR answers")

    if not suggestions:
        suggestions.append("You're doing great! Keep improving 🚀")

    analysis = {
        "level": level,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "suggestions": suggestions
    }

    # 🔥 SAVE TO DATABASE
    student_id = session.get('student_id')
    company = request.form.get('company')

    cur = mysql.connection.cursor()

    cur.execute(
        """INSERT INTO results(student_id, company_name, score, total, percentage,
        tech_score, apt_score, hr_score)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
        (student_id, company, score, total, percentage, tech, apt, hr)
    )

    mysql.connection.commit()
    cur.close()

    # 🔥 FINAL RETURN (ONLY ONE RETURN)
    return render_template(
        'result.html',
        score=score,
        total=total,
        correct=correct,
        wrong=wrong,
        unanswered=unanswered,
        percentage=percentage,
        analysis=analysis
    )

# ================= HISTORY =================

@app.route('/history')
def history():

    student_id = session.get('student_id')

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT company_name, percentage, tech_score, apt_score, hr_score, date
        FROM results
        WHERE student_id=%s
        ORDER BY date DESC
    """, (student_id,))

    data = cur.fetchall()

    print("DATA FROM DB:", data)   # 🔥 ADD THIS

    cur.close()

    # prepare lists for charts
    companies = [d[0] for d in data]
    scores = [d[1] for d in data]

    return render_template(
        'history.html',
        data=data,
        companies=companies,
        scores=scores,
        leaderboard=[],
        latest_tech = data[-1][2] if data else 0,
        latest_apt = data[-1][3] if data else 0,
        latest_hr = data[-1][4] if data else 0,
    )

import os
if __name__ == "__main__":
    app.run(host='0.0.0.0',
    port=int(os.environ.get('PORT', 5000)))