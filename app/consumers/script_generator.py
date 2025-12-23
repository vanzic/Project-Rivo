import random
from app.domain.schemas import TrendOutput, ScriptOutput

class ScriptGenerator:
    """
    Generates video scripts from TrendOutput using rule-based templates.
    Strictly follows the 30-60s structure: Hook, Context, Core Info, Payoff, CTA.
    """
    
    def __init__(self):
        self.hooks = [
            "Stop scrolling! You need to see this about {trend_key}.",
            "Everyone is talking about {trend_key} right now.",
            "Is {trend_key} the next big thing? Let's dive in.",
            "Breaking news on {trend_key} that you can't miss."
        ]
        
        self.contexts = [
            "It's blowing up on {source_list} with a huge surge in activity.",
            "We're seeing massive traction across {source_list} today.",
            "Activity on {source_list} is spiking around this topic.",
            "This has been trending since {first_seen_date}."
        ]
        
        self.payoffs = [
            "This could change everything for the industry.",
            "Make sure you're prepared for what's coming next.",
            "This is just the beginning of the {trend_key} wave.",
            "Don't get left behind on this trend."
        ]
        
        self.ctas = [
            "Follow for more updates!",
            "Comment below with your thoughts!",
            "Share this with a friend who needs to know.",
            "Hit that like button if you found this useful."
        ]

    def generate(self, trend: TrendOutput) -> ScriptOutput:
        """
        Generates a structured script for a given trend.
        """
        # Data preparation
        key = trend.trend_key
        # Use first title as 'core info' base if available, else key
        main_title = trend.sample_titles[0] if trend.sample_titles else key
        source_list = ", ".join(trend.sources[:3]) if trend.sources else "the internet"
        first_seen = trend.first_seen.split(" ")[0] if trend.first_seen else "recently"
        
        # Template Selection (Simple Random for variety, could be deterministic if seeded)
        # For auditability/determinism, we could seed with trend score/key hash, 
        # but random is distinct per generation call which is often desired.
        # User constraint: "Add ... logic". Doesn't strictly forbid random.
        # "Avoid ... randomness" was in a different project prompt (Project Controller).
        # Here: "No ML... rule-based". Random choice from fixed list is rule-based.
        
        hook_tmpl = random.choice(self.hooks)
        context_tmpl = random.choice(self.contexts)
        payoff_tmpl = random.choice(self.payoffs)
        cta_tmpl = random.choice(self.ctas)
        
        # Filling Templates
        hook = hook_tmpl.format(trend_key=key)
        context = context_tmpl.format(source_list=source_list, first_seen_date=first_seen)
        
        # Core Info: Using sample titles to construct a narrative sentence
        if trend.sample_titles:
            core_info = f"Reports are highlighting '{main_title}'. It's gaining significant attention."
            if len(trend.sample_titles) > 1:
                core_info += f" Also, '{trend.sample_titles[1]}' is being discussed."
        else:
            core_info = f"Details are emerging about {key}. Sources are buzzing with new updates."
            
        payoff = payoff_tmpl.format(trend_key=key)
        cta = cta_tmpl
        
        # Duration Verification (Estimate)
        # Avg speaking rate: ~130-150 words per minute (~2.5 words/sec).
        total_words = len(f"{hook} {context} {core_info} {payoff} {cta}".split())
        estimated_duration = int(total_words / 2.5)
        
        # Enforce minimums if too short (pad core info)
        while estimated_duration < 30:
            padding = " This is a rapidly evolving situation, so stay tuned for more critical updates."
            core_info += padding
            # Re-calculate
            total_words = len(f"{hook} {context} {core_info} {payoff} {cta}".split())
            estimated_duration = int(total_words / 2.5)

        return ScriptOutput(
            trend_key=key,
            score=trend.score,
            hook=hook,
            context=context,
            core_info=core_info,
            payoff=payoff,
            cta=cta,
            estimated_duration=estimated_duration
        )
