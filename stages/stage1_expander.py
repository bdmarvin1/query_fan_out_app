import logging
from typing import Dict, Any
from utils.gemini_client import call_gemini_api

logger = logging.getLogger("QueryFanOutSimulator")

def expand_query(query: str, cost_tracker, grounding_url: str = None) -> Dict[str, Any]:
    """
    Expands the user query using the Gemini API to discover sub-queries and latent intents.
    """
    logger.info(f"Executing Stage 1 for query: '{query}'")

    prompt = f"""
    You are an expert in search query analysis, deconstruction, and expansion, following the principles of modern generative search engines as described in the "AI Search Manual". Your task is to perform a complete "Query Fan-Out" on the user's initial query.

    Analyze the user's query: "{query}"

    Based on your analysis, provide the following expansions in a single, valid JSON object:
    1.  **Intent Classification**: Classify the user query's intent (e.g., informational, commercial), its domain/topic, and a risk profile.
    2.  **Slot Identification**: Identify both explicit and implicit variables (slots). Implicit slots are variables the system expects to fill for a useful answer.
    3.  **Latent Intent Projection**: Find related concepts, entities, and sub-topics based on proximity in vector space and knowledge graph linkages.
    4.  **Rewrites and Diversifications**: Generate numerous alternative phrasings, including more specific, long-tail variations or format-specific variations (e.g., "printable schedule").
    5.  **Speculative Sub-Questions**: Generate a list of likely follow-up questions a user might have.

    **Example based on "best half marathon training plan for beginners":**
    {{
      "classified_intent": "informational",
      "domain": "sports and fitness",
      "subdomain": "running",
      "risk_profile": "low with safety component",
      "identified_slots": {{
        "explicit": {{
          "distance": "half marathon",
          "audience": "beginners"
        }},
        "implicit": {{
          "training_timeframe": "unknown",
          "current_fitness_level": "unknown",
          "goal": "finish vs. personal record"
        }}
      }},
      "projected_latent_intents": [
        "16-week beginner training schedule",
        "run-walk method for half marathon",
        "cross-training for new runners",
        "gear checklist for long distance running",
        "hydration strategies for beginners",
        "how to avoid shin splints when training"
      ],
      "rewrites_and_diversifications": [
        "12-week half marathon plan for beginners over 40",
        "printable beginner half marathon schedule",
        "easy half marathon training plan",
        "first half marathon training guide pdf"
      ],
      "speculative_sub_questions": [
        "What shoes are best for half marathon training?",
        "How many miles should I run each week for a half marathon?",
        "What is a good pace for a beginner half marathon runner?"
      ]
    }}

    Now, generate the JSON output for the query: "{query}"
    """

    try:
        expansion_data = call_gemini_api(prompt, cost_tracker=cost_tracker, grounding_url=grounding_url)
        
        # Add original query for context in later stages
        expansion_data['original_query'] = query
        logger.info("Successfully expanded query using Gemini API.")
        return expansion_data

    except Exception as e:
        logger.error(f"An error occurred during Stage 1 expansion: {e}")
        # Return a fallback structure on failure
        return {
            "original_query": query,
            "error": str(e),
            "classified_intent": "unknown", "domain": "unknown", "subdomain": "unknown", "risk_profile": "unknown",
            "identified_slots": {}, "projected_latent_intents": [],
            "rewrites_and_diversifications": [], "speculative_sub_questions": []
        }
