import unittest
from unittest.mock import patch, MagicMock
import os
import subprocess
from app.consumers.video_assembler import VideoAssembler

class TestVideoAssembler(unittest.TestCase):
    def setUp(self):
        # Patch shutil.which to pretend ffmpeg exists
        self.which_patcher = patch('shutil.which')
        self.mock_which = self.which_patcher.start()
        self.mock_which.return_value = '/usr/bin/ffmpeg'
        
        self.assembler = VideoAssembler()
        self.dummy_audio = "/tmp/fake_audio.mp3"

    def tearDown(self):
        self.which_patcher.stop()

    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_assemble_success(self, mock_run, mock_exists):
        """Verify successful subprocess call with correct args."""
        mock_exists.return_value = True # Audio file exists
        
        # Mock successful run
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        output = self.assembler.assemble(self.dummy_audio)
        
        # Check args
        args, kwargs = mock_run.call_args
        command = args[0]
        
        self.assertEqual(command[0], 'ffmpeg')
        self.assertIn('-f', command)
        self.assertIn('lavfi', command)
        self.assertIn('color=c=black:s=1080x1920:r=30', command)
        self.assertIn(self.dummy_audio, command)
        self.assertIn('-shortest', command)
        
        # Verify output path derivation
        expected_output = os.path.join(self.assembler.output_dir, "fake_audio.mp4")
        self.assertEqual(output, expected_output)

    @patch('os.path.exists')
    def test_audio_not_found(self, mock_exists):
        """Verify FileNotFoundError if audio missing."""
        mock_exists.return_value = False
        with self.assertRaises(FileNotFoundError):
            self.assembler.assemble(self.dummy_audio)

    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_ffmpeg_failure(self, mock_run, mock_exists):
        """Verify RuntimeError on ffmpeg failure."""
        mock_exists.return_value = True
        
        # Mock failure
        mock_run.side_effect = subprocess.CalledProcessError(1, cmd='ffmpeg', stderr="Some Error")
        
        with self.assertRaises(RuntimeError):
            self.assembler.assemble(self.dummy_audio)

if __name__ == '__main__':
    unittest.main()
