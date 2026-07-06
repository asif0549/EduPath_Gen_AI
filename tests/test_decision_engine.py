import unittest

from decision_engine import generate_career_recommendations


class DecisionEngineTests(unittest.TestCase):
    def test_generates_top_three_recommendations_with_complete_fields(self):
        payload = {
            "attendance": 88,
            "cgpa": 8.5,
            "aptitude_score": 82,
            "coding_score": 85,
            "communication_score": 78,
            "mock_exam_score": 80,
            "backlogs": 1,
            "career_interest": "Cloud Engineer",
            "exam_selected": "GATE",
            "primary_goal": "Cloud / DevOps",
        }

        recommendations = generate_career_recommendations(payload)

        self.assertEqual(len(recommendations), 3)
        for recommendation in recommendations:
            self.assertTrue(recommendation["career"]) 
            self.assertGreaterEqual(recommendation["suitability_score"], 0)
            self.assertLessEqual(recommendation["suitability_score"], 100)
            self.assertTrue(recommendation["why_recommended"])
            self.assertTrue(recommendation["pros"])
            self.assertTrue(recommendation["challenges"])
            self.assertTrue(recommendation["required_skills"])
            self.assertTrue(recommendation["missing_skills"])
            self.assertTrue(recommendation["roadmap"])
            self.assertTrue(recommendation["future_demand"])
            self.assertTrue(recommendation["salary_range"])
            self.assertTrue(recommendation["time_to_job_ready"])


if __name__ == "__main__":
    unittest.main()
