import os
import logging
import subprocess
import shutil

logger = logging.getLogger(__name__)

class VideoAssembler:
    """
    Assembles a video from an audio file using FFmpeg.
    Currently uses a static background color (lavfi).
    """
    
    def __init__(self):
        self.output_dir = os.path.join(os.getcwd(), 'outputs', 'video')
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Check if ffmpeg is available
        if not shutil.which('ffmpeg'):
            logger.error("ffmpeg not found in PATH. Video assembly will fail.")

    def assemble(self, audio_path: str, output_path: str = None) -> str:
        """
        Generates a 9:16 video with the given audio.
        If output_path is not provided, derives it from audio filename.
        Returns absolute path to generated video.
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        if not output_path:
            # Derived defaults: /path/to/audio/foo.mp3 -> /path/to/video/foo.mp4
            filename = os.path.basename(audio_path)
            basename = os.path.splitext(filename)[0]
            output_path = os.path.join(self.output_dir, f"{basename}.mp4")

        # FFmpeg command construction
        # Inputs:
        # 1. -f lavfi -i color=c=black:s=1080x1920:r=30 (Infinite black video 1080x1920 @ 30fps)
        # 2. -i audio_path (The audio track)
        # Audio is stream 1, Video is stream 0.
        # -c:v libx264 (H.264 video)
        # -tune stillimage (Optimize for static content)
        # -c:a aac (AAC audio - better compatibility than copy if input isn't perfect)
        # -shortest (Finish when the shortest input stream ends - i.e. audio)
        # -pix_fmt yuv420p (Good compatibility)
        
        command = [
            'ffmpeg',
            '-y', # Overwrite output
            '-f', 'lavfi',
            '-i', 'color=c=black:s=1080x1920:r=30',
            '-i', audio_path,
            '-c:v', 'libx264',
            '-tune', 'stillimage',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-pix_fmt', 'yuv420p',
            '-shortest',
            output_path
        ]
        
        logger.info(f"Starting video assembly for {audio_path}")
        logger.debug(f"FFmpeg command: {' '.join(command)}")
        
        try:
            # Run ffmpeg, capturing output for debugging if it fails
            result = subprocess.run(
                command,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            logger.info(f"Video saved to {output_path}")
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg failed with exit code {e.returncode}")
            logger.error(f"FFmpeg stderr: {e.stderr}")
            raise RuntimeError(f"FFmpeg assembly failed: {e.stderr}")
        except Exception as e:
            logger.error(f"Unexpected error in video assembly: {e}")
            raise e
