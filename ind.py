import csv
import random

career_interests = [
    "Software Engineer",
    "Data Scientist",
    "AI Researcher",
    "Cybersecurity",
    "Cloud Engineer",
    "Business Analyst"
]

exams = ["RRB-NTPC", "SkillsCert", "GATE", "CAT", "GRE", "No exam"]

with open("students_dataset.csv", "w", newline="") as file:
    writer = csv.writer(file)

    writer.writerow([
        "student_id",
        "attendance",
        "cgpa",
        "aptitude_score",
        "coding_score",
        "communication_score",
        "mock_exam_score",
        "backlogs",
        "career_interest",
        "placement_status",
        "exam_selected"
    ])

    for i in range(1, 5001):
        student_id = f"S{i:05d}"
        attendance = random.randint(60, 100)
        cgpa = round(random.uniform(5.0, 10.0), 2)
        aptitude_score = random.randint(0, 100)
        coding_score = random.randint(0, 100)
        communication_score = random.randint(0, 100)
        mock_exam_score = random.randint(0, 100)

        # Logical backlog generation
        if attendance < 70 and cgpa < 6.5:
            backlogs = random.randint(2, 5)
        else:
            backlogs = random.randint(0, 1)

        career_interest = random.choice(career_interests)
        exam_selected = random.choice(exams)

        # Placement logic
        score = (cgpa * 10 + coding_score + communication_score) / 3

        if score > 75:
            placement_status = "Placed"
        elif score > 55:
            placement_status = "In Progress"
        else:
            placement_status = "Not Placed"

        writer.writerow([
            student_id,
            attendance,
            cgpa,
            aptitude_score,
            coding_score,
            communication_score,
            mock_exam_score,
            backlogs,
            career_interest,
            placement_status,
            exam_selected
        ])

print("CSV file created successfully with 5000 rows.")