import unittest

from app.services import video_source as vs


class VideoSourceTests(unittest.TestCase):
    def test_get_configured_stock_sources(self):
        app_config = {
            "pexels_api_keys": [],
            "pixabay_api_keys": ["pix-key"],
            "coverr_api_keys": "coverr-key",
        }
        self.assertEqual(
            vs.get_configured_stock_sources(app_config),
            ["pixabay", "coverr"],
        )

    def test_resolve_video_source_auto(self):
        app_config = {
            "pexels_api_keys": ["pex-key"],
            "pixabay_api_keys": ["pix-key"],
        }
        self.assertEqual(vs.resolve_video_source("auto", app_config), "pexels")
        self.assertEqual(vs.resolve_video_source("coverr", app_config), "coverr")

    def test_get_sources_for_download_auto_fallback(self):
        app_config = {
            "pexels_api_keys": [],
            "pixabay_api_keys": ["pix-key"],
            "coverr_api_keys": ["coverr-key"],
        }
        self.assertEqual(
            vs.get_sources_for_download("auto", app_config),
            ["pixabay", "coverr"],
        )


if __name__ == "__main__":
    unittest.main()
