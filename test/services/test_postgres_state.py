import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.postgres_state import flatten_task_row


class TestPostgresStateHelpers(unittest.TestCase):
    def test_flatten_task_row_merges_extra_fields(self):
        row = {
            "task_id": "task-1",
            "state": 1,
            "progress": 100,
            "extra": {"videos": ["final-1.mp4"], "script": "hello"},
        }

        task = flatten_task_row(row)

        self.assertEqual(task["task_id"], "task-1")
        self.assertEqual(task["videos"], ["final-1.mp4"])
        self.assertEqual(task["script"], "hello")


if __name__ == "__main__":
    unittest.main()
