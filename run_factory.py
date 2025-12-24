import argparse
import logging
import json
import os
import sys
from datetime import datetime

# Adjust path to allow imports from app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.storage.sqlite_store import TrendStore
from app.domain.schemas import TrendOutput
from app.consumers.script_generator import ScriptGenerator
from app.consumers.edit_blueprint_generator import EditBlueprintGenerator
from app.consumers.audio_generator import AudioGenerator
from app.consumers.video_assembler import VideoAssembler

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("FactoryRunner")

def run(limit: int):
    logger.info(f"Starting Content Factory (Limit: {limit})...")
    
    # Initialize Components
    store = TrendStore()
    script_gen = ScriptGenerator()
    blueprint_gen = EditBlueprintGenerator()
    audio_gen = AudioGenerator()
    video_assembler = VideoAssembler()
    
    # 1. Fetch Trends
    logger.info("Fetching top trends...")
    trends_data = store.get_top_trends_metadata(limit=limit)
    
    if not trends_data:
        logger.warning("No trends found in the last 48 hours. Run the poller first!")
        return

    logger.info(f"Found {len(trends_data)} trends.")

    # Create output dirs if not exist (though consumers usually handle this)
    os.makedirs("outputs/blueprints", exist_ok=True)

    for i, data in enumerate(trends_data):
        trend_key = data['trend_key']
        logger.info(f"[{i+1}/{len(trends_data)}] Processing Trend: {trend_key}")
        
        try:
            # Convert dict to TrendOutput
            trend = TrendOutput(
                trend_key=trend_key,
                score=data['score'],
                sources=data['sources'],
                sample_titles=data['sample_titles'],
                first_seen=data['first_seen'],
                last_seen=data.get('last_seen', str(datetime.now()))
            )
            
            # 2. Generate Script
            logger.info("  -> Generating Script...")
            script = script_gen.generate(trend)
            logger.debug(f"Script generated: {len(script.core_info)} chars")
            
            # 3. Generate Blueprint
            logger.info("  -> Generating Edit Blueprint...")
            blueprint = blueprint_gen.generate_blueprint(script)
            
            # Save Blueprint
            safe_key = "".join([c if c.isalnum() else "_" for c in trend_key])
            bp_path = f"outputs/blueprints/{safe_key}.json"
            with open(bp_path, 'w') as f:
                f.write(blueprint.to_json())
            logger.info(f"     Saved blueprint to {bp_path}")

            # 4. Generate Audio
            logger.info("  -> Generating Audio...")
            audio_path = audio_gen.generate_audio(script)
            logger.info(f"     Saved audio to {audio_path}")
            
            # 5. Assemble Video
            logger.info("  -> Assembling Video...")
            video_path = video_assembler.assemble(audio_path, blueprint=blueprint)
            logger.info(f"     SUCCESS! Video saved to {video_path}")
            
        except Exception as e:
            logger.error(f"Failed to process trend '{trend_key}': {e}", exc_info=True)
            continue

    logger.info("Factory run complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the RIVO Content Factory")
    parser.add_argument("--limit", type=int, default=3, help="Number of trends to process")
    args = parser.parse_args()
    
    run(args.limit)
