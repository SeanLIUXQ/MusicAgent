import json
import time
import unittest
from pathlib import Path

import app as api


class ApiTests(unittest.TestCase):
    def setUp(self):
        api.app.config.update(TESTING=True)
        self.client = api.app.test_client()
        self.original_client = api.client
        api.client = None

    def tearDown(self):
        api.client = self.original_client

    def wait_for_task(self, task_id):
        for _ in range(80):
            response = self.client.get(f"/api/task/{task_id}")
            payload = response.get_json()
            if payload["status"] in {"completed", "error"}:
                return payload
            time.sleep(0.025)
        self.fail("task did not finish")

    def test_generate_task_produces_composition_and_downloads(self):
        response = self.client.post("/api/generate", json={"prompt": "bright young electronic track"})
        self.assertEqual(response.status_code, 202)
        result = self.wait_for_task(response.get_json()["task_id"])
        self.assertEqual(result["status"], "completed")
        self.assertTrue(result["result_composition"]["tracks"])
        midi_response = self.client.get(f"/api/midi/{result['midi_filename']}")
        composition_response = self.client.get(f"/api/composition/{result['composition_filename']}")
        self.assertEqual(midi_response.status_code, 200)
        self.assertEqual(composition_response.status_code, 200)
        midi_response.close()
        composition_response.close()

    def test_feedback_uses_previous_composition(self):
        previous = api.generate_composition("calm piano", None)
        response = self.client.post(
            "/api/generate",
            json={
                "prompt": "calm piano",
                "feedback": "faster",
                "previous_composition": previous,
            },
        )
        result = self.wait_for_task(response.get_json()["task_id"])
        self.assertEqual(result["result_composition"]["tempo"], previous["tempo"] + 12)

    def test_download_rejects_directory_traversal(self):
        self.assertIsNone(api._safe_output_file("../app.py", {".mid"}))
        response = self.client.get("/api/midi/%2e%2e%2fapp.py")
        self.assertNotEqual(response.status_code, 200)

    def test_cors_only_allows_loopback_origins(self):
        denied = self.client.get("/api/health", headers={"Origin": "https://attacker.example"})
        allowed = self.client.get("/api/health", headers={"Origin": "http://localhost:5173"})
        self.assertNotIn("Access-Control-Allow-Origin", denied.headers)
        self.assertEqual(allowed.headers.get("Access-Control-Allow-Origin"), "http://localhost:5173")

    def test_invalid_json_and_invalid_composition_return_400(self):
        response = self.client.post("/api/generate", data="nope", content_type="text/plain")
        self.assertEqual(response.status_code, 400)
        response = self.client.post("/api/arrange", json={"composition": {}, "style_request": "rock"})
        self.assertEqual(response.status_code, 400)

    def test_history_delete_removes_json_and_matching_midi(self):
        composition = api.generate_composition("history test", None)
        json_name, midi_name = api._persist(composition, "test")
        response = self.client.delete(f"/api/history/{json_name}")
        self.assertEqual(response.status_code, 200)
        self.assertFalse((api.OUTPUT_DIR / json_name).exists())
        self.assertFalse((api.OUTPUT_DIR / midi_name).exists())

    def test_task_store_is_bounded(self):
        store = api.TaskStore(capacity=10, ttl_seconds=60)
        for _ in range(14):
            store.add(api.GenerationTask("test"))
        self.assertEqual(len(store._tasks), 10)


if __name__ == "__main__":
    unittest.main()
