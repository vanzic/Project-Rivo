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

class ElevenLabsTTS(TTSProvider):
    """
    Placeholder for online TTS.
    """
    def generate(self, text: str, output_path: str):
        raise NotImplementedError("ElevenLabs TTS is currently disabled/placeholder. Use Piper.")
