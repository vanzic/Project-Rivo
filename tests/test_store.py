import unittest
import os
import shutil
import tempfile
import sqlite3
from app.storage.sqlite_store import TrendStore

class TestStore(unittest.TestCase):
    def setUp(self):
        """Create a temp directory and DB."""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_trends.db")
        self.store = TrendStore(db_path=self.db_path)
    
    def tearDown(self):
        """Cleanup temp directory."""
        shutil.rmtree(self.test_dir)

    def test_init_db(self):
        """Test database initialization and schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trend_scores'")
            self.assertIsNotNone(cursor.fetchone())
            
            # Check columns
            cursor.execute("PRAGMA table_info(trend_scores)")
            columns = [row[1] for row in cursor.fetchall()]
            self.assertIn('trend_key', columns)
            self.assertIn('score', columns)
            self.assertIn('last_updated', columns)
            self.assertIn('sources_json', columns)

    def test_add_trend(self):
        """Test adding raw trends."""
        self.store.add_trend("Trend 1 [123]")
        self.assertIn("Trend 1 [123]", self.store.load_all())
        # Duplicate addition should not error
        self.store.add_trend("Trend 1 [123]")
        self.assertEqual(len(self.store.load_all()), 1)

    def test_increment_score_and_metadata(self):
        """Test scoring and metadata aggregation."""
        key = "python"
        
        # First hit
        self.store.increment_score(key, source="Reddit", title="Python 3.12")
        self.assertEqual(self.store.get_score(key), 1)
        
        # Second hit (same source, same title)
        self.store.increment_score(key, source="Reddit", title="Python 3.12")
        self.assertEqual(self.store.get_score(key), 2)
        
        # Third hit (new source, new title)
        self.store.increment_score(key, source="HN", title="Python 3.13")
        self.assertEqual(self.store.get_score(key), 3)
        
        # Verify metadata
        top = self.store.get_top_trends_metadata(limit=1)[0]
        self.assertEqual(top['trend_key'], key)
        self.assertEqual(top['score'], 3)
        self.assertEqual(set(top['sources']), {"Reddit", "HN"})
        self.assertEqual(set(top['sample_titles']), {"Python 3.12", "Python 3.13"})

    def test_get_top_trends_filter(self):
        """Test 48h filtering (implicitly, by checking insertion works)."""
        # Since we use CURRENT_TIMESTAMP, everything added now should be visible
        self.store.increment_score("recent_trend")
        results = self.store.get_top_trends_metadata(limit=10)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['trend_key'], "recent_trend")

if __name__ == '__main__':
    unittest.main()
