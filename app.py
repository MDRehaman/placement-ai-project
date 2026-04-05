from flask import Flask, render_template, request, redirect, session, flash, url_for
import sqlite3
import os
import random

app = Flask(__name__)
app.secret_key = "placement_secret"

# ================= SQLITE DB =================

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# ================= INIT DB =================

@app.route('/init_db')
def init_db():
    conn = get_db()
    cur = conn.cursor()

    # STUDENTS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT UNIQUE,
        password TEXT
    )
    """)

    # QUESTIONS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT,
        type TEXT,
        question TEXT,
        option1 TEXT,
        option2 TEXT,
        option3 TEXT,
        option4 TEXT,
        answer TEXT
    )
    """)

    # RESULTS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT,
        company_name TEXT,
        score INTEGER,
        total INTEGER,
        percentage REAL,
        tech_score INTEGER,
        apt_score INTEGER,
        hr_score INTEGER,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # COMPANIES (IMPORTANT)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT
    )
    """)

    conn.commit()
    conn.close()

    return "ALL TABLES CREATED ✅"

# ================= AUTH =================
@app.route('/check_users')
def check_users():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM students")
    data = cur.fetchall()

    conn.close()

    return str(data)

@app.route('/')
def home():
    return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        student_id = request.form['student_id']
        password = request.form['password']

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM students WHERE student_id=? AND password=?", (student_id, password))
        user = cur.fetchone()
        conn.close()

        if user:
            session['student_id'] = student_id
            return redirect('/dashboard')
        else:
            return "Invalid Login"

    return render_template('login.html')


@app.route('/register')
def register():
    return render_template("register.html")


@app.route('/register_user', methods=['POST'])
def register_user():

    student_id = request.form.get('student_id')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')

    if not student_id or not password:
        return "Missing data, please fill all fields"

    if password != confirm_password:
        return "Passwords do not match"

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM students WHERE student_id=?", (student_id,))
    existing_user = cur.fetchone()

    if existing_user:
        flash('This ID is already registered', 'danger')
        conn.close()
        return redirect(url_for('register'))

    cur.execute("INSERT INTO students(student_id, password) VALUES(?, ?)",
                (student_id, password))

    conn.commit()
    conn.close()

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
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT company_name FROM questions")
    data = cur.fetchall()
    conn.close()
    return render_template("companies.html", companies=data)

# ================= QUESTIONS =================

@app.route('/questions')
def questions():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT company_name FROM questions")
    companies = cur.fetchall()
    conn.close()
    return render_template("questions.html", companies=companies)


@app.route('/questions/<company>')
def company_questions(company):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, question,
        CASE 
            WHEN LOWER(type)='technical' THEN 'tech'
            WHEN LOWER(type)='aptitude' THEN 'apt'
            WHEN LOWER(type)='hr' THEN 'hr'
            ELSE LOWER(type)
        END as type
        FROM questions
        WHERE LOWER(company_name) = LOWER(?)
    """, (company,))

    questions = cur.fetchall()

    print("FINAL QUESTIONS:", questions)

    conn.close()

    return render_template(
        'company_questions.html',
        questions=questions,
        company=company
    )

# ================= TEST =================

@app.route('/test')
def test():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT company_name FROM questions")
    companies = cur.fetchall()
    conn.close()
    return render_template("test.html", companies=companies, active_page="test")


@app.route('/start_test/<company>')
def start_test(company):

    company = company.lower()

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, question, option1, option2, option3, option4, answer, type
        FROM questions
        WHERE LOWER(company_name)=?
        LIMIT 10
    """, (company,))

    questions = cur.fetchall()

    session['questions'] = questions  # 🔥 IMPORTANT

    print("DEBUG QUESTIONS:", questions)

    conn.close()

    return render_template('exam.html', questions=questions, company=company)


@app.route('/submit_test', methods=['POST'])
def submit_test():

    questions = session.get('questions', [])

    score = 0
    total = len(questions)

    correct = 0
    wrong = 0
    unanswered = 0

    tech = apt = hr = 0
    tech_total = apt_total = hr_total = 0

    for q in questions:
        q_id = q[0]
        correct_ans = q[6]
        q_type = q[7]

        user_ans = request.form.get(f'q{q_id}')

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

    percentage = (score / total) * 100 if total > 0 else 0

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

    student_id = session.get('student_id')
    company = request.form.get('company')

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO results(student_id, company_name, score, total, percentage,
        tech_score, apt_score, hr_score)
        VALUES (?,?,?,?,?,?,?,?)
    """, (student_id, company, score, total, percentage, tech, apt, hr))

    conn.commit()
    conn.close()

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

@app.route('/force_db')
def force_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT,
        password TEXT
    )
    """)

    conn.commit()
    conn.close()

    return "Students table created ✅"
# ================= HISTORY =================

@app.route('/history')
def history():

    student_id = session.get('student_id')

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT company_name, percentage, tech_score, apt_score, hr_score, date
        FROM results
        WHERE student_id=?
        ORDER BY date DESC
    """, (student_id,))

    data = cur.fetchall()

    print("DATA FROM DB:", data)

    conn.close()

    companies = [d[0] for d in data]
    scores = [d[1] for d in data]

    return render_template(
        'history.html',
        data=data,
        companies=companies,
        scores=scores,
        leaderboard=[],
        latest_tech=data[-1][2] if data else 0,
        latest_apt=data[-1][3] if data else 0,
        latest_hr=data[-1][4] if data else 0,
    )

# ================= RUN =================

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))