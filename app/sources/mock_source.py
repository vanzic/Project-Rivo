import random
import uuid
from app.sources.base import TrendSource

class MockTrendSource(TrendSource):
    """
    Mock source that simulates a noisy stream of trends.
    Emits a mix of:
    1. Static trends (Simulates recurring/duplicate data)
    2. Dynamic unique trends (Simulates new incoming data)
    """
    def __init__(self):
        # A pool of recurring trends to test deduplication
        # Added lifecycle tags to simulate realistic tagging
        self.static_trends = [
            "AI is taking over! | peaking",
            "Python 4.0 released? | emerging",
            "New framework drops | emerging",
            "Tabs vs Spaces debate heating up | declining",
            "Coffee prices skyrocket | peaking",
            "Rust is the future | emerging",
            "Vim vs Emacs eternal war | declining"
        ]
        self.lifecycle_states = ["emerging", "peaking", "declining"]
        self.counter = 0

    def fetch_trends(self) -> list[str]:
        """
        Returns a list of 1-3 trends.
        - 70% chance of picking from static pool (Noise/Duplicates)
        - 30% chance of generating a brand new trend (Signal)
        """
        num_items = random.randint(1, 3)
        results = []
        
        for _ in range(num_items):
            if random.random() < 0.7:
                # Return a known duplicate
                results.append(random.choice(self.static_trends))
            else:
                # Generate a new unique trend
                self.counter += 1
                unique_id = uuid.uuid4().hex[:6]
                state = random.choice(self.lifecycle_states)
                results.append(f"Viral Topic #{self.counter} [{unique_id}] | {state}")
                
        return results
