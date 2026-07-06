from __future__ import annotations

from typing import Any


CAREER_RULES = {
    "Cloud Engineer": {
        "weights": {
            "coding_score": 0.32,
            "aptitude_score": 0.20,
            "communication_score": 0.15,
            "attendance": 0.15,
            "cgpa": 0.10,
            "mock_exam_score": 0.08,
        },
        "required_skills": ["Linux", "Networking", "AWS/Azure", "Docker & Kubernetes"],
        "future_demand": "Very high demand across startups and enterprises",
        "salary_range": "$70k–$130k+",
        "roadmap": [
            "Python fundamentals",
            "Linux and networking basics",
            "Cloud foundations (AWS/Azure)",
            "Docker + Kubernetes",
            "Infrastructure as code",
            "Projects and portfolio",
            "Resume + mock interviews",
        ],
    },
    "AI Engineer": {
        "weights": {
            "aptitude_score": 0.28,
            "coding_score": 0.25,
            "cgpa": 0.18,
            "communication_score": 0.10,
            "attendance": 0.10,
            "mock_exam_score": 0.09,
        },
        "required_skills": ["Python", "Math", "Machine Learning", "Deep Learning", "LLMs"],
        "future_demand": "Strong demand in applied AI and product teams",
        "salary_range": "$80k–$150k+",
        "roadmap": [
            "Python and statistics",
            "Machine learning foundations",
            "Deep learning concepts",
            "LLMs and RAG workflows",
            "Capstone projects",
            "Portfolio and internships",
        ],
    },
    "Data Scientist": {
        "weights": {
            "aptitude_score": 0.25,
            "coding_score": 0.20,
            "cgpa": 0.20,
            "communication_score": 0.15,
            "attendance": 0.10,
            "mock_exam_score": 0.10,
        },
        "required_skills": ["Statistics", "Python", "SQL", "Data visualization", "Experimentation"],
        "future_demand": "Consistent demand in analytics and decision science",
        "salary_range": "$70k–$140k+",
        "roadmap": [
            "Python and SQL",
            "Statistics and probability",
            "Data cleaning and modeling",
            "Dashboarding and storytelling",
            "Projects and case studies",
            "Internships and analytics portfolio",
        ],
    },
    "Government Job": {
        "weights": {
            "aptitude_score": 0.35,
            "mock_exam_score": 0.25,
            "attendance": 0.15,
            "cgpa": 0.10,
            "communication_score": 0.10,
            "coding_score": 0.05,
        },
        "required_skills": ["Quantitative aptitude", "General awareness", "Mock tests", "Time management"],
        "future_demand": "Steady demand through public sector recruitment cycles",
        "salary_range": "$25k–$70k+",
        "roadmap": [
            "Quantitative aptitude",
            "General awareness and current affairs",
            "Mock tests and previous papers",
            "Interview preparation",
            "Revision and speed drills",
        ],
    },
    "Cybersecurity": {
        "weights": {
            "aptitude_score": 0.25,
            "coding_score": 0.25,
            "attendance": 0.15,
            "cgpa": 0.15,
            "communication_score": 0.10,
            "mock_exam_score": 0.10,
        },
        "required_skills": ["Networking", "Linux", "Security fundamentals", "Scripting"],
        "future_demand": "High demand as cyber threats continue to expand",
        "salary_range": "$70k–$140k+",
        "roadmap": [
            "Networking and OS basics",
            "Security fundamentals",
            "Scripting and automation",
            "Hands-on labs",
            "Certifications and projects",
        ],
    },
    "Business Analyst": {
        "weights": {
            "communication_score": 0.30,
            "aptitude_score": 0.25,
            "cgpa": 0.20,
            "attendance": 0.10,
            "mock_exam_score": 0.10,
            "coding_score": 0.05,
        },
        "required_skills": ["Communication", "Business thinking", "Excel/SQL", "Stakeholder handling"],
        "future_demand": "Stable demand across consulting and product analytics",
        "salary_range": "$55k–$110k+",
        "roadmap": [
            "Communication and business case writing",
            "Excel and SQL basics",
            "Market and process analysis",
            "Dashboarding and reporting",
            "Stakeholder communication",
        ],
    },
}


def _score_career(profile: dict[str, Any], career: str) -> float:
    rule = CAREER_RULES[career]
    score = 0.0
    for feature, weight in rule["weights"].items():
        score += float(profile.get(feature, 0.0)) * weight

    if profile.get("primary_goal") == career:
        score += 8
    if profile.get("career_interest") == career:
        score += 6
    if career == "Cloud Engineer" and profile.get("coding_score", 0) >= 75:
        score += 4
    if career == "AI Engineer" and profile.get("aptitude_score", 0) >= 75:
        score += 4
    if career == "Government Job" and profile.get("mock_exam_score", 0) >= 75:
        score += 5
    if profile.get("backlogs", 0) > 2 and career in {"Cloud Engineer", "AI Engineer", "Data Scientist"}:
        score -= 6
    return round(min(100.0, max(0.0, score)), 1)


