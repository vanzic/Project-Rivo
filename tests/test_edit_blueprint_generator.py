import unittest
from app.consumers.edit_blueprint_generator import EditBlueprintGenerator
from app.domain.schemas import ScriptOutput

class TestEditBlueprintGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = EditBlueprintGenerator()
        self.sample_script = ScriptOutput(
            trend_key="Test Trend",
            score=10,
            # Short sections
            hook="This is the hook.",
            context="Here is some context for you.",
            # Long section to test splitting
            core_info="This is the core info. It has multiple sentences to test the splitting logic deeply. Updates are coming fast.",
            payoff="The payoff is here.",
            cta="Subscribe now!",
            estimated_duration=30
        )

    def test_blueprint_structure(self):
        """Verify the blueprint has correct basic structure."""
        blueprint = self.generator.generate_blueprint(self.sample_script)
        self.assertEqual(blueprint.trend_key, "Test Trend")
        self.assertTrue(len(blueprint.beats) > 0)
        
        # Verify sections are all present
        sections_found = set(b.section for b in blueprint.beats)
        expected_sections = {'hook', 'context', 'core_info', 'payoff', 'cta'}
        self.assertTrue(expected_sections.issubset(sections_found))

    def test_pacing_and_breaks(self):
        """Verify pattern breaks occur frequently enough."""
        blueprint = self.generator.generate_blueprint(self.sample_script)
        
        # Check that we don't have long stretches without a break
        # Logic: Iterate beats, sum duration. Reset on pattern_break=True.
        # Max duration shouldn't exceed threshold significantly (allowing for chunk granularity)
        
        time_since_break = 0.0
        max_gap = 0.0
        
        for beat in blueprint.beats:
            if beat.pattern_break:
                time_since_break = 0.0
            
            time_since_break += beat.estimated_duration
            if time_since_break > max_gap:
                max_gap = time_since_break
                
        # We expect the max gap to be roughly around the threshold + length of one sentence max
        # If the code works, it should trigger a break *before* adding a new chunk if previous gap was large, 
        # so time_since_break at the END of a chunk might be (Threshold + ChunkDuration) if the break happened at start.
        # Actually logic is: If gap > T, mark THIS chunk as break. So gap becomes 0 -> then + duration.
        # So max gap should effectively be the max duration of a single chunk (unless logic fails).
        
        # In our logic: 
        # if time + duration > Threshold: break=True, time=0. 
        # time += duration.
        # So 'time_since_break' tracks duration of the *current visual run*. 
        # It should never exceed Threshold + DurationOfCurrentChunk.
        # Let's just sanity check it's not huge (like 10s).
        self.assertLess(max_gap, 5.0) 

    def test_emotion_mapping(self):
        """Verify emotions are mapped correctly to sections."""
        blueprint = self.generator.generate_blueprint(self.sample_script)
        for beat in blueprint.beats:
            if beat.section == 'hook':
                self.assertEqual(beat.emotion, 'curiosity')
            elif beat.section == 'cta':
                self.assertEqual(beat.emotion, 'urgency')

    def test_tokenization(self):
        """Verify text splitting logic."""
        text = "Hello world. This is a test! Does it work?"
        chunks = self.generator._tokenize_section(text)
        self.assertEqual(len(chunks), 3)
        self.assertEqual(chunks[0], "Hello world.")
        self.assertEqual(chunks[1], "This is a test!")
        self.assertEqual(chunks[2], "Does it work?")

if __name__ == '__main__':
    unittest.main()
