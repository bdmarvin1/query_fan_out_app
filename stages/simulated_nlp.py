"""
Simulated NLP Models for Stage 1.

This module contains functions that simulate the behavior of complex NLP models
(like LLMs, classifiers, and embedding models) for the query expansion stage.
The logic is based on the "best half marathon training plan for beginners" example.
"""
from typing import Dict, Any, List

def classify_intent(query: str) -> Dict[str, str]:
    """Simulates classifying the query's intent, domain, and risk profile."""
    # This is a rule-based simulation. A real system would use a trained classifier.
    query_lower = query.lower()
    if "half marathon" in query_lower and "training" in query_lower:
        return {
            "domain": "sports and fitness",
            "subdomain": "running",
            "task_type": "plan/guide",
            "embedded_elements": ["comparative ('best')"],
            "risk_profile": "low with safety component (injury prevention)",
        }
    if "savings account" in query_lower:
        return {
            "domain": "finance",
            "subdomain": "personal banking",
            "task_type": "comparison/research",
            "embedded_elements": ["comparative ('best')", "temporal ('2025')"],
            "risk_profile": "high (YMYL)",
        }
    return {
        "domain": "general",
        "subdomain": "unknown",
        "task_type": "informational",
        "risk_profile": "low",
    }

def identify_slots(query: str) -> Dict[str, Any]:
    """Simulates identifying explicit and implicit slots in the query."""
    query_lower = query.lower()
    slots = {"explicit": {}, "implicit": {}}
    
    # Example for the primary use case
    if "half marathon" in query_lower:
        slots["explicit"]["distance"] = "half marathon"
        if "beginners" in query_lower:
            slots["explicit"]["audience"] = "beginners"
        elif "intermediate" in query_lower:
            slots["explicit"]["audience"] = "intermediate"
        
        slots["implicit"]["training_timeframe"] = "unknown"
        slots["implicit"]["runner_fitness_level"] = "unknown"
        slots["implicit"]["runner_age_group"] = "unknown"
        slots["implicit"]["goal"] = "finish vs. personal record"

    return slots

def project_latent_intents(query: str, slots: Dict[str, Any]) -> List[str]:
    """Simulates projecting latent intents using embeddings and knowledge graphs."""
    query_lower = query.lower()
    latent_intents = []

    # Example for the primary use case
    if "half marathon" in query_lower and slots.get("explicit", {}).get("audience") == "beginners":
        latent_intents.extend([
            "16-week beginner training schedule",
            "run-walk method for half marathon",
            "cross-training for new runners",
            "gear checklist for long distance running",
            "hydration strategies for beginners",
            "how to avoid shin splints when training",
            "what to eat before a long run"
        ])
    return latent_intents

def generate_rewrites_and_diversifications(query: str, slots: Dict[str, Any]) -> List[str]:
    """Simulates generating alternative phrasings and more specific variations."""
    query_lower = query.lower()
    rewrites = []

    if "half marathon" in query_lower and "beginners" in query_lower:
        rewrites.extend([
            "12-week half marathon plan for beginners over 40",
            "printable beginner half marathon schedule",
            "easy half marathon training plan",
            "first half marathon training guide pdf"
        ])
    else:
        # Generic rewrite
        rewrites.append(f"how to {query.replace('best', '').strip()}")

    return rewrites

def generate_speculative_questions(query: str) -> List[str]:
    """Simulates generating likely follow-up questions."""
    query_lower = query.lower()
    questions = []

    if "half marathon" in query_lower and "training" in query_lower:
        questions.extend([
            "What shoes are best for half marathon training?",
            "How many miles should I run each week for a half marathon?",
            "What is a good pace for a beginner half marathon runner?",
            "How to prevent injuries during half marathon training?"
        ])
    return questions
