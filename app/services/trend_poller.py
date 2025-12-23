import threading
import time
import logging
from app.storage.sqlite_store import TrendStore
from app.sources.base import TrendSource

from app.domain.trend import normalize_text, parse_trend_string

class TrendPoller:
    """
    Service that mimics fetching trendy content periodically with deduplication.
    """
    def __init__(self, sources: list[TrendSource], interval=30):
        self.interval = interval
        self.sources = sources
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._poll_loop, daemon=True)
        
        # Initialize persistence
        self.store = TrendStore()
        # Load persisted state to enable deduplication across restarts
        self.seen_trends = self.store.load_all()

    def start(self):
        """Starts the background polling thread."""
        logging.info("TrendPoller service getting ready to start...")
        self.thread.start()
        logging.info("TrendPoller service started.")

    def stop(self):
        """Stops the background polling thread and waits for it to finish."""
        logging.info("Stopping TrendPoller service...")
        self.stop_event.set()
        self.thread.join(timeout=5)
        logging.info(f"Total unique trends seen: {len(self.seen_trends)}")
        logging.info("TrendPoller service stopped cleanly.")

    def _poll_loop(self):
        """Internal loop for polling."""
        logging.info(f"TrendPoller loop running every {self.interval} seconds.")
        while not self.stop_event.is_set():
            try:
                # Metrics for this poll cycle
                total_fetched = 0
                new_trends_count = 0
                duplicate_trends_count = 0

                for source in self.sources:
                    # Fetch trends from each source
                    try:
                        trends = source.fetch_trends()
                        total_fetched += len(trends)
                        for trend in trends:
                            # Deduplication logic
                            if trend not in self.seen_trends:
                                logging.info(f"New trend found: '{trend}'")
                                self.seen_trends.add(trend)
                                self.store.add_trend(trend)
                                new_trends_count += 1
                                
                                # Normalization and Scoring
                                try:
                                    raw_title = parse_trend_string(trend)
                                    trend_key = normalize_text(raw_title)
                                    if trend_key:
                                        # Determine source name
                                        source_name = getattr(source, 'name', source.__class__.__name__)
                                        
                                        self.store.increment_score(trend_key, source=source_name, title=raw_title)
                                        # new_score = self.store.get_score(trend_key) # Optimized out to save DB read
                                        logging.info(f"Trend scored: '{trend_key}'")
                                except Exception as score_err:
                                    logging.error(f"Scoring failed for '{trend}': {score_err}")
                                
                            else:
                                logging.info(f"Duplicate trend ignored: '{trend}'")
                                duplicate_trends_count += 1
                    except Exception as e:
                        logging.error(f"Error fetching from source {source}: {e}")
                
                # Log cycle metrics
                logging.info(f"Poll metrics: fetched={total_fetched}, new={new_trends_count}, duplicates={duplicate_trends_count}")
                
                # Log top trends (ranking) with Structure
                try:
                    from app.domain.schemas import TrendOutput
                    import json
                    top_trends_data = self.store.get_top_trends_metadata(limit=5)
                    
                    if top_trends_data:
                        structured_output = []
                        for item in top_trends_data:
                            trend_out = TrendOutput(
                                trend_key=item['trend_key'],
                                score=item['score'],
                                sources=item['sources'],
                                sample_titles=item['sample_titles'],
                                first_seen=item['first_seen'],
                                last_seen=item['last_seen']
                            )
                            structured_output.append(json.loads(trend_out.to_json()))
                        
                        logging.info(f"Top Trends Output: {json.dumps(structured_output, indent=2)}")
                except Exception as rank_err:
                    logging.error(f"Ranking failed: {rank_err}")

                # Wait for interval or stop signal
                if self.stop_event.wait(self.interval):
                    break
            except Exception as e:
                logging.error(f"Error in TrendPoller loop: {e}")
