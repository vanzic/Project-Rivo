import os
import json
import logging
import sys
from datetime import datetime
from typing import List, Dict

# Adjust path to allow imports from app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.domain.schemas import TrendOutput, ScriptOutput
from app.consumers.script_generator import ScriptGenerator
from app.consumers.audio_generator import AudioGenerator
from app.consumers.edit_blueprint_generator import EditBlueprintGenerator
from app.consumers.video_assembler import VideoAssembler

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("RetentionHarness")

# 1. GOLDEN DATASET (Mock Trends)
GOLDEN_TRENDS = [
    {"key": "The AI Singles Apocalypse", "score": 95, "src": ["HackerNews", "Twitter"]},
    {"key": "Why Javascript Won", "score": 88, "src": ["Reddit"]},
    {"key": "Dopamine Fasting 2.0", "score": 82, "src": ["YouTube"]},
    {"key": "Fusion Energy Breakthrough", "score": 90, "src": ["Nature"]},
    {"key": "The Death of SaaS", "score": 75, "src": ["IndieHackers"]},
    {"key": "Rust vs C++ in 2025", "score": 85, "src": ["Lobsters"]},
    {"key": "Quantum Computing for Dummies", "score": 70, "src": ["Medium"]},
    {"key": "Neuralink Human Trials Results", "score": 98, "src": ["BBC"]},
    {"key": "The End of Moore's Law", "score": 65, "src": ["ArsTechnica"]},
    {"key": "Python 4.0 Rumors", "score": 60, "src": ["Dev.to"]},
]

CACHE_DIR = "outputs/.cache"
EVAL_DIR = "outputs/videos"

###############################################################################
# HELPERS
###############################################################################

def get_safe_key(key: str) -> str:
    return "".join([c if c.isalnum() else "_" for c in key]).lower()

def ensure_cache_script(trend: TrendOutput, safe_key: str, script_gen: ScriptGenerator) -> ScriptOutput:
    """Gets script from cache or generates it."""
    path = os.path.join(CACHE_DIR, f"{safe_key}_script.json")
    
    if os.path.exists(path):
        logger.info(f"  [CACHE HIT] Script: {safe_key}")
        with open(path, 'r') as f:
            data = json.load(f)
            # Reconstruct Dataclass (simple kwarg unpacking)
            return ScriptOutput(**data)
            
    logger.info(f"  [CACHE MISS] Generating Script: {safe_key}")
    script = script_gen.generate(trend)
    with open(path, 'w') as f:
        f.write(script.to_json())
    return script

def ensure_cache_audio(script: ScriptOutput, safe_key: str, audio_gen: AudioGenerator) -> str:
    """Gets audio path from cache or generates it."""
    # Note: AudioGenerator saves to its own configured output dir usually.
    # We will copy or symlink, or just let AudioGenerator do its thing and we assume consistency.
    # Actually, the AudioGenerator output filename is deterministic based on key+score.
    # BUT, we want to allow re-running this harness without re-calling TTS if possible.
    
    # Let's check if the expected file exists in our CACHE dir.
    # AudioGenerator returns a path. We should copy it to cache to be safe.
    
    cached_audio_path = os.path.join(CACHE_DIR, f"{safe_key}.aiff") # Assuming system TTS aiff
    # Check if exists (and non zero size)
    if os.path.exists(cached_audio_path) and os.path.getsize(cached_audio_path) > 0:
        logger.info(f"  [CACHE HIT] Audio: {safe_key}")
        return cached_audio_path

    logger.info(f"  [CACHE MISS] Generating Audio: {safe_key}")
    # We need to temporarily hijack output dir or just move file
    # Let's just generate standard way and copy.
    generated_path = audio_gen.generate_audio(script)
    
    # Normalize extension for cache (system TTS produces .aiff or .wav depending on config)
    # We rename to .aiff in cache for consistency logic here
    import shutil
    shutil.copy2(generated_path, cached_audio_path)
    
    return cached_audio_path

###############################################################################
# MAIN RUNNER
###############################################################################

def run_harness():
    logger.info("Starting Retention Testing Harness...")
    os.makedirs(CACHE_DIR, exist_ok=True)
    os.makedirs(EVAL_DIR, exist_ok=True)

    # Init Components
    script_gen = ScriptGenerator()
    audio_gen = AudioGenerator()
    blueprint_gen = EditBlueprintGenerator() # We want FRESH instances each run
    video_assembler = VideoAssembler()       # We want FRESH logic

    metadata_registry = []

    for i, item in enumerate(GOLDEN_TRENDS):
        key = item['key']
        safe_key = get_safe_key(key)
        logger.info(f"[{i+1}/{len(GOLDEN_TRENDS)}] Processing: {key}")

        # 1. Trend Object
        trend = TrendOutput(
            trend_key=key,
            score=item['score'],
            sources=item['src'],
            sample_titles=[key],
            first_seen="2025-01-01",
            last_seen="2025-01-02"
        )

        # 2. Get/Gen Script (Cached)
        script = ensure_cache_script(trend, safe_key, script_gen)

        # 3. Get/Gen Audio (Cached)
        audio_path = ensure_cache_audio(script, safe_key, audio_gen)

        # 4. ALWAYS GEN FRESH BLUEPRINT (The variable under test)
        logger.info("  -> Generating Dynamic Blueprint...")
        blueprint = blueprint_gen.generate_blueprint(script)
        
        # Save Blueprint to Eval Dir
        bp_path = os.path.join(EVAL_DIR, f"{safe_key}_blueprint.json")
        with open(bp_path, 'w') as f:
            f.write(blueprint.to_json())

        # 5. ALWAYS GEN FRESH VIDEO (The variable under test)
        logger.info("  -> Assembling Video...")
        # Since output_dir of assembler is already outputs/videos, we don't need to move.
        # But wait, run_harness wants to rename or ensure it is there.
        # VideoAssembler.assemble returns the final path in `outputs/videos`.
        
        generated_video_path = video_assembler.assemble(audio_path, blueprint=blueprint)
        logger.info(f"  -> Video generated at: {generated_video_path}")

        # Metadata
        metadata_registry.append({
            "key": key,
            "script": script.to_json(),
            "blueprint": blueprint.to_json(),
            "audio_path": audio_path,
            "video_path": generated_video_path
        })

    # Save Registry
    meta_path = os.path.join(EVAL_DIR, "harness_metadata.json")
    with open(meta_path, 'w') as f:
        json.dump(metadata_registry, f, indent=2)
        
    logger.info(f"Retention Test Complete. Results in {EVAL_DIR}")

if __name__ == "__main__":
    run_harness()
