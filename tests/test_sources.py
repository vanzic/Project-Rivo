import unittest
from app.sources.mock_source import MockTrendSource

class TestSources(unittest.TestCase):
    def test_mock_source_fetches_trends(self):
        source = MockTrendSource()
        trends = source.fetch_trends()
        self.assertIsInstance(trends, list)
        self.assertGreaterEqual(len(trends), 1)
        # Check format: "Title | Tag"
        for t in trends:
            self.assertIn("|", t)

if __name__ == '__main__':
    unittest.main()
