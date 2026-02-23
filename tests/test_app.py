import unittest

from app import app


class AppPreviewTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_preview_returns_events(self):
        payload = {
            "progression": "c#add9 F#m7 B7 Emaj7",
            "style": "jazz",
            "tempo": "96",
            "complexity": "66",
            "beats_per_chord": "4",
            "variations": "1",
            "humanize": "on",
            "humanize_amount": "40",
            "seed": "1234",
        }

        response = self.client.post("/preview", data=payload)
        self.assertEqual(response.status_code, 200)

        payload = response.get_json()
        self.assertEqual(payload["tempo"], 96)
        self.assertEqual(payload["style"], "jazz")
        self.assertGreater(len(payload["events"]), 0)
        self.assertIn("left_hand", payload["events"][0])
        self.assertIn("right_hand", payload["events"][0])


if __name__ == "__main__":
    unittest.main()
