import json
from typing import List, Dict, Any
from dataclasses import dataclass, field, asdict

@dataclass
class TrendOutput:
    trend_key: str
    score: int
    sources: List[str]
    sample_titles: List[str]
    first_seen: str
    last_seen: str
    
    def to_json(self) -> str:
        return json.dumps(self.__dict__, default=str)

@dataclass
class ScriptOutput:
    trend_key: str
    score: int
    hook: str
    context: str
    core_info: str
    payoff: str
    cta: str
    estimated_duration: int
    
    def to_json(self) -> str:
        return json.dumps(self.__dict__, default=str)

@dataclass
class EditBeat:
    section: str # hook, context, etc.
    text: str
    estimated_duration: float
    emotion: str  # curiosity, tension, clarity, payoff, urgency
    visual_intent: str # cut, zoom, text_overlay, broll
    pattern_break: bool

@dataclass
class EditBlueprint:
    trend_key: str
    beats: List[EditBeat]

    def to_json(self) -> str:
        # Custom helper to handle nested dataclasses
        return json.dumps(asdict(self), default=str)
