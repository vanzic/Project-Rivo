import urllib.request
import xml.etree.ElementTree as ET
import hashlib
import logging
from app.sources.base import TrendSource

class RSSSource(TrendSource):
    """
    Source that fetches trends from an RSS feed.
    """
    def __init__(self, url: str, name: str = "RSS"):
        self.url = url
        self.name = name

    def fetch_trends(self) -> list[str]:
        """
        Fetches items from the RSS feed, extracting title, link, and pubDate.
        Generates a unique ID by hashing the link.
        """
        trends = []
        try:
            # Set a timeout to prevent hanging
            with urllib.request.urlopen(self.url, timeout=10) as response:
                if response.status != 200:
                    logging.error(f"Failed to fetch RSS from {self.url}: Status {response.status}")
                    return []
                
                content = response.read()
                root = ET.fromstring(content)
                
                # Standard RSS 2.0 structure: channel -> item
                for item in root.findall('./channel/item'):
                    try:
                        title = item.find('title').text
                        link = item.find('link').text
                        # pubDate is optional in some feeds, handle gracefully
                        pub_date_elem = item.find('pubDate')
                        pub_date = pub_date_elem.text if pub_date_elem is not None else "Unknown Date"
                        
                        if title and link:
                            # Generate deterministic ID
                            trend_id = hashlib.md5(link.encode('utf-8')).hexdigest()[:8]
                            
                            # Format: "Title [ID] | Source" (Keeping it simple but unique)
                            trend_string = f"{title} [{trend_id}] | {self.name}"
                            trends.append(trend_string)
                    except Exception as item_error:
                        logging.warning(f"Skipping malformed RSS item in {self.name}: {item_error}")
                        continue
                        
        except Exception as e:
            logging.error(f"Error fetching RSS from {self.name} ({self.url}): {e}")
            
        return trends
