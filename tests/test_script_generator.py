import unittest
from app.domain.schemas import TrendOutput, ScriptOutput
from app.consumers.script_generator import ScriptGenerator

class TestScriptGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = ScriptGenerator()
        self.sample_trend = TrendOutput(
            trend_key="ai automation",
            score=10,
            sources=["TechCrunch", "HackerNews"],
            sample_titles=["AI Automation is taking over jobs", "New AI tools released"],
            first_seen="2025-01-01 10:00:00",
            last_seen="2025-01-02 10:00:00"
        )
        
    def test_generate_structure(self):
        """Verify that generate returns a valid ScriptOutput object."""
        script = self.generator.generate(self.sample_trend)
        self.assertIsInstance(script, ScriptOutput)
        self.assertEqual(script.trend_key, "ai automation")
        self.assertEqual(script.score, 10)
        
    def test_script_fields_populated(self):
        """Verify all script sections are populated strings."""
        script = self.generator.generate(self.sample_trend)
        self.assertTrue(len(script.hook) > 5)
        self.assertTrue(len(script.context) > 5)
        self.assertTrue(len(script.core_info) > 5)
        self.assertTrue(len(script.payoff) > 5)
        self.assertTrue(len(script.cta) > 5)
        
    def test_context_includes_sources(self):
        """Verify context mentions the sources."""
        script = self.generator.generate(self.sample_trend)
        # Template might use "TechCrunch, HackerNews" or "the internet" if empty
        # Given sample data, it should use sources
        self.assertIn("TechCrunch", script.context)
        
    def test_duration_logic(self):
        """Verify duration is within reasonable bounds."""
        script = self.generator.generate(self.sample_trend)
        # We target 30-60s roughly. Logic enforces >= 30.
        self.assertGreaterEqual(script.estimated_duration, 30)

    def test_serialization(self):
        """Verify JSON serialization works."""
        script = self.generator.generate(self.sample_trend)
        json_str = script.to_json()
        self.assertIn('"trend_key": "ai automation"', json_str)
        self.assertIn('"hook":', json_str)

if __name__ == '__main__':
    unittest.main()
