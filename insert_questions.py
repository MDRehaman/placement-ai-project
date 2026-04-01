import random
import MySQLdb

db = MySQLdb.connect(
    host="localhost",
    user="root",
    passwd="Rehman@123",
    db="placement_ai"
)

cursor = db.cursor()

companies = ["Google", "Amazon", "TCS", "Infosys", "Wipro"]

tech_questions = [
    "Explain OOP concepts",
    "What is polymorphism?",
    "Difference between stack and queue",
    "Explain DBMS normalization",
    "What is REST API?",
    "Explain time complexity",
    "What is Python list vs tuple?",
    "Explain multithreading",
    "What is cloud computing?",
    "Difference between SQL and NoSQL"
]

apt_questions = [
    "Find next number: 2, 6, 12, 20, ?",
    "Probability of getting 2 heads in 3 tosses?",
    "Solve: 3x + 5 = 20",
    "Find LCM of 12 and 18",
    "Train problem: speed calculation",
    "Percentage: 30% of 500",
    "Time and work problem",
    "Simple interest formula",
    "Ratio and proportion",
    "Permutation and combination basic"
]

hr_questions = [
    "Tell me about yourself",
    "Why should we hire you?",
    "What are your strengths?",
    "What are your weaknesses?",
    "Where do you see yourself in 5 years?",
    "Why do you want this job?",
    "Describe a challenge you faced",
    "Tell me about a failure",
    "Are you a team player?",
    "Why this company?"
]

for company in companies:
    for _ in range(100):  # 100 per company = 500 total

        q_type = random.choice(["tech", "apt", "hr"])

        if q_type == "tech":
            question = random.choice(tech_questions)
        elif q_type == "apt":
            question = random.choice(apt_questions)
        else:
            question = random.choice(hr_questions)

        cursor.execute(
            "INSERT INTO questions (company_name, question, type) VALUES (%s,%s,%s)",
            (company, question, q_type)
        )

db.commit()
cursor.close()
db.close()

print("✅ 500+ Questions Inserted Successfully")