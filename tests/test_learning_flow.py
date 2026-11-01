"""Cross-request learning contracts, with no network or paid provider calls."""

import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

with patch.dict(os.environ, {"SARVAM_API_KEY": "", "GEMINI_API_KEY": ""}):
    from backend import main


class LearningFlowTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {"SARVAM_API_KEY": "", "GEMINI_API_KEY": ""})
        self.env.start()
        self.client = TestClient(main.app)
        main.sources.clear()
        main.lessons.clear()
        main.followups.clear()

    def tearDown(self):
        self.client.close()
        self.env.stop()

    def demo(self):
        response = self.client.post("/api/lesson", json={"mode": "demo", "language": "en-IN"})
        self.assertEqual(response.status_code, 200)
        return response.json()

    def submit(self, lesson, step, answer, mode="demo"):
        return self.client.post("/api/answer", json={
            "lessonId": lesson["id"], "stepId": step["id"],
            "answer": answer, "language": "en-IN", "mode": mode,
        })

    def test_live_source_does_not_silently_become_demo_when_gemini_missing(self):
        source = self.client.post("/api/material", data={
            "text": "Evaporation changes liquid water into water vapor. Heat can increase evaporation.",
            "title": "Water cycle",
        })
        self.assertEqual(source.status_code, 200)
        self.assertEqual(source.json()["pages"][0]["page"], 1)
        response = self.client.post("/api/lesson", json={
            "sourceId": source.json()["sourceId"], "language": "en-IN", "mode": "live",
        })
        self.assertEqual(response.status_code, 503)
        self.assertIn("GEMINI_API_KEY", response.json()["detail"])
        self.assertFalse(main.lessons)

    def test_demo_cannot_claim_uploaded_source_provenance(self):
        lesson = self.client.post("/api/lesson", json={
            "sourceId": "unrelated-upload", "mode": "demo", "language": "en-IN",
        }).json()
        self.assertEqual(lesson["provider"], "demo")
        self.assertIsNone(lesson["sourceId"])
        self.assertTrue(all(not step["sourcePages"] for step in lesson["steps"]))

    def test_wrong_reason_changes_question_and_grades_the_new_question(self):
        lesson = self.demo()
        step = next(step for step in lesson["steps"] if step["id"] == "compare-parts")
        repair = self.submit(lesson, step, "1/4 because four is bigger").json()
        self.assertEqual(repair["status"], "needs_work")
        self.assertIn("1/2", repair["followUpQuestion"])
        self.assertTrue(repair["board"]["fractionBars"])
        result = self.submit(
            lesson, step, "1/2 is larger because the same whole is split into fewer equal pieces."
        ).json()
        self.assertEqual(result["status"], "correct")
        self.assertNotIn((lesson["id"], step["id"]), main.followups)

    def test_request_mode_cannot_change_stored_lesson_provider(self):
        lesson = self.demo()
        response = self.submit(lesson, lesson["steps"][0], "four equal parts make the whole", mode="live")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "correct")

    def test_contradictory_reasoning_is_never_marked_correct(self):
        lesson = self.demo()
        for step_id, statement in [
            ("compare-parts", "1/4 is larger than 1/3 because four pieces"),
            ("compare-parts", "1/3 is smaller than 1/4 because the whole is the same"),
            ("transfer", "1/2 is smaller than 1/5 because there are fewer equal parts"),
        ]:
            with self.subTest(step=step_id):
                step = next(step for step in lesson["steps"] if step["id"] == step_id)
                response = self.submit(lesson, step, statement)
                self.assertEqual(response.status_code, 200)
                self.assertNotEqual(response.json()["status"], "correct")


if __name__ == "__main__":
    unittest.main()
