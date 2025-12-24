import os
import logging
import subprocess
import urllib.request
import ssl

logger = logging.getLogger(__name__)

class AssetPrefetcher:
    """
    Downloads and normalizes background videos for the asset library.
    Enforces strict formats: 1080x1920 (9:16), 30fps, >5s duration.
    """
    
    ASSET_DIR = os.path.join(os.getcwd(), 'app', 'assets', 'backgrounds')
    TEMP_DIR = os.path.join(os.getcwd(), 'outputs', '.temp')

    def __init__(self):
        os.makedirs(self.ASSET_DIR, exist_ok=True)
        os.makedirs(self.TEMP_DIR, exist_ok=True)
        # Allow requests to ignore SSL cert errors if needed (for some public datasets)
        self.ssl_context = ssl._create_unverified_context()

    def fetch_and_process(self, url: str, emotion: str) -> str:
        """
        Downloads a video from URL, validates it, normalizes it, and saves it to the asset library.
        Returns the path to the final asset.
        """
        logger.info(f"[Prefetcher] Processing '{emotion}' from {url}")
        
        # 1. Download to Temp
        filename = url.split('/')[-1].split('?')[0] or f"temp_{emotion}.mp4"
        if not filename.endswith('.mp4'): filename += ".mp4"
        
        temp_path = os.path.join(self.TEMP_DIR, f"raw_{filename}")
        
        try:
            logger.info("  Downloading...")
            req = urllib.request.Request(
                url, 
                data=None, 
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
                }
            )
            with urllib.request.urlopen(req, context=self.ssl_context) as response, open(temp_path, 'wb') as out_file:
                 out_file.write(response.read())
        except Exception as e:
            logger.error(f"  Download failed: {e}")
            raise

        # 2. Probe & Validate
        if not self._validate_video(temp_path):
            os.remove(temp_path)
            raise ValueError("Video failed validation (too short or invalid format)")

        # 3. Normalize (FFmpeg)
        # Target: 1080x1920, 30fps, x264, yuv420p, no audio
        final_path = os.path.join(self.ASSET_DIR, f"{emotion}.mp4")
        
        logger.info("  Normalizing (Scale/Crop to 9:16, 30fps)...")
        # Logic: Scale to cover 1080x1920, then crop
        filter_str = (
            "scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,"
            "fps=30"
        )
        
        cmd = [
            'ffmpeg', '-y',
            '-i', temp_path,
            '-vf', filter_str,
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-an', # Remove audio
            final_path
        ]
        
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logger.info(f"  -> Saved to {final_path}")
        except subprocess.CalledProcessError as e:
            logger.error(f"  Normalization failed: {e}")
            raise
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
        return final_path

    def _validate_video(self, path: str) -> bool:
        """Checks if video is valid and longer than 5 seconds."""
        cmd = [
            'ffprobe', 
            '-v', 'error', 
            '-show_entries', 'format=duration', 
            '-of', 'default=noprint_wrappers=1:nokey=1', 
            path
        ]
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            duration = float(result.stdout.strip())
            
            if duration < 5.0:
                logger.warning(f"  Validation Warning: Video too short ({duration}s < 5.0s)")
                return False
                
            return True
        except Exception as e:
            logger.warning(f"  Validation Probe Failed: {e}")
            return False
