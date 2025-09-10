import json
import logging
from typing import Any, Dict, List

from utils.gemini_client import call_gemini_api

logger = logging.getLogger("QueryFanOutSimulator")

# A comprehensive list of source types and modalities for content routing.
SOURCE_TYPES = [
    "Coaching blogs", "training websites", "expert-authored pages",
    "E-commerce sites", "product review sites", "affiliate blogs",
    "Instructional platforms", "fitness apps", "YouTube channels",
    "Knowledge bases", "encyclopedias", "government or academic sources",
    "financial data APIs", "bank product pages", "personal finance editorial sites"
]

MODALITY_TYPES = [
    "Long-form text", "structured schedules", "tables", "Listicles",
    "bullet lists", "product comparison tables", "Video (with transcripts)",
    "step-by-step guides", "Concise explanatory text", "structured definitions"
]


def route_subqueries(
    stage1_output: Dict[str, Any], cost_tracker, grounding_url: str = None
) -> List[Dict[str, Any]]:
    """
    Routes each sub-query to appropriate sources and modalities using the Gemini API.

    Args:
        stage1_output: The dictionary output from the query expansion stage.
        cost_tracker: An instance of the CostTracker class.
        grounding_url: The URL to be used for grounding the model's analysis.

    Returns:
        A list of dictionaries, where each dictionary contains a sub-query
        and its predicted source types and modality.
    """
    logger.info("Executing Stage 2: Sub-query Routing.")

    # Consolidate all generated queries into a single unique list.
    sub_queries = list(set(
        stage1_output.get("rewrites_and_diversifications", [])
        + stage1_output.get("speculative_sub_questions", [])
        + stage1_output.get("projected_latent_intents", [])
    ))

    if not sub_queries:
        logger.warning("No sub-queries found from Stage 1 to route.")
        return []

    # Construct the prompt for the Gemini API call.
    prompt = (
        f"You are an expert in information retrieval and search algorithms. Your task is to "
        f"analyze a list of sub-queries and determine the most appropriate source types and "
        f"content modalities for finding the best answers, based on the principles of the "
        f"\"AI Search Manual\".\n\n"
        f"**CRUCIAL INSTRUCTION FOR GROUNDING:** Utilize the comprehensive context provided "
        f"by the URL: {grounding_url} for all aspects of your analysis and response, "
        f"especially for understanding the principles of \"Query Fan-Out\".\n\n"
        f"**Instructions:**\n"
        f"1. For each sub-query, select one or more source types from this exact list: {SOURCE_TYPES}\n"
        f"2. For each sub-query, select the single most appropriate modality from this exact list: {MODALITY_TYPES}\n"
        f"3. Return the output as a single, valid JSON object, which is a list of dictionaries. "
        f"Each dictionary must have three keys: \"sub_query\", \"predicted_source_types\", and "
        f"\"predicted_modality\".\n\n"
        f"**List of Sub-Queries to Analyze:**\n"
        f"{json.dumps(sub_queries, indent=2)}\n\n"
        f"**Example Output Format:**\n"
        f"[\n"
        f"    {{\n"
        f'        "sub_query": "16-week beginner half marathon training plan",\n'
        f'        "predicted_source_types": ["Coaching blogs", "training websites"],\n'
        f'        "predicted_modality": "structured schedules"\n'
        f"    }},\n"
        f"    {{\n"
        f'        "sub_query": "Half marathon gear checklist",\n'
        f'        "predicted_source_types": ["E-commerce sites", "product review sites"],\n'
        f'        "predicted_modality": "Listicles"\n'
        f"    }}\n"
        f"]\n"
    )

    logger.info(f"Sending {len(sub_queries)} unique sub-queries to Gemini for routing.")

    try:
        routed_queries = call_gemini_api(
            prompt,
            cost_tracker=cost_tracker,
            grounding_url=grounding_url,
            response_mime_type='application/json'
        )

        if not isinstance(routed_queries, list):
            raise ValueError("Gemini API did not return a list as expected.")

        logger.info(f"Successfully routed {len(routed_queries)} sub-queries.")
        return routed_queries
    except Exception as e:
        logger.error(f"An error occurred during Stage 2 routing: {e}")
        # Provide a fallback structure on failure to ensure downstream compatibility.
        return [
            {
                "sub_query": sq,
                "predicted_source_types": ["unknown"],
                "predicted_modality": "unknown",
                "error": str(e),
            }
            for sq in sub_queries
        ]
