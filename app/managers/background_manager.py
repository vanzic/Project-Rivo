import os
import logging
import subprocess
from typing import Dict

logger = logging.getLogger(__name__)

class BackgroundManager:
    """
    Manages local background video assets.
    Ensures assets exist and provides paths based on emotion metadata.
    """
    
    ASSET_DIR = os.path.join(os.getcwd(), 'app', 'assets', 'backgrounds')
    
    # Metadata: Emotion -> Filter/Description
    BACKGROUNDS: Dict[str, Dict[str, str]] = {
        "curiosity": {
            "desc": "Deep Purple/Blue Fractal",
            "filter": "mandelbrot=s=1080x1920:r=30:start_scale=2.5:end_scale=2.0:end_pts=300, hue=h=280:s=2",
            "motion": "low"
        },
        "tension": {
            "desc": "Dark Red Pulsing Noise",
            "filter": "color=c=black:s=1080x1920:r=30, noise=alls=50:allf=t+u, eq=contrast=1.5, colorbalance=rs=0.3:gs=-0.3:bs=-0.3",
            "motion": "high"
        },
        "clarity": {
            "desc": "Smooth Blue Gradient",
            "filter": "color=c=#001f3f:s=1080x1920:r=30, vignette=angle=PI/4",
            "motion": "low"
        },
        "payoff": {
            "desc": "Gold Shimmer",
            "filter": "testsrc=s=1080x1920:r=30, drawgrid=w=100:h=100:t=2:c=gold",
            "motion": "high"
        },
        "urgency": {
            "desc": "Fast Red Strobe/Noise",
            "filter": "color=c=red:s=1080x1920:r=30, drawbox=w=1080:h=1920:color=black@0.5:t=fill",
            "motion": "high"
        },
        # Fallback for unknown emotions
        "neutral": {
            "desc": "Basic Grey",
            "filter": "color=c=gray:s=1080x1920:r=30",
            "motion": "low"
        }
    }

    def __init__(self):
        os.makedirs(self.ASSET_DIR, exist_ok=True)

    def get_background(self, emotion: str) -> str:
        """
        Returns the absolute path to a background video loop for the given emotion.
        Generates it on the fly if missing (Offline/Local generation).
        """
        emotion = emotion.lower()
        if emotion not in self.BACKGROUNDS:
            logger.warning(f"Unknown emotion '{emotion}', falling back to 'neutral'")
            emotion = 'neutral'
            
        filename = f"{emotion}.mp4"
        path = os.path.join(self.ASSET_DIR, filename)
        
        if not os.path.exists(path):
            logger.info(f"[BackgroundManager] Asset missing for '{emotion}'. Generating...")
            self._generate_asset(emotion, path)
            
        return path

    def select_background(self, target_emotion: str, word_count: int = 0) -> str:
        """
        Intelligently selects a background.
        - Enforces readability: If word_count > 5, forces 'low' motion background (neutral/clarity).
        - Otherwise returns the requested emotion's asset.
        """
        target_emotion = target_emotion.lower()
        
        # 1. Readability Check
        if word_count > 5:
            # Check if target is high motion
            info = self.BACKGROUNDS.get(target_emotion, self.BACKGROUNDS['neutral'])
            if info.get('motion') == 'high':
                logger.info(f"[BackgroundManager] Text heavy ({word_count} words). Overriding '{target_emotion}' (High Motion) -> 'neutral'")
                return self.get_background('neutral')
                
        # 2. Standard Selection
        return self.get_background(target_emotion)

    def _generate_asset(self, emotion: str, output_path: str):
        """Generates a 10s looping background using FFmpeg lavfi."""
        data = self.BACKGROUNDS[emotion]
        
        cmd = [
            'ffmpeg', '-y',
            '-f', 'lavfi', '-i', data['filter'],
            '-t', '10', # 10 seconds loop
            '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
            output_path
        ]
        
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logger.info(f"[BackgroundManager] Generated {output_path}")
        except subprocess.CalledProcessError as e:
            logger.error(f"[BackgroundManager] Failed to generate {emotion}: {e}")
            raise RuntimeError(f"Could not generate background for {emotion}")

    def ensure_all_assets(self):
        """Pre-generates all defined backgrounds."""
        for emotion in self.BACKGROUNDS:
            self.get_background(emotion)
