import os
import logging
import subprocess
import math
import shutil
import random
import hashlib
from typing import List
from app.domain.schemas import EditBlueprint, EditBeat
from app.domain.presets import get_preset
from app.managers.background_manager import BackgroundManager

logger = logging.getLogger(__name__)

class VideoAssembler:
    """
    Assembles a video from an audio file using FFmpeg.
    Currently uses a static background color (lavfi).
    """
    
    
    def __init__(self):
        self.output_dir = os.path.join(os.getcwd(), 'outputs', 'videos')
        self.temp_dir = os.path.join(os.getcwd(), 'outputs', '.temp')
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Initialize Managers
        self.bg_manager = BackgroundManager()
        self.current_bg_path = None # State for persistence
        self.current_bg_offset = 0.0 # State for seamless looping
        
        if not shutil.which('ffmpeg'):
            logger.error("ffmpeg not found in PATH. Video assembly will fail.")
        if not shutil.which('ffprobe'):
            logger.error("ffprobe not found in PATH. Duration calculation will fail.")

    def _get_audio_duration(self, audio_path: str) -> float:
        """Probes exact audio duration."""
        try:
            cmd = [
                'ffprobe', 
                '-v', 'error', 
                '-show_entries', 'format=duration', 
                '-of', 'default=noprint_wrappers=1:nokey=1', 
                audio_path
            ]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            return float(result.stdout.strip())
        except Exception as e:
            logger.error(f"Failed to probe audio duration: {e}")
            return 30.0 # Fallback

    def _get_color_for_emotion(self, emotion: str) -> str:
        """Maps emotion to FFmpeg color syntax."""
        # Visual retention theory colors
        map = {
            'curiosity': '0x2A004E', # Deep Purple
            'tension': '0x3B0000',   # Dark Red
            'clarity': '0x002147',   # Oxford Blue
            'payoff': '0xFFD700',    # Gold
            'urgency': '0xFF4500',   # Orange Red
            'neutral': 'black'
        }
        return map.get(emotion, 'black')



    def _get_beat_seed(self, text: str, index: int) -> int:
        """Generates a deterministic integer seed from beat text and index."""
        hash_input = f"{text}_{index}"
        hash_val = hashlib.md5(hash_input.encode('utf-8')).hexdigest()
        return int(hash_val, 16)

    def _create_beat_clip(self, beat: EditBeat, duration: float, index: int, safe_key: str, preset_name: str = 'balanced') -> str:
        """Generates a short video segment for a single beat with retention-focused captions."""
        output_path = os.path.join(self.temp_dir, f"{safe_key}_beat_{index:03d}.mp4")
        
        # Background Logic (Persistent Intelligence)
        # Determine if we should switch background
        should_switch = (index == 0) or beat.pattern_break
        
        word_count = len(beat.text.split()) if beat.text else 0
        
        if should_switch or self.current_bg_path is None:
            # Select new background based on emotion and text density
            self.current_bg_path = self.bg_manager.select_background(beat.emotion, word_count)
            self.current_bg_offset = 0.0 # Reset offset for new background
            # logger.debug(f"Beat {index}: Switched BG to {os.path.basename(self.current_bg_path)}")
            
        bg_file = self.current_bg_path
        has_bg_video = True
        
        # Caption Logic
        text = beat.caption if beat.caption else " "
        text = text.replace("'", "").replace(":", "").replace('"', '')
        
        font_path = "/System/Library/Fonts/Helvetica.ttc"
        if not os.path.exists(font_path):
             font_path = "/System/Library/Fonts/Geneva.ttf"

        # Layout
        x_expr = "(w-text_w)/2"
        y_expr = "(h-text_h)/2" 
        fontsize = 80
        
        if beat.caption_layout == 'bottom':
            y_expr = "h-(h/3)"
            fontsize = 60
        elif beat.caption_layout == 'top':
            y_expr = "h/5"
            fontsize = 90
        elif beat.caption_layout == 'minimal':
            text = " "
            
        if text.strip():
            drawtext_filter = f"drawtext=fontfile='{font_path}':text='{text}':fontcolor=white:fontsize={fontsize}:x={x_expr}:y={y_expr}:borderw=3:bordercolor=black"
        else:
            drawtext_filter = "null"

        # Construct Filtergraph with Kinetic Animation
        
        # 1. Background Chain
        if has_bg_video:
            # boxblur=20:1, drawbox (darken)
            bg_chain = (
                f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
                f"boxblur=20:1,drawbox=x=0:y=0:w=1080:h=1920:color=black@0.4:t=fill[bg]"
            )
            input_args = ['-stream_loop', '-1', '-i', bg_file]
        else:
            # Solid color
            color = self._get_color_for_emotion(beat.emotion)
            bg_chain = f"color=c={color}:s=1080x1920:r=30[bg]"
            input_args = []

        # 2. Text Chain (Kinetic)
        # We create a separate transparent input for text to animate it
        # Animation: Zoom in slightly (Pop)
        # 'zoompan' filter: z='if(lte(on,5), 1.5-0.1*on, 1.0)' -> Zoom starts 1.5x and drops to 1.0x in first 5 frames
        # d=1: Output duration per frame? No, d=1 means 1 frame input = 1 frame output effectively.
        # But zoompan works on input streams. Easier to apply to the text layer.
        
        if text.strip():
            # Create text on transparent background
            # We need to render the text large then zoom/scale it.
            
            # Position logic needs to be handled in overlay or padding
            # Simpler: Draw text on 1080x1920 transparent, then zoompan the whole layer centered.
            
            text_chain = (
                f"color=c=0x00000000:s=1080x1920:r=30,"
                f"{drawtext_filter},"
                f"zoompan=z='min(zoom+0.15,1.5)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920[txt]"
            )
            # Wait, zoompan accumulates zoom if we aren't careful.
            # Pop effect: start large, go small? Or Start small go large?
            # "Pop" usually means 0 -> 1.0 (overshoot). 
            # Zoompan default is 1.0. 
            # Let's try: Start at z=1.5 (big) then go to 1.0 rapidamente?
            # Expression: `if(lte(time,0.1), 1.0 + (0.5 * (1-time/0.1)), 1.0)`
            # Note: zoompan uses 'time' or 'in'.
            # A simple zoom-out (Slam) often looks punchier than zoom-in.
            
            # Slam effect logic with Deterministic Micro-Variations
            seed = self._get_beat_seed(beat.text, index)
            rng = random.Random(seed)
            preset = get_preset(preset_name)
            
            # Variances from Preset
            z_min, z_max = preset.zoom_range
            decay_min, decay_max = preset.zoom_decay_range
            j_amt = preset.jitter_amount
            
            zoom_start = z_min + (rng.random() * (z_max - z_min)) 
            zoom_decay = decay_min + (rng.random() * (decay_max - decay_min))
            jitter_x = rng.randint(-j_amt, j_amt)
            jitter_y = rng.randint(-j_amt, j_amt)
            
            # Apply slam: starts at zoom_start, decays by zoom_decay per frame to 1.0 minimum
            text_chain = (
                f"color=c=0x00000000:s=1080x1920:r=30,"
                f"{drawtext_filter},"
                f"zoompan=z='if(eq(on,1), {zoom_start:.2f}, max(1.0, zoom-{zoom_decay:.3f}))':d=1:fps=30:s=1080x1920[txt]"
            )
            
            # Overlay with position jitter
            final_graph = f"{bg_chain};{text_chain};[bg][txt]overlay=x={jitter_x}:y={jitter_y}:format=auto[out]"
            
        else:
            # No text, just bg. Pass [bg] to [out] via copy or null filter.
            final_graph = f"{bg_chain};[bg]copy[out]"


        cmd = ['ffmpeg', '-y']
        cmd.extend(input_args)
        cmd.extend([
            '-f', 'lavfi', '-i', final_graph, # Wait, complex filter graph needs -filter_complex, inputs handled differently
            # If using complex filter, inputs must be mapped.
            # If using lavfi source inside complex filter, that's fine.
            # But the bg_chain uses [0:v] if input exists.
        ])
        
        # FIX: Structure command properly for filter_complex
        cmd = ['ffmpeg', '-y']
        cmd.extend(input_args) # Input 0 (if bg exists)
        
        if not has_bg_video:
             # Need a dummy input for filter graph? No, we can generate inside.
             pass
             
        cmd.extend(['-filter_complex', final_graph])
        cmd.extend([
            '-map', '0' if not has_bg_video else '0', # wait, if not has_bg_video, output is from filter?
            # Output map is implicit from last node if not named? 
            # Let's name final output [out]
        ])
        
        # final_graph now ends with [out]

        
        # If no input file (solid color), we don't map input.
        # If no input file (solid color), we don't map input.
        if has_bg_video:
             # Seamless Looping: Slice into the infinite loop at the current offset
             cmd = [
                 'ffmpeg', '-y', 
                 '-stream_loop', '-1', '-i', bg_file, 
                 '-ss', f"{self.current_bg_offset:.3f}", # Seek AFTER input (output seeking)
                 '-t', str(duration), 
                 '-filter_complex', final_graph, 
                 '-map', '[out]', 
                 '-c:v', 'libx264', '-pix_fmt', 'yuv420p', 
                 output_path
             ]
             self.current_bg_offset += duration # Advance cursor for next beat
        else:
             cmd = ['ffmpeg', '-y', '-filter_complex', final_graph, '-map', '[out]', '-t', str(duration), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', output_path]
        
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return output_path

    def assemble(self, audio_path: str, blueprint: EditBlueprint = None) -> str:
        """
        Assembles video using blueprint logic.
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Derive paths
        filename = os.path.basename(audio_path)
        basename = os.path.splitext(filename)[0]
        final_output = os.path.join(self.output_dir, f"{basename}.mp4")
        
        # If no blueprint, fallback to static (legacy)
        if not blueprint:
            return ""

        # Reset State for new video
        self.current_bg_path = None
        self.current_bg_offset = 0.0
        
        logger.info(f"Generating visuals for {len(blueprint.beats)} beats...")

        # 1. Analyze Audio
        total_duration = self._get_audio_duration(audio_path)
        
        # 2. Distribute duration across beats
        # The blueprint estimated_duration might not match actual TTS duration exactly.
        # We need to normalize.
        total_estimated = sum(b.estimated_duration for b in blueprint.beats)
        if total_estimated == 0: total_estimated = 1 # avoid div/0
        
        scale_factor = total_duration / total_estimated
        
        # 3. Generate Segments
        segment_files = []
        concat_list_path = None
        temp_video = None
        safe_key = "".join([c if c.isalnum() else "_" for c in blueprint.trend_key])
        
        logger.info(f"Generating visuals for {len(blueprint.beats)} beats...")
        
        try:
            for i, beat in enumerate(blueprint.beats):
                real_duration = beat.estimated_duration * scale_factor
                # Enforce min duration (1 frame)
                if real_duration < 0.04: real_duration = 0.04
                
                seg_path = self._create_beat_clip(beat, real_duration, i, safe_key, blueprint.visual_style)
                segment_files.append(seg_path)
            
            # 4. Concatenate Segments
            concat_list_path = os.path.join(self.temp_dir, f"{safe_key}_files.txt")
            with open(concat_list_path, 'w') as f:
                for path in segment_files:
                    f.write(f"file '{path}'\n")
            
            temp_video = os.path.join(self.temp_dir, f"{safe_key}_visuals.mp4")
            
            # Concat command
            subprocess.run([
                'ffmpeg', '-y', 
                '-f', 'concat', 
                '-safe', '0', 
                '-i', concat_list_path, 
                '-c', 'copy', 
                temp_video
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # 5. Merry Audio and Visuals
            # Output map: Visuals from temp_video, Audio from audio_path
            subprocess.run([
                'ffmpeg', '-y',
                '-i', temp_video,
                '-i', audio_path,
                '-c:v', 'copy', # Video is already encoded correctly
                '-c:a', 'aac', '-b:a', '192k',
                '-shortest', # Truncate if visual is slightly longer
                final_output
            ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            logger.info(f"Retenion-optimized video saved to {final_output}")
            
        except Exception as e:
            logger.error(f"Assembly failed: {e}")
            raise e
        finally:
            # Cleanup temps
            for p in segment_files:
                if os.path.exists(p): os.remove(p)
            if concat_list_path and os.path.exists(concat_list_path): os.remove(concat_list_path)
            if temp_video and os.path.exists(temp_video): os.remove(temp_video)

        return final_output

    def _legacy_assemble(self, audio_path, output_path):
        # Fallback for tests or no blueprint
        subprocess.run([
            'ffmpeg', '-y', '-f', 'lavfi', '-i', 'color=c=black:s=1080x1920:r=30',
            '-i', audio_path, '-c:v', 'libx264', '-tune', 'stillimage',
            '-c:a', 'aac', '-shortest', output_path
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return output_path
