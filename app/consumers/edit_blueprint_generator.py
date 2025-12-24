import re
from typing import List
from app.domain.schemas import ScriptOutput, EditBlueprint, EditBeat
from app.domain.presets import ALL_PRESETS, get_preset, VisualPreset
import hashlib

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

    def _generate_caption(self, text: str, word_limit: int = 3) -> str:
        """
        Creates a punchy, retention-optimized caption.
        KINETIC RULES: Max 1-3 words (dynamic based on preset).
        """
        stop_words = {'the', 'is', 'at', 'which', 'on', 'and', 'a', 'an', 'of', 'to', 'in', 'for', 'with', 'by', 'that', 'this', 'it', 'you', 'are', 'so', 'can', 'be', 'will', 'my', 'your', 'has', 'have', 'just', 'but', 'not'}
        
        # Clean
        clean = re.sub(r'[^\w\s]', '', text)
        words = clean.split()
        
        # Filter
        keywords = [w.upper() for w in words if w.lower() not in stop_words]
        
        # Fallback if everything was removed
        if not keywords: 
            keywords = [w.upper() for w in words]
            
        # KINETIC UPDATE: Strict truncation based on preset
        if len(keywords) > word_limit:
            # Heuristic: First N usually contain the subject/action
            keywords = keywords[:word_limit]
            
        return " ".join(keywords)

    def _tokenize_section(self, text: str, word_limit: int = 7) -> List[str]:
        """Splits text into smaller chunks (visual beats)."""
        # Split by punctuation first
        parts = re.split(r'([.?!,;]+)', text)
        chunks = []
        for i in range(0, len(parts)-1, 2):
            chunk = parts[i].strip() + parts[i+1]
            if chunk: chunks.append(chunk)
        if len(parts) % 2 != 0 and parts[-1].strip():
             chunks.append(parts[-1].strip())
             
        # Sub-split long chunks (retention rule: changes frequently)
        # Ideally we want < 3 seconds per chunk. Avg speed 2.5 wps -> < 7 words.
        # But preset might demand tighter cuts (e.g. 2 words).
        final_chunks = []
        for chunk in chunks:
            words = chunk.split()
            # Dynamic limit from preset * 2 (roughly, since caption is subset)
            # Actually, let's keep it simple: split if > 2x word_limit
            split_threshold = max(4, word_limit * 2) 
            
            if len(words) > split_threshold:
                # Split in half
                mid = len(words) // 2
                final_chunks.append(" ".join(words[:mid]))
                final_chunks.append(" ".join(words[mid:]))
            else:
                final_chunks.append(chunk)
                
        return final_chunks

    def generate_blueprint(self, script: ScriptOutput) -> EditBlueprint:
        # Select Visual Preset based on Score (Viral Potential)
        # Requirement: "Preset chosen per trend type or score."
        if script.score > 85:
            preset_name = "aggressive"
        elif script.score < 50:
            preset_name = "calm"
        else:
            preset_name = "balanced"
            
        preset = get_preset(preset_name)
        
        # LOGGING
        print(f"  [Visual Style] Selected '{preset.name}' for trend '{script.trend_key}' (Score: {script.score}, Word Limit: {preset.word_limit})")
        
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
        layout_cycle = ['center', 'bottom', 'top', 'minimal']
        current_layout_idx = 0
        
        for section_name, text in sections:
            # Tokenize with preset limits (controls cut density)
            chunks = self._tokenize_section(text, word_limit=preset.word_limit)
            section_emotion = self.emotion_map.get(section_name, 'neutral')
            
            for chunk in chunks:
                duration = self._estimate_duration(chunk)
                
                # Logic: Check if we need to force a break
                is_new_section = (chunks.index(chunk) == 0)
                pattern_break = False
                
                if is_new_section or time_since_break + duration > self.PATTERN_BREAK_THRESHOLD:
                    pattern_break = True
                    # Rotate visual pattern
                    pattern_idx = (pattern_idx + 1) % len(self.visual_patterns)
                    current_visual = self.visual_patterns[pattern_idx]
                    
                    # Rotate layout (ensure distinct from last)
                    current_layout_idx = (current_layout_idx + 1) % len(layout_cycle)
                    time_since_break = duration # Fixed logic: duration of this new chunk starts the timer
                else:
                    pattern_break = False
                    current_visual = 'sustain' # Meaning "continue previous" or just slight movement
                    time_since_break += duration

                # Layout logic for retention
                layout = layout_cycle[current_layout_idx]
                
                # REWATCH LOGIC: HOOK
                if section_name == 'hook': 
                    layout = 'center' 
                    # First beat of hook: Minimal words, max intrigue
                    if chunks.index(chunk) == 0:
                        layout = 'top' # Huge impact
                        # Force minimal caption for first beat (1-2 words max)
                        base_caption = self._generate_caption(chunk, word_limit=preset.word_limit)
                        caption_text = " ".join(base_caption.split()[:2]) # Super short
                
                if section_name == 'core_info' and pattern_break: layout = 'bottom' 
                
                # REWATCH LOGIC: ENDING (Visual Echo)
                # If this is the very last beat of the CTA, echo the Hook's emotion/color
                is_last_beat = (section_name == 'cta' and chunk == chunks[-1])
                
                if is_last_beat:
                    # Echo the start
                    section_emotion = 'curiosity' # Force loop back to curiosity/hook color (Purple)
                    layout = 'center'
                    caption_text = "LOOP?" # Or keep original text? 
                    # User: "Ending must reframe the hook... complete an implied loop"
                    # Using the visual identity (color) is the safest "Visual Echo".
                    # Let's simple keep the text but force the visual style.
                    # Actually, let's keep the generated caption but ensure the emotion is loop-ready.
                    pass 

                if layout == 'minimal': 
                    caption_text = "" 
                elif section_name != 'hook' or chunks.index(chunk) > 0:
                    # Standard generation for non-first-hook beats
                    caption_text = self._generate_caption(chunk, word_limit=preset.word_limit)

                beat = EditBeat(
                    section=section_name,
                    text=chunk,
                    caption=caption_text,
                    estimated_duration=round(duration, 2),
                    emotion=section_emotion,
                    visual_intent=current_visual,
                    pattern_break=pattern_break,
                    caption_layout=layout
                )
                beats.append(beat)
        
        return EditBlueprint(trend_key=script.trend_key, beats=beats, visual_style=preset.name)
