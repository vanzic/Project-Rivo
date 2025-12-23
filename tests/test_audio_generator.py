import unittest
from unittest.mock import patch, MagicMock
import os
import json
from app.consumers.audio_generator import AudioGenerator
from app.domain.schemas import ScriptOutput

class TestAudioGenerator(unittest.TestCase):
    def setUp(self):
        # Patch config to ensure we have a dummy key for tests
        self.config_patcher = patch('app.consumers.audio_generator.load_config')
        self.mock_config = self.config_patcher.start()
        self.mock_config.return_value = {
            'ELEVENLABS_API_KEY': 'test_key',
            'ELEVENLABS_VOICE_ID': 'test_voice'
        }
        
        self.generator = AudioGenerator()
        
        self.sample_script = ScriptOutput(
            trend_key="Test Trend 123!",
            score=10,
            hook="Hook.",
            context="Context.",
            core_info="Core.",
            payoff="Payoff.",
            cta="CTA.",
            estimated_duration=30
        )

    def tearDown(self):
        self.config_patcher.stop()

    def test_sanitize_filename(self):
        """Verify filename sanitization logic."""
        raw = "Trend: New AI Model & Stuff"
        clean = self.generator._sanitize_filename(raw)
        # Expected: trend_new_ai_model__stuff (spaces->_, & removed, : removed, lower)
        # Regex used: sub(r'[^a-zA-Z0-9_\-]', '', key.replace(' ', '_'))
        # "Trend: New AI Model & Stuff" -> "Trend_New_AI_Model_&_Stuff" -> remove special chars
        # "Trend_New_AI_Model__Stuff" -> lower
        self.assertEqual(clean, "trend_new_ai_model__stuff")

    @patch('urllib.request.urlopen')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    @patch('os.makedirs') # Mock this to avoid touching filesystem
    def test_generate_success(self, mock_makedirs, mock_file, mock_urlopen):
        """Verify successful API call and file write."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b"fake_audio_bytes"
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        # Call generate
        path = self.generator.generate_audio(self.sample_script)
        
        # Verify API called correctly
        args, kwargs = mock_urlopen.call_args
        req = args[0]
        self.assertEqual(req.full_url, "https://api.elevenlabs.io/v1/text-to-speech/test_voice")
        self.assertEqual(req.headers['Xi-api-key'], 'test_key')
        
        # Verify payload contains full text
        payload = json.loads(req.data.decode('utf-8'))
        self.assertEqual(payload['text'], "Hook. Context. Core. Payoff. CTA.")
        
        # Verify file write
        expected_filename = "test_trend_123_10.mp3"
        self.assertIn(expected_filename, path)
        mock_file.assert_called_with(path, 'wb')
        mock_file().write.assert_called_with(b"fake_audio_bytes")

    def test_missing_api_key(self):
        """Verify ValueError is raised if API key is missing."""
        self.mock_config.return_value = {} # Empty config
        gen = AudioGenerator() # Re-init to pick up empty config
        
        with self.assertRaises(ValueError):
            gen.generate_audio(self.sample_script)

if __name__ == '__main__':
    unittest.main()
