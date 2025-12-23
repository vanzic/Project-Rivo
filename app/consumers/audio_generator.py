import os
import logging
import re
from app.config import load_config
from app.domain.schemas import ScriptOutput
from app.consumers.tts_provider import PiperTTS, ElevenLabsTTS

logger = logging.getLogger(__name__)

class AudioGenerator:
    """
    Generates audio from ScriptOutput using the configured TTS Backend.
    """
    
    def __init__(self):
        self.config = load_config()
        self.output_dir = os.path.join(os.getcwd(), 'outputs', 'audio')
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.backend = self.config.get('TTS_BACKEND', 'piper')
        self.provider = self._get_provider()
        
    def _get_provider(self):
        if self.backend == 'piper':
            binary = self.config.get('PIPER_BINARY_PATH', 'piper')
            model = self.config.get('PIPER_MODEL_PATH', '')
            logger.info(f"Initializing PiperTTS with binary='{binary}' and model='{model}'")
            return PiperTTS(binary, model)
        elif self.backend == 'elevenlabs':
            logger.info("Initializing ElevenLabsTTS (Placeholder)")
            return ElevenLabsTTS()
        else:
            logger.warning(f"Unknown TTS backend '{self.backend}', falling back to Piper")
            return PiperTTS('piper', '')

    def _sanitize_filename(self, key: str) -> str:
        """Creates a safe filename from the trend key."""
        clean = re.sub(r'[^a-zA-Z0-9_\-]', '', key.replace(' ', '_'))
        return clean.lower()[:50]

    def generate_audio(self, script: ScriptOutput) -> str:
        """
        Converts the script to audio and saves it. 
        Returns the absolute path to the generated file.
        """
        # Concatenate script parts
        full_text = f"{script.hook} {script.context} {script.core_info} {script.payoff} {script.cta}"
        
        filename = f"{self._sanitize_filename(script.trend_key)}_{script.score}.wav" # Piper usually outputs wav
        output_path = os.path.join(self.output_dir, filename)
        
        logger.info(f"Generatng audio for trend: {script.trend_key} using {self.backend}")
        
        # Delegate to provider
        self.provider.generate(full_text, output_path)
        
        return output_path
