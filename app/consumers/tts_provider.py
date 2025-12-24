from abc import ABC, abstractmethod
import logging
import os
import subprocess
import json

logger = logging.getLogger(__name__)

class TTSProvider(ABC):
    """
    Abstract Base Class for Text-to-Speech Providers.
    """
    @abstractmethod
    def generate(self, text: str, output_path: str):
        """
        Generates audio from text and saves it to output_path.
        """
        pass

class PiperTTS(TTSProvider):
    """
    Offline TTS using Piper.
    Requires 'piper' binary or executable in path.
    """
    def __init__(self, binary_path: str, model_path: str):
        self.binary_path = binary_path
        self.model_path = model_path
        
        if not os.path.exists(self.model_path):
            logger.warning(f"Piper model not found at {self.model_path}")

    def generate(self, text: str, output_path: str):
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Construct command
        # echo "text" | piper --model model.onnx --output_file output.wav
        
        cmd = [
            self.binary_path,
            "--model", self.model_path,
            "--output_file", output_path
        ]
        
        logger.info(f"Running Piper: {' '.join(cmd)} (input text hidden)")
        
        try:
            # Piper takes input from stdin
            process = subprocess.run(
                cmd,
                input=text,
                text=True, # implies encoding='utf-8' for input/output
                capture_output=True,
                check=True
            )
            logger.info(f"Piper TTS successful: {output_path}")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Piper TTS failed: {e.stderr}")
            raise RuntimeError(f"Piper TTS failed: {e.stderr}")
        except FileNotFoundError:
            logger.error(f"Piper binary not found at {self.binary_path}")
            raise RuntimeError(f"Piper binary not found at {self.binary_path}. See TTS_SETUP.md")

class SystemTTS(TTSProvider):
    """
    Offline TTS using macOS native 'say' command.
    """
    def generate(self, text: str, output_path: str):
        # Determine voice (optional, Samantha is decent default)
        # MacOS say outputs .aiff by default if extension not provided, but we can force it.
        # But ffmpeg prefers standard formats.
        
        # We'll output to the requested path. 'say' infers format from extension if supported, 
        # or we can output aiff and ffmpeg will handle it.
        # However, for consistency, let's just let 'say' handle it.
        
        cmd = ["say", "-o", output_path, "--data-format=LEF32@44100", text] # Linear PCM float 32
        
        # If output path ends in .wav or .mp3, 'say' might complain or do it.
        # 'say' on modern macs supports --file-format=m4af, etc.
        # Safe bet: output to AIFF then convert? Or just trust ffmpeg.
        # Let's try simple command first.
        
        cmd = ["say", "-o", output_path, text]
        
        logger.info(f"Running System TTS: {' '.join(cmd)}")
        try:
            subprocess.run(cmd, check=True)
            logger.info(f"System TTS successful: {output_path}")
        except subprocess.CalledProcessError as e:
            logger.error(f"System TTS failed: {e}")
            raise RuntimeError(f"System TTS failed: {e}")

class ElevenLabsTTS(TTSProvider):
    """
    Placeholder for online TTS.
    """
    def generate(self, text: str, output_path: str):
        raise NotImplementedError("ElevenLabs TTS is currently disabled/placeholder. Use Piper.")
