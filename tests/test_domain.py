import unittest
from app.domain.trend import normalize_text, parse_trend_string

class TestDomain(unittest.TestCase):
    def test_normalize_text_basic(self):
        """Test basic normalization rules."""
        self.assertEqual(normalize_text("Hello World"), "hello world")
        self.assertEqual(normalize_text("  SPACES  "), "spaces")
        # normalize_text does NOT Strip | Source, parse_trend_string does.
        # But it does remove special chars like |
        self.assertEqual(normalize_text("Title | Source"), "title source")
    
    def test_normalize_text_special_chars(self):
        """Test removal of special characters."""
        self.assertEqual(normalize_text("Python 4.0 Released!"), "python 40 released")
        # 'vs' remains as it is alphanumeric
        self.assertEqual(normalize_text("C++ vs Rust"), "c vs rust")
    
    def test_parse_trend_string(self):
        """Test extracting title from raw trend string."""
        self.assertEqual(parse_trend_string("Simple Title"), "Simple Title")
        # parse_trend_string splits and strips
        self.assertEqual(parse_trend_string("Title [123]"), "Title")
        self.assertEqual(parse_trend_string("Title | Source"), "Title")
        self.assertEqual(parse_trend_string("Title [123] | Source"), "Title")

if __name__ == '__main__':
    unittest.main()
