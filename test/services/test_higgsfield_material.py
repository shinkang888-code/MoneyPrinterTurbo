import unittest

from app.services.higgsfield_material import _extract_duration, _extract_video_url


class HiggsfieldMaterialTests(unittest.TestCase):
    def test_extract_video_url_from_videos_list(self):
        result = {"videos": [{"url": "https://cdn.example.com/video.mp4"}]}
        self.assertEqual(
            _extract_video_url(result),
            "https://cdn.example.com/video.mp4",
        )

    def test_extract_video_url_from_raw_url(self):
        result = {"rawUrl": "https://cdn.example.com/raw.mp4"}
        self.assertEqual(
            _extract_video_url(result),
            "https://cdn.example.com/raw.mp4",
        )

    def test_extract_duration(self):
        self.assertEqual(_extract_duration({"durationSec": 6.5}, 5), 6)


if __name__ == "__main__":
    unittest.main()
