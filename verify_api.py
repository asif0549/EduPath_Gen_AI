import json
import urllib.request

payload = {
    'attendance': 88,
    'cgpa': 8.5,
    'aptitude_score': 82,
    'coding_score': 85,
    'communication_score': 78,
    'mock_exam_score': 80,
    'backlogs': 1,
    'career_interest': 'Cloud Engineer',
    'exam_selected': 'GATE',
    'primary_goal': 'Cloud / DevOps',
}
req = urllib.request.Request(
    'http://127.0.0.1:8000/api/v1/predictions/student',
    data=json.dumps(payload).encode(),
    headers={'Content-Type': 'application/json'},
    method='POST',
)
with urllib.request.urlopen(req) as resp:
    print(resp.read().decode())
