import sys
import os
import logging

# Add project root to path
sys.path.append(os.getcwd())

from app.managers.asset_prefetcher import AssetPrefetcher

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("BackgroundFetcher")

MANIFEST = [
    # 1. Sample Public Domain / Test Videos (Confirmed Working)
    {
        "emotion": "calm",
        "url": "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"
        # Source: Google Sample Videos (Stable Test URL)
    },
    {
        "emotion": "curiosity", 
        "url": "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyrides.mp4"
        # Source: Google Sample Videos (Stable Test URL)
    },
    
    # 2. Placeholders for Stock Sites (Pexels, Pixabay, Coverr)
    # INSTRUCTIONS: 
    # 1. Go to https://www.pexels.com/search/videos/abstract/
    # 2. Click a video -> Free Download -> Right Click 'Original' -> Copy Link Address
    # 3. Paste below. Link should end in .mp4
    
    # {
    #     "emotion": "tension",
    #     "url": "INSERT_DIRECT_MP4_LINK_HERE" 
    # },
    # {
    #     "emotion": "payoff",
    #     "url": "INSERT_DIRECT_MP4_LINK_HERE"
    # }
]

def main():
    prefetcher = AssetPrefetcher()
    
    logger.info("Starting Background Asset Prefetcher...")
    
    if len(sys.argv) > 1:
        # CLI Mode: python3 fetch_backgrounds.py <emotion> <url>
        if len(sys.argv) != 3:
            logger.error("Usage: python3 fetch_backgrounds.py <emotion> <url>")
            sys.exit(1)
            
        emotion = sys.argv[1]
        url = sys.argv[2]
        
        try:
            prefetcher.fetch_and_process(url, emotion)
            logger.info("Success.")
        except Exception as e:
            logger.error(f"Failed: {e}")
            sys.exit(1)
            
    else:
        # Bulk Mode from Manifest
        if not MANIFEST:
            logger.info("No URLs in MANIFEST. Run with arguments: python3 fetch_backgrounds.py <emotion> <url>")
            return

        for item in MANIFEST:
            try:
                prefetcher.fetch_and_process(item['url'], item['emotion'])
            except Exception as e:
                logger.error(f"Skipping {item['emotion']}: {e}")

if __name__ == "__main__":
    main()
