from dataclasses import dataclass
from typing import Tuple

@dataclass
class VisualPreset:
    name: str
    word_limit: int          # Max words per caption (controls cut pace)
    zoom_range: Tuple[float, float] # Min/Max start zoom (e.g. 1.15, 1.30)
    jitter_amount: int       # Pixel offset for position jitter
    zoom_decay_range: Tuple[float, float] # Min/Max decay per frame

# --- PRESET DEFINITIONS ---

AGGRESSIVE = VisualPreset(
    name="aggressive",
    word_limit=2,            # Very fast cuts
    zoom_range=(1.30, 1.50), # Hard slams
    jitter_amount=20,        # High chaotic jitter
    zoom_decay_range=(0.06, 0.10) # Fast settle
)

BALANCED = VisualPreset(
    name="balanced",
    word_limit=3,            # Standard pacing
    zoom_range=(1.15, 1.30), # Noticeable but not dizzying
    jitter_amount=15,        # Organic imperfection
    zoom_decay_range=(0.04, 0.08)
)

CALM = VisualPreset(
    name="calm",
    word_limit=5,            # Slower reading, longer shots
    zoom_range=(1.05, 1.15), # Gentle floating
    jitter_amount=5,         # Subtle drift
    zoom_decay_range=(0.01, 0.03) # Slow, smooth settle
)

ALL_PRESETS = {
    "aggressive": AGGRESSIVE,
    "balanced": BALANCED,
    "calm": CALM
}

def get_preset(name: str) -> VisualPreset:
    return ALL_PRESETS.get(name, BALANCED)