def _generate_reasons(profile: dict[str, Any], career: str, score: float) -> tuple[str, list[str], list[str]]:
    reasons: list[str] = []
    missing_skills: list[str] = []

    if career == "Cloud Engineer":
        if profile.get("coding_score", 0) >= 75:
            reasons.append("Your coding strength is a strong fit for cloud implementation work")
        else:
            missing_skills.append("Cloud automation and scripting")
        if profile.get("communication_score", 0) >= 70:
            reasons.append("Your communication skills support documentation and teamwork")
        else:
            missing_skills.append("Technical documentation")
        if profile.get("attendance", 0) >= 75:
            reasons.append("Consistent attendance supports sustained learning")
    elif career == "AI Engineer":
        if profile.get("aptitude_score", 0) >= 75:
            reasons.append("Your analytical ability is a strong base for model building")
        else:
            missing_skills.append("Mathematics and experimentation")
        if profile.get("cgpa", 0) >= 7.0:
            reasons.append("Your academic foundation supports a technical learning curve")
        if profile.get("coding_score", 0) >= 75:
            reasons.append("Your programming score aligns with applied AI workflows")
    elif career == "Data Scientist":
        if profile.get("aptitude_score", 0) >= 75:
            reasons.append("Strong analytical skills support data-driven decision work")
        if profile.get("communication_score", 0) >= 70:
            reasons.append("Good communication helps translate insights to business users")
        else:
            missing_skills.append("Business storytelling")
    elif career == "Government Job":
        if profile.get("mock_exam_score", 0) >= 75:
            reasons.append("Your mock test performance points to good exam readiness")
        if profile.get("aptitude_score", 0) >= 75:
            reasons.append("Your aptitude profile supports competitive exam preparation")
    elif career == "Cybersecurity":
        if profile.get("coding_score", 0) >= 75:
            reasons.append("Your coding ability supports security automation and scripting")
        if profile.get("aptitude_score", 0) >= 75:
            reasons.append("Logical thinking is valuable in defensive security")
    elif career == "Business Analyst":
        if profile.get("communication_score", 0) >= 75:
            reasons.append("Strong communication aligns with stakeholder-facing analysis")
        if profile.get("cgpa", 0) >= 7.0:
            reasons.append("A solid academic profile supports structured problem solving")

    if not reasons:
        reasons.append("This path matches your current profile and learning trends")

    pros = [
        f"High fit score ({score:.0f}%) based on your current academic signal mix",
        "The roadmap is designed around measurable skill growth",
        "The path can be pursued with a focused 90-day execution plan",
    ]
    challenges = [
        "Prioritized skill gaps will require consistent weekly practice",
        "Portfolio proof matters more than academic marks alone",
        "Interview readiness must be built through repeated exposure",
    ]

    return (
        f"Your profile suggests {career} is a strong fit because {reasons[0].lower()}.",
        pros,
        challenges,
    )


def generate_career_recommendations(profile: dict[str, Any]) -> list[dict[str, Any]]:
    scored_careers = []
    for career in CAREER_RULES:
        score = _score_career(profile, career)
        why_recommended, pros, challenges = _generate_reasons(profile, career, score)
        rule = CAREER_RULES[career]
        missing_skills = []
        if career == "Cloud Engineer":
            if profile.get("coding_score", 0) < 75:
                missing_skills.append("Cloud automation and scripting")
            if profile.get("attendance", 0) < 75:
                missing_skills.append("Consistent study cadence")
        elif career == "AI Engineer":
            if profile.get("aptitude_score", 0) < 75:
                missing_skills.append("Advanced mathematics")
            if profile.get("coding_score", 0) < 75:
                missing_skills.append("Production-grade Python")
        elif career == "Data Scientist":
            if profile.get("aptitude_score", 0) < 75:
                missing_skills.append("Advanced statistics")
            if profile.get("communication_score", 0) < 70:
                missing_skills.append("Storytelling with data")
        elif career == "Government Job":
            if profile.get("mock_exam_score", 0) < 75:
                missing_skills.append("Mock test discipline")
        elif career == "Cybersecurity":
            if profile.get("coding_score", 0) < 75:
                missing_skills.append("Security scripting")
        elif career == "Business Analyst":
            if profile.get("communication_score", 0) < 75:
                missing_skills.append("Stakeholder communication")
        if not missing_skills:
            missing_skills = ["Portfolio depth and interview practice"]

        scored_careers.append(
            {
                "career": career,
                "suitability_score": score,
                "confidence": round(min(0.98, 0.62 + score / 100 * 0.3), 2),
                "why_recommended": why_recommended,
                "pros": pros,
                "challenges": challenges,
                "future_demand": rule["future_demand"],
                "salary_range": rule["salary_range"],
                "required_skills": rule["required_skills"],
                "missing_skills": missing_skills,
                "time_to_job_ready": "3–6 months" if score >= 80 else "6–12 months",
                "roadmap": rule["roadmap"],
            }
        )

    scored_careers.sort(key=lambda item: item["suitability_score"], reverse=True)
    return scored_careers[:3]
