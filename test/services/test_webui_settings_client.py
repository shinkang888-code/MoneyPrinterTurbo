import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.models import const
from webui import settings_client


class TestWebuiSettingsClient(unittest.TestCase):
    def test_task_state_label(self):
        tr = lambda key: key
        self.assertEqual(
            settings_client.task_state_label(const.TASK_STATE_COMPLETE, tr),
            "Task Complete",
        )

    @patch("webui.settings_client.pg.is_postgres_enabled", return_value=True)
    @patch("webui.settings_client.pg.set_setting")
    def test_sync_webui_prefs_uses_postgres(self, mock_set_setting, _mock_enabled):
        self.assertTrue(
            settings_client.sync_webui_prefs(
                ui_language="en-US",
                hide_config=False,
                hide_log=True,
                match_materials_to_script=True,
            )
        )
        mock_set_setting.assert_called_once()


if __name__ == "__main__":
    unittest.main()
