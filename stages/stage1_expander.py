import logging
from typing import Any, Dict

from utils.gemini_client import call_gemini_api

logger = logging.getLogger("QueryFanOutSimulator")


def expand_query(
    query: str, cost_tracker, grounding_url: str = None
) -> Dict[str, Any]:
    """
    Expands the user query using the Gemini API to discover sub-queries and latent intents.

    Args:
        query: The initial query from the user.
        cost_tracker: An instance of the CostTracker class.
        grounding_url: The URL to be used for grounding the model's analysis.

    Returns:
        A dictionary containing the expanded query information, including intents,
        slots, and generated sub-queries.
    """
    logger.info(f"Executing Stage 1 for query: '{query}'")

    prompt = (
        f'You are an expert in search query analysis, deconstruction, and expansion, following the '
        f'principles of modern generative search engines as described in the "AI Search Manual". '
        f'Your task is to perform a complete "Query Fan-Out" on the user\'s initial query.\n\n'
        f"**CRUCIAL INSTRUCTION FOR GROUNDING:** Utilize the comprehensive context provided "
        f"by the URL: {grounding_url} for all aspects of your analysis and response, "
        f'especially for understanding the principles of "Query Fan-Out".\n\n'
        f'Analyze the user\'s query: "{query}"\n\n'
        f"Based on your analysis, provide the following expansions in a single, valid JSON object:\n"
        f"1. **Intent Classification**: Classify the user query's intent (e.g., informational, commercial), "
        f"its domain/topic, and a risk profile.\n"
        f"2. **Slot Identification**: Identify both explicit and implicit variables (slots). Implicit "
        f"slots are variables the system expects to fill for a useful answer.\n"
        f"3. **Latent Intent Projection**: Find related concepts, entities, and sub-topics based on "
        f"proximity in vector space and knowledge graph linkages.\n"
        f"4. **Rewrites and Diversifications**: Generate numerous alternative phrasings, including "
        f'more specific, long-tail variations or format-specific variations (e.g., "printable schedule").\n'
        f'5. **Speculative Sub-Questions**: Generate a list of likely follow-up questions a user might have.\n\n'
        f'**Example based on "best half marathon training plan for beginners":**\n'
        f'{{\n'
        f'  "classified_intent": "informational",\n'
        f'  "domain": "sports and fitness",\n'
        f'  "subdomain": "running",\n'
        f'  "risk_profile": "low with safety component",\n'
        f'  "identified_slots": {{\n'
        f'    "explicit": {{\n'
        f'      "distance": "half marathon",\n'
        f'      "audience": "beginners"\n'
        f'    }},\n'
        f'    "implicit": {{\n'
        f'      "training_timeframe": "unknown",\n'
        f'      "current_fitness_level": "unknown",\n'
        f'      "goal": "finish vs. personal record"\n'
        f'    }}\n'
        f'  }},\n'
        f'  "projected_latent_intents": [\n'
        f'    "16-week beginner training schedule",\n'
        f'    "run-walk method for half marathon",\n'
        f'    "cross-training for new runners"\n'
        f'  ],\n'
        f'  "rewrites_and_diversifications": [\n'
        f'    "12-week half marathon plan for beginners over 40",\n'
        f'    "printable beginner half marathon schedule"\n'
        f'  ],\n'
        f'  "speculative_sub_questions": [\n'
        f'    "What shoes are best for half marathon training?",\n'
        f'    "What is a good pace for a beginner half marathon runner?"\n'
        f'  ]\n'
        f'}}\n\n'
        f'Now, generate the JSON output for the query: "{query}"'
    )

    try:
        expansion_data = call_gemini_api(
            prompt,
            cost_tracker=cost_tracker,
            grounding_url=grounding_url,
            response_mime_type='application/json'
        )
        expansion_data['original_query'] = query
        logger.info("Successfully expanded query using Gemini API.")
        return expansion_data
    except Exception as e:
        logger.error(f"An error occurred during Stage 1 expansion: {e}")
        return {
            "original_query": query,
            "error": str(e),
            "classified_intent": "unknown",
            "domain": "unknown",
            "subdomain": "unknown",
            "risk_profile": "unknown",
            "identified_slots": {},
            "projected_latent_intents": [],
            "rewrites_and_diversifications": [],
            "speculative_sub_questions": [],
        }
