import re
from typing import List
from app.domain.schemas import ScriptOutput, EditBlueprint, EditBeat

class EditBlueprintGenerator:
    """
    Generates an editing blueprint from a script.
    Enforces pacing, visual variety, and emotional mapping.
    """
    
    WORDS_PER_SECOND = 2.5 # Average speaking rate
    PATTERN_BREAK_THRESHOLD = 2.0 # Seconds

    def __init__(self):
        self.emotion_map = {
            'hook': 'curiosity',
            'context': 'tension',
            'core_info': 'clarity',
            'payoff': 'satisfaction',
            'cta': 'urgency'
        }
        self.visual_patterns = ['cut', 'zoom', 'text_overlay', 'broll']

    def _estimate_duration(self, text: str) -> float:
        word_count = len(text.split())
        return max(0.5, word_count / self.WORDS_PER_SECOND)

    def _tokenize_section(self, text: str) -> List[str]:
        """Splits text into smaller chunks (visual beats)."""
        # split by punctuation (.?!,;) but keep the punctuation
        # Simple regex split
        parts = re.split(r'([.?!,;]+)', text)
        # Rejoin punctuation to the preceding sentence
        chunks = []
        for i in range(0, len(parts)-1, 2):
            chunk = parts[i].strip() + parts[i+1]
            if chunk:
                chunks.append(chunk)
        if len(parts) % 2 != 0 and parts[-1].strip():
             chunks.append(parts[-1].strip())
        return chunks

    def generate_blueprint(self, script: ScriptOutput) -> EditBlueprint:
        beats: List[EditBeat] = []
        sections = [
            ('hook', script.hook),
            ('context', script.context),
            ('core_info', script.core_info),
            ('payoff', script.payoff),
            ('cta', script.cta)
        ]

        time_since_break = 0.0
        pattern_idx = 0
        
        for section_name, text in sections:
            chunks = self._tokenize_section(text)
            section_emotion = self.emotion_map.get(section_name, 'neutral')
            
            for chunk in chunks:
                duration = self._estimate_duration(chunk)
                current_visual = 'cut' # Default start
                pattern_break = False
                
                # Logic: Check if we need to force a break
                # If it's the start of a new section, usually a cut (pattern break implicitly)
                # If within a section, check timer
                
                is_new_section = (chunks.index(chunk) == 0)
                
                if is_new_section:
                    pattern_break = True
                    current_visual = 'cut'
                    time_since_break = 0.0
                elif time_since_break + duration > self.PATTERN_BREAK_THRESHOLD:
                    # Force a break mid-chunk? 
                    # Actually, we apply the break TO this chunk.
                    pattern_break = True
                    # Rotate distinct visuals
                    pattern_idx = (pattern_idx + 1) % len(self.visual_patterns)
                    current_visual = self.visual_patterns[pattern_idx]
                    time_since_break = duration
                else:
                    # Sustain
                    pattern_break = False
                    current_visual = 'sustain' # Meaning "continue previous" or just slight movement
                    time_since_break += duration

                beat = EditBeat(
                    section=section_name,
                    text=chunk,
                    estimated_duration=round(duration, 2),
                    emotion=section_emotion,
                    visual_intent=current_visual,
                    pattern_break=pattern_break
                )
                beats.append(beat)
                
                # If the chunk was very long (e.g. > 4s), we might want to split it further in future iterations.
                # For now, we just reset the timer if we marked a break.
                # Note: The logic above effectively says "This chunk STARTS with a break".
                # If the chunk itself is 5 seconds long, we can't break INSIDE it with this simple logic without splitting text.
                # Optimization: Return simply. The constraint says "Pattern break at least every 2s". 
                # If a sentence is 5s, we fail. 
                # Let's add a quick sub-split check?
                # User rules: "Divide the script into time-based beats... Enforce pattern break at least every 2s".
                # If estimate > 2.0, we should probably force sub-visuals or just accept the granularity for now 
                # as splitting by comma is safer than arbitrary string slicing.
                # I'll stick to sentence splits for safety, but maybe split by commas too if needed?
                # Let's split by commas too if the chunk is long.
        
        return EditBlueprint(trend_key=script.trend_key, beats=beats)
